"""Generate 4-page portable Power BI Project (.pbip) with embedded aggregate CSVs.

Trade-off: precomputed anonymized summary sources embedded as compressed CSV so
Power BI Desktop can import offline; rerun this script to refresh after analysis.
Generated/JSON structurally checked, but cannot claim Windows Desktop validation.
"""
from pathlib import Path
import json,uuid,hashlib,gzip,base64,pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results';BASE=ROOT/'powerbi';NM='Retail_Revenue_Intelligence';MD=BASE/(NM+'.SemanticModel');RD=BASE/(NM+'.Report');M=MD/'definition';R=RD/'definition';P='https://developer.microsoft.com/json-schemas/fabric/'
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(value,encoding='utf8')
def j(path,value):write(path,json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def gid(s):return hashlib.sha1(s.encode()).hexdigest()[:20]
def plat(kind):return {'$schema':P+'gitIntegration/platformProperties/2.0.0/schema.json','metadata':{'type':kind,'displayName':'Retail Revenue Intelligence'},'config':{'version':'2.0','logicalId':str(uuid.uuid4())}}
# Publish only aggregate/anonymized stats, not the user's 384k transaction rows.
sales=pd.read_csv(D/'monthly_country.csv');customers=pd.read_csv(D/'customer_metrics_anonymized.csv');co=pd.read_csv(D/'cohort_retention.csv')
co=co[co.CohortIndex==1].loc[:,['FirstObservedMonth','CohortSize','RetainedCustomers','RetentionPct']].rename(columns={'FirstObservedMonth':'CohortMonth','CohortSize':'CustomersInCohort','RetainedCustomers':'CustomersNextMonth','RetentionPct':'NextMonthRetentionPct'})
# One aggregate forecast in the PBIP; SKU detail remains in the standalone dashboard.
forecast=pd.read_csv(D/'forecast_weekly_history.csv')[['WeekStart','All products']].rename(columns={'All products':'ObservedUnits'})
hold=pd.read_csv(D/'forecast_holdout_weeks.csv').query('Series == "All products"')
forecast=forecast.merge(hold[['WeekStart','ForecastUnits','BaselineUnits']],on='WeekStart',how='left')
forecast['IsHoldout']=['Yes' if date in set(hold.WeekStart) else 'No' for date in forecast.WeekStart]
sku_errors=pd.read_csv(D/'forecast_evaluation.csv').query('Series != "All products"')
# Separate ML experiment, independently selected on five earlier validation folds.
mlscores=pd.read_csv(D/'ml_holdout_comparison.csv').query('Series == "All products"')[
    ['Method','ValidationWAPE','HoldoutWAPE','SelectedByValidation']].copy()
mlscores['SelectedByValidation']=mlscores['SelectedByValidation'].map({True:'Yes',False:'No'})
mlweeks=pd.read_csv(D/'ml_holdout_weeks.csv').query('Series == "All products"')
mlwide=(mlweeks.pivot(index='WeekStart',columns='Method',values='ForecastUnits')
        .rename(columns={'four_week_mean':'MeanForecast','eight_week_damped_trend':'DampedForecast',
                         'random_forest':'RandomForestForecast','xgboost':'XGBoostForecast'})
        [['MeanForecast','DampedForecast','RandomForestForecast','XGBoostForecast']])
mlactual=mlweeks.query('Method == "four_week_mean"').set_index('WeekStart')[['ActualUnits']]
mlwide=mlactual.join(mlwide).reset_index()


# Avoid implicit Python list syntax escaping in M. This file is fully portable
# even without a local CSV; the user can regenerate from locally supplied data.
def encoded(df):
 from io import StringIO
 s=df.to_csv(index=False,float_format='%.2f');return base64.b64encode(gzip.compress(s.encode(),mtime=0)).decode('ascii')
tables={
 'Sales':(sales,{'Month':'string','Country':'string','Revenue':'double','Orders':'int64','ActiveCustomers':'int64','Units':'int64','Year':'int64','FirstObservedMonthRevenue':'double','ReturningLaterMonthRevenue':'double','AOV':'double'}),
 'Customers':(customers,{'CustomerKey':'int64','Revenue':'double','Orders':'int64','FirstObservedMonth':'string','RecencyDays':'int64','Country':'string','Segment':'string'}),
 'CohortMonth1':(co,{'CohortMonth':'string','CustomersInCohort':'int64','CustomersNextMonth':'int64','NextMonthRetentionPct':'double'}),
 'ForecastAll':(forecast,{'WeekStart':'string','ObservedUnits':'int64','ForecastUnits':'double','BaselineUnits':'double','IsHoldout':'string'}),
 'ForecastSkuErrors':(sku_errors,{'Series':'string','Product':'string','SelectedMethod':'string','HoldoutWAPE':'double','BaselineHoldoutWAPE':'double','ActualTotal':'int64','ForecastTotal':'double','BaselineForecastTotal':'double'}),
 'MLModelScores':(mlscores,{'Method':'string','ValidationWAPE':'double','HoldoutWAPE':'double','SelectedByValidation':'string'}),
 'MLHoldout':(mlwide,{'WeekStart':'string','ActualUnits':'double','MeanForecast':'double','DampedForecast':'double','RandomForestForecast':'double','XGBoostForecast':'double'})
}
j(BASE/(NM+'.pbip'),{'$schema':P+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':NM+'.Report'}}],'settings':{'enableAutoRecovery':True}})
j(RD/'.platform',plat('Report'));j(MD/'.platform',plat('SemanticModel'))
j(RD/'definition.pbir',{'$schema':P+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../'+NM+'.SemanticModel'}}})
j(MD/'definition.pbism',{'$schema':P+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.2','settings':{'qnaEnabled':True}})
write(M/'database.tmdl','database\n\tcompatibilityLevel: 1600\n')
write(M/'model.tmdl','model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\n'+'\n'.join('ref table '+n for n in tables)+'\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n')
measures={
 'Sales':{
 'Recorded Sales':'SUM(Sales[Revenue])',
 'Invoices':'SUM(Sales[Orders])',
 'Average Order Value':'DIVIDE([Recorded Sales], [Invoices])',
 'Later Month Buyer Sales':'SUM(Sales[ReturningLaterMonthRevenue])',
 'Later Month Buyer Share':'DIVIDE([Later Month Buyer Sales], [Recorded Sales])',
 },
 'Customers':{
 'Customer Count':'COUNTROWS(Customers)',
 'Multiple Order Buyers':'CALCULATE([Customer Count], KEEPFILTERS(Customers[Orders] >= 2))',
 'Multi Order Buyer Sales Share':'DIVIDE(CALCULATE(SUM(Customers[Revenue]), KEEPFILTERS(Customers[Orders] >= 2)),SUM(Customers[Revenue]))',
 'Champion Sales Share':'DIVIDE(CALCULATE(SUM(Customers[Revenue]),KEEPFILTERS(Customers[Segment] = "Champions")),SUM(Customers[Revenue]))',
 'Customer Sales':'SUM(Customers[Revenue])',
 },
 'CohortMonth1':{'Next Month Cohort Retention':'DIVIDE(SUM(CohortMonth1[CustomersNextMonth]),SUM(CohortMonth1[CustomersInCohort]))'},
 'ForecastAll':{
  'Weekly Observed Units':'SUM(ForecastAll[ObservedUnits])',
  'Weekly Selected Forecast':'SUM(ForecastAll[ForecastUnits])',
  'Weekly Baseline Forecast':'SUM(ForecastAll[BaselineUnits])',
  'Actual Holdout Units':'CALCULATE(SUM(ForecastAll[ObservedUnits]),ForecastAll[IsHoldout]="Yes")',
  'Selected Holdout Forecast':'SUM(ForecastAll[ForecastUnits])',
  'Selected Holdout WAPE':'DIVIDE(SUMX(FILTER(ForecastAll,ForecastAll[IsHoldout]="Yes"),ABS(ForecastAll[ObservedUnits]-ForecastAll[ForecastUnits])),CALCULATE(SUM(ForecastAll[ObservedUnits]),ForecastAll[IsHoldout]="Yes"))',
  'Simple Holdout WAPE':'DIVIDE(SUMX(FILTER(ForecastAll,ForecastAll[IsHoldout]="Yes"),ABS(ForecastAll[ObservedUnits]-ForecastAll[BaselineUnits])),CALCULATE(SUM(ForecastAll[ObservedUnits]),ForecastAll[IsHoldout]="Yes"))'},
 'ForecastSkuErrors':{'Selected SKU WAPE':'SUM(ForecastSkuErrors[HoldoutWAPE])'},
 'MLModelScores':{
   'ML Validation WAPE':'DIVIDE(AVERAGE(MLModelScores[ValidationWAPE]),100)',
   'ML Holdout WAPE':'DIVIDE(AVERAGE(MLModelScores[HoldoutWAPE]),100)',
   'RF Validation WAPE':'CALCULATE([ML Validation WAPE],MLModelScores[Method]="random_forest")',
   'RF Holdout WAPE':'CALCULATE([ML Holdout WAPE],MLModelScores[Method]="random_forest")',
   'Damped Holdout WAPE':'CALCULATE([ML Holdout WAPE],MLModelScores[Method]="eight_week_damped_trend")',
   'Baseline Holdout WAPE':'CALCULATE([ML Holdout WAPE],MLModelScores[Method]="four_week_mean")',
 },
 'MLHoldout':{
   'ML Actual Units':'SUM(MLHoldout[ActualUnits])',
   'ML RF Forecast':'SUM(MLHoldout[RandomForestForecast])',
   'ML Damped Forecast':'SUM(MLHoldout[DampedForecast])',
   'ML XGBoost Forecast':'SUM(MLHoldout[XGBoostForecast])',
   'ML Moving Average':'SUM(MLHoldout[MeanForecast])',
 }
}
fmt=lambda label:'0.0%' if 'Share' in label or 'Retention' in label or ' WAPE' in label else ('£#,0.00' if 'Value' in label else ('£#,0' if 'Sales' in label else '#,0'))
for name,(df,types) in tables.items():
 text='table '+name+'\n\tlineageTag: '+str(uuid.uuid4())+'\n\n'
 for k,t in types.items():
  text+=f'\tcolumn {k}\n\t\tdataType: {t}\n\t\tlineageTag: {uuid.uuid4()}\n\t\tsummarizeBy: '+('none' if t=='string' or k in ('Year','CustomerKey','Orders','RecencyDays','CustomersInCohort','CustomersNextMonth') else 'sum')+f'\n\t\tsourceColumn: {k}\n\n'
 for label,ex in measures[name].items():text+='\tmeasure '+"'"+label+"' = "+ex+'\n\t\tlineageTag: '+str(uuid.uuid4())+f'\n\t\tformatString: {fmt(label)}\n\n'
 # M CSV embedded avoids invalid local paths after ZIP download. Data is anonymized/
 # preaggregated; this is a reproducible DEMO snapshot, not a live ETL refresh.
 zipped=encoded(df)
 m=('let\n'
    f'    Contents = Binary.Decompress(Binary.FromText("{zipped}", BinaryEncoding.Base64), Compression.GZip),\n'
    '    CSV = Csv.Document(Contents,[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
    '    Headers = Table.PromoteHeaders(CSV,[PromoteAllScalars=true]),\n'
    '    Typed = Table.TransformColumnTypes(Headers, {'+','.join('{"'+col+'", '+('Int64.Type' if dtype=='int64' else 'type number' if dtype=='double' else 'type text')+'}' for col,dtype in types.items())+'})\n'
    'in\n    Typed')
 text+='\tpartition '+name+' = m\n\t\tmode: import\n\t\tsource =\n'+'\n'.join('\t\t\t\t'+line for line in m.splitlines())+'\n\n\tannotation PBI_ResultType = Table\n'
 write(M/('tables/'+name+'.tmdl'),text)
write(BASE/'dax_measures.dax','\n\n'.join('-- '+k+' / '+n+'\n'+n+' = '+e for k,meas in measures.items() for n,e in meas.items())+'\n')
PA={'bg':'#0E1728','panel':'#192A40','white':'#F8FBFD','muted':'#AABFD0','teal':'#64DECD','peach':'#FFB18E','blue':'#9FB2FF','pink':'#F18B9D'}
theme={'name':'RetailSignals','dataColors':[PA['teal'],PA['peach'],PA['blue'],PA['pink']], 'foreground':PA['white'],'foregroundNeutralSecondary':PA['muted'],'background':PA['bg'],'backgroundLight':PA['panel'],'tableAccent':PA['teal'],'textClasses':{'callout':{'fontSize':28,'fontFace':'Segoe UI Semibold','color':PA['white']},'title':{'fontSize':12,'fontFace':'Segoe UI Semibold','color':PA['white']},'label':{'fontSize':11,'fontFace':'Segoe UI','color':PA['muted']}}}
j(BASE/'power_bi_theme.json',theme);j(RD/'StaticResources/SharedResources/BaseThemes/RetailSignals.json',theme)
SC=P+'item/report/definition/';j(R/'version.json',{'$schema':SC+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
j(R/'report.json',{'$schema':SC+'report/3.2.0/schema.json','themeCollection':{'baseTheme':{'name':'RetailSignals','reportVersionAtImport':{'visual':'2.6.0','report':'3.1.0','page':'2.3.0'},'type':'SharedResources'}},'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':'RetailSignals','path':'BaseThemes/RetailSignals.json','type':'BaseTheme'}]}], 'settings':{'useStylableVisualContainerHeader':True,'exportDataMode':'AllowSummarized','defaultDrillFilterOtherVisuals':True}})
ids=[gid('retail-page-'+s) for s in ['sales','customers','forecast','ml']]
j(R/'pages/pages.json',{'$schema':SC+'pagesMetadata/1.0.0/schema.json','pageOrder':ids,'activePageName':ids[0]})
for pg,label in zip(ids,['Sales and Markets','Customers and Cohorts','Demand Forecasting','ML Model Comparison']):
 page_obj = {
   '$schema':SC+'page/2.1.0/schema.json', 'name':pg,
   'displayName':label, 'displayOption':'FitToPage', 'width':1440, 'height':900,
   'objects': {'background':[{'properties':{
      'color': {'solid': {'color': {'expr': {'Literal': {'Value': "'"+PA['bg']+"'"}}}}},
      'transparency': {'expr': {'Literal': {'Value':'0D'}}}
   }}]}
 }
 j(R/f'pages/{pg}/page.json',page_obj)
def col(table,k):return {'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':k}}
def measure(table,k):return {'Measure':{'Expression':{'SourceRef':{'Entity':table}},'Property':k}}
def lit(x):return {'expr':{'Literal':{'Value':x}}}
def solid(c):return {'solid':{'color':lit("'"+c+"'")}}
count=0
def add(pg,key,typ,x,y,w,h,roles=None,txt=None,size='13pt',title=None,color=None):
 global count
 count+=1;vid=gid(pg+key);v={'visualType':typ,'drillFilterOtherVisuals':typ!='textbox'}
 if roles:
  v['query']={'queryState':{role:{'projections':[{'field':f,'queryRef':next(iter(f.values()))['Expression']['SourceRef']['Entity']+'.'+next(iter(f.values()))['Property'],'nativeQueryRef':next(iter(f.values()))['Property']} for f in fields]} for role,fields in roles.items()}}
 if typ=='textbox':v['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':txt or '', 'textStyle':{'fontFamily':'Segoe UI','fontSize':size,'fontWeight':'bold' if title else 'normal','color':color or PA['white']}}],'horizontalTextAlignment':'left'}]}}]}
 else:
  v['visualContainerObjects']={'background':[{'properties':{'show':lit('true'),'color':solid(PA['panel']),'transparency':lit('0D')}}],'visualHeader':[{'properties':{'show':lit('false')}}]}
  if title:v['visualContainerObjects']['title']=[{'properties':{'show':lit('true'),'text':lit("'"+title.replace("'","''")+"'"),'fontColor':solid(PA['white'])}}]
 j(R/f'pages/{pg}/visuals/{vid}/visual.json',{'$schema':SC+'visualContainer/2.7.0/schema.json','name':vid,'position':{'x':x,'y':y,'width':w,'height':h,'z':1000+count,'tabOrder':1000+count},'visual':v})
