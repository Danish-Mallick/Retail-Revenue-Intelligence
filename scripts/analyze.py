"""Reproduce the analysis of the USER-SUPPLIED, FILTERED Online Retail.csv extract.

Important: source has 13 columns and is NOT a byte-identical copy of the
unfiltered original UCI Online Retail Excel file. Source uses mixed date
representations: ambiguous days/months are reversed. Original duplicates
are retained for headline sales; sensitivity analysis quantifies removal.

Usage:
    python scripts/analyze.py --source 'data/raw/Online Retail.csv'
No network access required.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'InvoiceNo','StockCode','Description','Quantity','UnitPrice','CustomerID','Country','InvoiceDate'}

def load_extract(source):
    source = Path(source)
    raw = pd.read_csv(source, dtype={'StockCode':'string','Description':'string','Country':'string','InvoiceDate':'string'},low_memory=False)
    missing = EXPECTED-set(raw.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    if raw.InvoiceNo.isna().any() or raw.CustomerID.isna().any():
        raise ValueError('This project is designed for the attached filtered extract with identifiable invoice/customer rows.')
    if (raw.Quantity<=0).any() or (raw.UnitPrice<=0).any():
        raise ValueError('Unexpected non-positive quantity/price: investigate returns and zero-value rows separately.')
    if raw.InvoiceNo.duplicated().all(): raise ValueError('Unexpected invoice identifiers')
    return raw

def fix_dates(raw):
    original = pd.to_datetime(raw.InvoiceDate,format='%Y-%m-%d %H:%M:%S', errors='raise')
    # Date corruption is verifiable via the ordering of invoice identifiers. Swapping
    # both date components for all ambiguous rows restores chronological invoice order.
    # day == month gives the same date, and is harmless to include.
    swap = original.dt.day.le(12) & original.dt.month.le(12) & original.dt.day.ne(original.dt.month)
    fixed = original.copy()
    x = original.loc[swap]
    fixed.loc[swap] = pd.to_datetime(dict(year=x.dt.year,month=x.dt.day,day=x.dt.month,
                                              hour=x.dt.hour,minute=x.dt.minute,second=x.dt.second))
    # Date and weekday columns in this extract reflect the uncorrected date,
    # so ALWAYS derive fresh calendar values from the corrected datetime.
    return original, fixed, swap

def summary(source):
    raw = load_extract(source)
    orig, dates, swap = fix_dates(raw)
    duplicate_mask = raw.duplicated(keep='first')
    d = raw.loc[:,['InvoiceNo','StockCode','Description','Quantity','UnitPrice','CustomerID','Country']].copy()
    d['InvoiceDateCorrected'] = dates
    d['Month'] = dates.dt.strftime('%Y-%m')
    d['Year'] = dates.dt.year
    d['Revenue'] = (d.Quantity * d.UnitPrice).round(2)
    assert d.InvoiceDateCorrected.min()==pd.Timestamp('2010-12-01 08:26:00')
    assert d.InvoiceDateCorrected.max()==pd.Timestamp('2011-12-09 12:50:00')
    # One invoice maps to exactly one customer and country. A small number of
    # invoice numbers have more than one raw timestamp, so pick earliest.
    assert (d.groupby('InvoiceNo').CustomerID.nunique()==1).all()
    assert (d.groupby('InvoiceNo').Country.nunique()==1).all()
    invoice=(d.groupby('InvoiceNo',as_index=False).agg(CustomerID=('CustomerID','first'),
             Country=('Country','first'),InvoiceDate=('InvoiceDateCorrected','min'),
             Revenue=('Revenue','sum'),Items=('Quantity','sum')))
    invoice['Month']=invoice.InvoiceDate.dt.strftime('%Y-%m')
    invoice['Year']=invoice.InvoiceDate.dt.year
    first_month=invoice.groupby('CustomerID')['Month'].min().rename('FirstObservedMonth')
    invoice=invoice.merge(first_month,left_on='CustomerID',right_index=True,validate='many_to_one')
    invoice['CustomerStatus']=np.where(invoice.Month==invoice.FirstObservedMonth,
                 'First observed month','Returning (later month)')
    # Cohort definition is first observed purchase in THIS extract, not acquisition.
    cohorts=(invoice[['CustomerID','Month','FirstObservedMonth']].drop_duplicates()
              .assign(CohortIndex=lambda x:(pd.to_datetime(x.Month).dt.year-pd.to_datetime(x.FirstObservedMonth).dt.year)*12+
                                pd.to_datetime(x.Month).dt.month-pd.to_datetime(x.FirstObservedMonth).dt.month)
              .groupby(['FirstObservedMonth','CohortIndex'],as_index=False).agg(RetainedCustomers=('CustomerID','nunique')))
    cohort_sizes=invoice.groupby('FirstObservedMonth').CustomerID.nunique().rename('CohortSize')
    cohorts=cohorts.merge(cohort_sizes,on='FirstObservedMonth')
    cohorts['RetentionPct']=(cohorts.RetainedCustomers/cohorts.CohortSize*100).round(2)
    monthly=(invoice.groupby('Month',as_index=False).agg(Revenue=('Revenue','sum'),
             Orders=('InvoiceNo','nunique'),ActiveCustomers=('CustomerID','nunique'),
             Units=('Items','sum')))
    monthly['AOV']=(monthly.Revenue/monthly.Orders).round(2)
    monthly['Year']=monthly.Month.str[:4].astype(int)
    monthly['CompleteMonth']=~monthly.Month.isin(['2010-12','2011-12']) # observed endpoints; Dec-2010 has data but no YoY.
    # Each customer is observed under one country in this extract? Check rather than assume.
    customer_country_counts=invoice.groupby('CustomerID').Country.nunique()
    customer_country=(invoice.groupby(['CustomerID','Country']).Revenue.sum().reset_index()
                  .sort_values(['CustomerID','Revenue'],ascending=[True,False])
                  .drop_duplicates('CustomerID').set_index('CustomerID').Country)
    customer=(invoice.groupby('CustomerID').agg(Revenue=('Revenue','sum'),
              Orders=('InvoiceNo','nunique'),FirstPurchase=('InvoiceDate','min'),LastPurchase=('InvoiceDate','max'),
              FirstObservedMonth=('FirstObservedMonth','min')).reset_index())
    asof=d.InvoiceDateCorrected.max().normalize()+pd.Timedelta(days=1)
    customer['RecencyDays']=(asof-customer.LastPurchase.dt.normalize()).dt.days.astype(int)
    customer['Country']=customer.CustomerID.map(customer_country)
    def classify(r):
        rec,freq=r.RecencyDays,r.Orders
        if rec<=30 and freq>=5:return 'Champions'
        if rec<=90 and freq>=5:return 'Loyal active'
        if rec>90 and freq>=3:return 'At risk (rule-based)'
        if rec>90:return 'Dormant (rule-based)'
        if rec<=30:return 'Recent buyers'
        return 'Developing'
    customer['Segment']=customer.apply(classify,axis=1)
    customer['Revenue']=customer.Revenue.round(2)
    customer['FirstPurchase']=customer.FirstPurchase.dt.strftime('%Y-%m-%d')
    customer['LastPurchase']=customer.LastPurchase.dt.strftime('%Y-%m-%d')
    # Data for Power BI intentionally contains only aggregated / anonymized outputs.
    monthly_country=(invoice.groupby(['Month','Country'],as_index=False).agg(
        Revenue=('Revenue','sum'),Orders=('InvoiceNo','nunique'),ActiveCustomers=('CustomerID','nunique'),Units=('Items','sum')))
    monthly_country['Year']=monthly_country.Month.str[:4].astype(int)
    returning=(invoice.pivot_table(index=['Month','Country'],columns='CustomerStatus',values='Revenue',aggfunc='sum',fill_value=0).reset_index())
    monthly_country=monthly_country.merge(returning,on=['Month','Country'],how='left')
    for col in ['First observed month','Returning (later month)']:
        if col not in monthly_country:monthly_country[col]=0.0
    monthly_country.rename(columns={'First observed month':'FirstObservedMonthRevenue',
                                    'Returning (later month)':'ReturningLaterMonthRevenue'},inplace=True)
    monthly_country['AOV']=(monthly_country.Revenue/monthly_country.Orders).round(2)
    country=(invoice.groupby('Country',as_index=False).agg(Revenue=('Revenue','sum'),
                 Orders=('InvoiceNo','nunique'),Customers=('CustomerID','nunique')))
    country['SharePct']=(country.Revenue/country.Revenue.sum()*100).round(2)
    country=country.sort_values('Revenue',ascending=False)
    product=(d.groupby('StockCode',as_index=False).agg(Revenue=('Revenue','sum'),
       Units=('Quantity','sum'),LineItems=('InvoiceNo','size'),Orders=('InvoiceNo','nunique')))
    # Many codes have different descriptions. Report the most frequent observed spelling.
    titles=d.groupby('StockCode').Description.agg(lambda x:x.mode(dropna=True).iloc[0] if len(x.mode(dropna=True)) else '').rename('Description')
    product=product.merge(titles,on='StockCode').sort_values('Revenue',ascending=False)
    segments=(customer.groupby('Segment',as_index=False).agg(Customers=('CustomerID','nunique'),
           Revenue=('Revenue','sum'),AvgOrders=('Orders','mean'),AvgRecency=('RecencyDays','mean')))
    segments['RevenueSharePct']=(segments.Revenue/segments.Revenue.sum()*100).round(2)
    segments=segments.sort_values('Revenue',ascending=False)
    customer_anonym=customer.drop(columns=['CustomerID','FirstPurchase','LastPurchase']).copy()
    customer_anonym.insert(0,'CustomerKey',range(1,len(customer_anonym)+1))
    # Full-year comparison would be misleading: December 2010 and 2011 endpoints differ.
    data={
      'raw_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),
      'rows':len(d),'customers':int(d.CustomerID.nunique()),'invoices':int(d.InvoiceNo.nunique()),
      'products':int(d.StockCode.nunique()),'countries':int(d.Country.nunique()),
      'revenue':round(float(d.Revenue.sum()),2), 'aov':round(float(d.Revenue.sum()/d.InvoiceNo.nunique()),2),
      'date_swapped_rows':int(swap.sum()),'date_same_day_month_rows':int(((orig.dt.day==orig.dt.month)&(orig.dt.day<=12)).sum()),
      'invoice_date_inversions_raw':int((raw.assign(_ts=orig).groupby('InvoiceNo')._ts.min().sort_index().diff().dropna()<pd.Timedelta(0)).sum()),
      'invoice_date_inversions_corrected':int((raw.assign(_ts=dates).groupby('InvoiceNo')._ts.min().sort_index().diff().dropna()<pd.Timedelta(0)).sum()),
      'invoices_with_multiple_corrected_timestamps':int((d.groupby('InvoiceNo').InvoiceDateCorrected.nunique()>1).sum()),
      'customer_multiple_country_count':int((customer_country_counts>1).sum()),
      'duplicate_exact_rows':int(duplicate_mask.sum()),
      'revenue_if_exact_duplicates_dropped':round(float(d.loc[~duplicate_mask,'Revenue'].sum()),2),
      'duplicate_revenue_sensitivity':round(float(d.loc[duplicate_mask,'Revenue'].sum()),2),
      'date_min':str(d.InvoiceDateCorrected.min()),'date_max':str(d.InvoiceDateCorrected.max()),
      'repeat_customers_multi_invoice':int((customer.Orders>=2).sum()),
      'repeat_customers_multi_invoice_revenue':round(float(customer.loc[customer.Orders>=2,'Revenue'].sum()),2),
      'single_invoice_customers':int((customer.Orders==1).sum()),
      'UK_revenue_share_pct':round(float(country.set_index('Country').loc['United Kingdom','SharePct']),2),
      'November_2011_sales':round(float(monthly.set_index('Month').loc['2011-11','Revenue']),2),
      'November_2011_orders':int(monthly.set_index('Month').loc['2011-11','Orders']),
      'September_2011_sales':round(float(monthly.set_index('Month').loc['2011-09','Revenue']),2),
      'September_2011_orders':int(monthly.set_index('Month').loc['2011-09','Orders']),
      'September_2011_AOV':round(float(monthly.set_index('Month').loc['2011-09','AOV']),2),
      'November_2011_AOV':round(float(monthly.set_index('Month').loc['2011-11','AOV']),2),
      'asof_date':asof.strftime('%Y-%m-%d'),
      'currency_note':'Assumed GBP (UK-based Online Retail source); the provided CSV has no currency field.',
      'lineage_note':'Provided 13-column positive-transaction extract, not unfiltered source. Recomputed calendar fields after date repair.',
      'customer_segment_definition':'Rule-based based on end-of-observation recency and lifetime-in-extract invoice frequency; NOT a churn model.'
    }
    dest=ROOT/'results';dest.mkdir(exist_ok=True,parents=True)
    exports={
      'monthly.csv':monthly,
      'monthly_country.csv':monthly_country,
      'country.csv':country,
      'products.csv':product,
      'segments.csv':segments,
      'customer_metrics_anonymized.csv':customer_anonym,
      'cohort_retention.csv':cohorts,
      'invoice_status_summary.csv':invoice.groupby(['Month','CustomerStatus'],as_index=False).agg(Revenue=('Revenue','sum'),Orders=('InvoiceNo','nunique'))
    }
    for name,frame in exports.items():frame.to_csv(dest/name,index=False,float_format='%.2f')
    (dest/'verified_metrics.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    return data, exports

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',default=str(ROOT/'data/raw/Online Retail.csv'));args=parser.parse_args()
    m,_=summary(args.source)
    print(json.dumps(m,indent=2))
