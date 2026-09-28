"""Runs against bundled aggregated snapshots; raw extract optional."""
import json,sys,unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import fix_dates, load_extract

class TestRetailSnapshots(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.metrics=json.loads((R/'verified_metrics.json').read_text())
  cls.mon=pd.read_csv(R/'monthly.csv');cls.monthcountry=pd.read_csv(R/'monthly_country.csv');cls.seg=pd.read_csv(R/'segments.csv');cls.cust=pd.read_csv(R/'customer_metrics_anonymized.csv');cls.cohort=pd.read_csv(R/'cohort_retention.csv')
 def test_population_and_totals(self):
  m=self.metrics
  self.assertEqual((m['rows'],m['invoices'],m['customers']), (384721,17635,4261))
  self.assertAlmostEqual(self.mon.Revenue.sum(),m['revenue'],places=1)
  self.assertAlmostEqual(self.seg.Revenue.sum(),m['revenue'],places=1)
  self.assertAlmostEqual(self.cust.Revenue.sum(),m['revenue'],places=1)
  self.assertEqual(len(self.cust),m['customers'])
 def test_sales_summaries_match(self):
  mc=self.monthcountry.groupby('Month').agg(Revenue=('Revenue','sum'),Orders=('Orders','sum')).sort_index()
  mm=self.mon.set_index('Month').loc[mc.index]
  self.assertTrue((mc.Revenue-mm.Revenue).abs().max()<.04)
  self.assertTrue((mc.Orders==mm.Orders).all())
 def test_october_november_sales_not_partial(self):
  self.assertAlmostEqual(self.mon.set_index('Month').loc['2011-11','Revenue'],881270.87,places=2)
  self.assertEqual(self.mon.Month.min(),'2010-12');self.assertEqual(self.mon.Month.max(),'2011-12')
  self.assertFalse(bool(self.mon.set_index('Month').loc['2011-12','CompleteMonth']))
 def test_cohort_denominator(self):
  x=self.cohort[self.cohort.CohortIndex==0]
  self.assertEqual(x.CohortSize.sum(),self.metrics['customers'])
  self.assertTrue((x.RetentionPct==100.0).all())
  dec=self.cohort[(self.cohort.FirstObservedMonth=='2010-12')&(self.cohort.CohortIndex==1)].iloc[0]
  self.assertAlmostEqual(dec.RetentionPct,36.17,places=2)
 def test_segments_are_exclusive(self):
  self.assertEqual(self.seg.Customers.sum(),self.metrics['customers'])
  champ=self.seg.set_index('Segment').loc['Champions','RevenueSharePct']
  self.assertAlmostEqual(champ,54.77,places=2)
 def test_calendar_repair_synthetic(self):
  d=pd.DataFrame({'InvoiceDate':['2010-01-12 08:26:00','2011-11-15 09:10:00','2011-05-05 09:10:00']})
  raw,fixed,mask=fix_dates(d)
  self.assertEqual(fixed.iloc[0].strftime('%Y-%m-%d'),'2010-12-01')
  self.assertEqual(fixed.iloc[1],raw.iloc[1]);self.assertEqual(fixed.iloc[2],raw.iloc[2]);self.assertEqual(int(mask.sum()),1)
 def test_quality_numbers(self):
  m=self.metrics;self.assertEqual(m['date_swapped_rows'],147998);self.assertEqual(m['invoice_date_inversions_corrected'],0)
  self.assertAlmostEqual(m['revenue']-m['revenue_if_exact_duplicates_dropped'],23119.37,places=1)
 def test_project_files(self):
  self.assertTrue((ROOT/'powerbi/Retail_Revenue_Intelligence.pbip').exists())
  self.assertTrue((ROOT/'report/interactive_dashboard.html').exists())
  self.assertTrue((ROOT/'report/executive_field_report.pdf').exists())
  self.assertTrue((ROOT/'charts/LinkedIn_Featured_Sales.png').exists())
if __name__=='__main__':unittest.main()