a,b,c,d=ids
for pg,eyebrow,title,subtitle in [(a,'SALES INTELLIGENCE / 01','More orders, not bigger baskets','Recorded sales and invoices  ·  historical filtered extract  ·  assumed GBP'),(b,'CUSTOMER INTELLIGENCE / 02','Returning is not retention','Rule-based segments and first-observed monthly cohorts  ·  filtered extract'),(c,'DEMAND EXPERIMENT / 03','Can a simple forecast anticipate the surge?','Historical 4-week backtest   ·   positive sold units are not unconstrained demand'),(d,'ML COMPARISON / 04','Did machine learning actually help?','Random Forest + XGBoost vs statistical rules   ·   same earlier folds and final test')]:
 add(pg,'eyebrow','textbox',44,14,1100,28,txt=eyebrow,size='11pt',color=PA['teal'],title='x')
 add(pg,'title','textbox',44,54,1200,54,txt=title,size='30pt',title='x')
 add(pg,'subtitle','textbox',44,118,1270,35,txt=subtitle,size='11pt',color=PA['muted'])
for i,(lab,me) in enumerate([('RECORDED SALES','Recorded Sales'),('INVOICES','Invoices'),('AVG ORDER VALUE','Average Order Value'),('LATER-MONTH SALES SHARE','Later Month Buyer Share')]):
 x=44+i*347
 add(a,'lab'+str(i),'textbox',x,171,296,28,txt=lab,size='10pt',title='x',color=PA['muted'])
 add(a,'kpi'+str(i),'cardVisual',x,208,308,98,roles={'Data':[measure('Sales',me)]})
add(a,'sales_chart','columnChart',44,349,815,346,roles={'Category':[col('Sales','Month')],'Y':[measure('Sales','Recorded Sales')]},title='Monthly sales / assumed GBP')
add(a,'market_chart','barChart',878,349,513,346,roles={'Category':[col('Sales','Country')],'Y':[measure('Sales','Recorded Sales')]},title='Recorded sales by country')
add(a,'country_slicer','slicer',44,718,335,103,roles={'Values':[col('Sales','Country')]})
add(a,'year_slicer','slicer',405,718,295,103,roles={'Values':[col('Sales','Year')]})
add(a,'sales_note','textbox',748,724,642,115,txt='Scope: filters affect sales aggregates. Do not compare partial Dec 2011 as a full month. Months/countries are precalculated; raw data are deliberately not redistributed.',size='12pt',color=PA['muted'])
for i,(lab,me) in enumerate([('OBSERVED CUSTOMERS','Customer Count'),('MULTI-ORDER BUYERS','Multiple Order Buyers'),('THEIR SALES SHARE','Multi Order Buyer Sales Share'),('CHAMPION SEGMENT SHARE','Champion Sales Share')]):
 x=44+i*347
 add(b,'lab'+str(i),'textbox',x,171,296,28,txt=lab,size='10pt',title='x',color=PA['muted'])
 add(b,'kpi'+str(i),'cardVisual',x,208,308,98,roles={'Data':[measure('Customers',me)]})
add(b,'segchart','barChart',44,349,750,349,roles={'Category':[col('Customers','Segment')],'Y':[measure('Customers','Customer Sales')]},title='Rule-based groups: retrospective sales')
add(b,'cochart','columnChart',818,349,572,349,roles={'Category':[col('CohortMonth1','CohortMonth')],'Y':[measure('CohortMonth1','Next Month Cohort Retention')]},title='Following-month retention by first-observed cohort')
add(b,'seg_slicer','slicer',44,719,335,101,roles={'Values':[col('Customers','Country')]})
add(b,'note','textbox',418,721,943,114,txt='Customer country uses the highest-spend market for eight cross-country customers. Cohort chart is full-extract and does NOT follow the country slicer. Group labels are descriptive, not churn predictions.',size='12pt',color=PA['muted'])
# Forecasting page shows the complete historical weekly aggregate and the 4 final
# held-out weeks. It intentionally makes no live or current-demand claim.
for i,(label,met) in enumerate([('FINAL 4 WEEKS / ACTUAL','Actual Holdout Units'),('SELECTED FORECAST','Selected Holdout Forecast'),('SELECTED WAPE','Selected Holdout WAPE'),('SIMPLE BASELINE WAPE','Simple Holdout WAPE')]):
 x=44+i*347
 add(c,'flab'+str(i),'textbox',x,171,296,28,txt=label,size='10pt',title='x',color=PA['muted'])
 add(c,'fkpi'+str(i),'cardVisual',x,208,308,98,roles={'Data':[measure('ForecastAll',met)]})
add(c,'forecast_history','lineChart',44,348,930,351,roles={'Category':[col('ForecastAll','WeekStart')],'Y':[measure('ForecastAll','Weekly Observed Units'),measure('ForecastAll','Weekly Selected Forecast'),measure('ForecastAll','Weekly Baseline Forecast')]},title='Weekly sold units · historical and final holdout')
add(c,'sku_error','barChart',995,349,398,350,roles={'Category':[col('ForecastSkuErrors','Series')],'Y':[measure('ForecastSkuErrors','Selected SKU WAPE')]},title='SKU forecast errors · holdout WAPE in %')
add(c,'forecast_note','textbox',44,724,1330,104,txt='Forecasts were chosen with earlier rolling folds; final test is 7 Nov–4 Dec 2011. The model underpredicted late-autumn sales. Short historical sample, no stockout/promotions data and no out-of-sample live validation. Open report/forecast_experiment.html to compare models by product.',size='12pt',color=PA['muted'])
# The fourth page compares the entire candidate pool on the *same* holdout.
# The method chosen by validation is not retroactively replaced by the best test result.
for i,(label,met) in enumerate([('RF VALIDATION WAPE','RF Validation WAPE'),('RF HOLDOUT WAPE','RF Holdout WAPE'),('DAMPED HOLDOUT WAPE','Damped Holdout WAPE'),('BASELINE HOLDOUT WAPE','Baseline Holdout WAPE')]):
 x=44+i*347
 add(d,'ml_label'+str(i),'textbox',x,171,299,28,txt=label,size='10pt',title='x',color=PA['muted'])
 add(d,'ml_card'+str(i),'cardVisual',x,208,307,98,roles={'Data':[measure('MLModelScores',met)]})
add(d,'ml_bars','columnChart',44,354,770,350,roles={'Category':[col('MLModelScores','Method')],
 'Y':[measure('MLModelScores','ML Validation WAPE'),measure('MLModelScores','ML Holdout WAPE')]},title='Validation versus untouched test  ·  WAPE')
add(d,'ml_weekly','lineChart',837,354,555,350,roles={'Category':[col('MLHoldout','WeekStart')],
 'Y':[measure('MLHoldout','ML Actual Units'),measure('MLHoldout','ML RF Forecast'),measure('MLHoldout','ML Damped Forecast')]},title='Observed units versus RF and damped trend')
add(d,'ml_note','textbox',44,734,1330,104,txt='Random Forest (19.1%) was chosen by five earlier validation windows but its test error was 15.7%; the damped trend scored 13.4% on this one final test. Test scores are diagnostics, not retrospective model selection. A year of recorded sales is not sufficient for production demand planning.',size='12pt',color=PA['muted'])
readme='''# Power BI: open the editable 4-page PBIP

Double-click **Retail_Revenue_Intelligence.pbip** with an up-to-date Power BI Desktop version supporting PBIP/TMDL. The project includes four pages: **Sales and Markets**, **Customers and Cohorts**, **Demand Forecasting**, and **ML Model Comparison**.

This report imports *compressed, embedded* precomputed CSV snapshots. It needs no access to your raw third-party retail CSV and does not depend on your local file paths. The snapshots come from the actual Python analysis in `results/` (sales by month/country, anonymized customer metrics, first-following-month cohort summary, and aggregate weekly forecast backtest). The original forecasting page contains the statistical all-product series. The separate ML page compares Random Forest and XGBoost with the same statistical methods. Both pages use precomputed historical aggregate snapshots; the standalone ML HTML explores individual products.

**To refresh** after updating the user-supplied raw extract, run `python scripts/analyze.py --source 'data/raw/Online Retail.csv'` then `python scripts/demand_forecast.py --source 'data/raw/Online Retail.csv'` and then `python scripts/ml_forecast_comparison.py --source 'data/raw/Online Retail.csv'` and `python scripts/build_powerbi.py`; reopen the PBIP. The snapshot tables are not live ETL connections. This is an editable Power BI project; I generated and structurally validated the definitions but did **not** open/verify them on Windows Power BI Desktop. In Desktop, verify visuals and filters before claiming it as an interactive deployed report or sharing screenshots.

The customer page and cohort bar use separate precomputed tables. Customer country assigns the highest-sales country to the **eight cross-country customers**; the cohort chart is globally aggregated and unaffected by the customer-country slicer. Do not imply the slicer changes cohort retention. The source excludes cancellations and unknown customers, and excludes part of December 2011. On both forecasting pages, WAPE values are evaluated on a historical held-out four-week test only; this is not a 2026 operational prediction, and observed sold units are not total customer demand.
'''
write(BASE/'OPEN_IN_DESKTOP.md',readme)
print('PBIP generated:',len(list(R.rglob('visual.json'))),'visuals across',len(ids),'pages;',[(n,len(df)) for n,(df,types) in tables.items()])
