"""Publication-size figures built only from verified analysis output."""
from pathlib import Path
import pandas as pd,numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
ROOT=Path(__file__).resolve().parents[1];res=ROOT/'results';out=ROOT/'charts';out.mkdir(exist_ok=True)
COL={'navy':'#101A2C','dark':'#1D2C42','muted':'#64748B','teal':'#2BBBAA','coral':'#EF837B','gold':'#E5A65E','blue':'#5A80CC'}
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,
 'axes.edgecolor':'#CBD5E1','grid.color':'#E5EAF1','text.color':COL['navy'],'axes.labelcolor':COL['muted'],
 'xtick.color':COL['muted'],'ytick.color':COL['muted'],'figure.facecolor':'white','axes.facecolor':'white','font.size':10})
def save(name):plt.savefig(out/name, dpi=185,bbox_inches='tight',pad_inches=.3,facecolor='white');plt.close()
mon=pd.read_csv(res/'monthly.csv');mon=mon[mon.Month.between('2011-01','2011-11')]
fig,ax=plt.subplots(figsize=(10,3.8));x=np.arange(len(mon));ax.plot(x,mon.Revenue/1000,color=COL['teal'],lw=3,marker='o',ms=6);ax.fill_between(x,mon.Revenue/1000,alpha=.08,color=COL['teal']);ax.set_xticks(x,mon.Month.str[-2:].map({'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov'}));ax.set_ylim(0,1000);ax.set_ylabel('Recorded sales value (£ thousands)*');ax.grid(axis='y');ax.set_title('Autumn sales increased, but the cause needs a second metric',fontweight='bold',loc='left',pad=18)
for ind in [8,10]:ax.annotate(f'£{mon.iloc[ind].Revenue/1000:,.0f}k',xy=(ind,mon.iloc[ind].Revenue/1000),xytext=(ind-.5,mon.iloc[ind].Revenue/1000+100),color=COL['navy'],fontweight='bold',arrowprops={'arrowstyle':'-','color':COL['muted']})
save('01_monthly_sales.png')
sel=mon[mon.Month.isin(['2011-09','2011-11'])].copy()
fig,ax=plt.subplots(figsize=(8.2,2.95));ax.set_xlim(-.34,1.1);ax.set_ylim(-.25,5.4);ax.axis('off')
from matplotlib.patches import FancyBboxPatch
for k,(title,field,maxval,formatter) in enumerate([('NUMBER OF INVOICES','Orders',2800,lambda v:f'{v:,.0f}'),('AVERAGE ORDER VALUE','AOV',440,lambda v:f'£{v:,.0f}')]):
 top=4.4-k*2.55;ax.text(-.3,top+.72,title,weight='bold',fontsize=13,color=COL['navy'])
 for j,idx in enumerate([0,1]):
  val=float(sel.iloc[idx][field]);y=top-j*.69
  ax.text(-.3,y+.13,'SEP' if j==0 else 'NOV',weight='bold',fontsize=10,color=COL['muted'])
  ax.add_patch(FancyBboxPatch((0,y),.80,.29,boxstyle='round,pad=0.015,rounding_size=.05',fc='#E9EFF3',ec='none'))
  ax.add_patch(FancyBboxPatch((0,y),.80*val/maxval,.29,boxstyle='round,pad=0.015,rounding_size=.05',fc=COL['blue'] if j==0 else COL['teal'],ec='none'))
  ax.text(.85,y+.11,formatter(val),fontsize=11,weight='bold',color=COL['navy'])
 growth=(float(sel.iloc[1][field])/float(sel.iloc[0][field])-1)*100
 ax.text(0,top-1.02,f'CHANGE  {growth:+.1f}%',weight='bold',fontsize=10,color=COL['coral'])
fig.suptitle('More invoices, not larger average orders',fontsize=14,weight='bold',x=.035,y=1.02,ha='left')
save('02_orders_vs_aov.png')
segments=pd.read_csv(res/'segments.csv').sort_values('RevenueSharePct',ascending=True)
fig,ax=plt.subplots(figsize=(10,4));ax.barh(segments.Segment,segments.RevenueSharePct,color=[COL['teal'] if x=='Champions' else COL['blue'] for x in segments.Segment]);ax.set_xlim(0,62);ax.set_xlabel('Share of recorded revenue (%)');ax.grid(axis='x');ax.set_axisbelow(True)
for i,x in enumerate(segments.RevenueSharePct):ax.text(x+.6,i,f'{x:.1f}%',va='center',fontweight='bold')
ax.set_title('Rule-based groups: historic revenue contribution',fontweight='bold',loc='left',pad=17)
save('03_customer_segments.png')
ret=pd.read_csv(res/'cohort_retention.csv');ret=ret[ret.FirstObservedMonth.between('2010-12','2011-08')];values=ret.pivot(index='FirstObservedMonth',columns='CohortIndex',values='RetentionPct').reindex(columns=range(5));fig,ax=plt.subplots(figsize=(9.1,4));m=np.ma.masked_invalid(values.values);cm=plt.cm.YlGn;cm.set_bad('white');img=ax.imshow(m,cmap=cm,aspect='auto',vmin=0,vmax=100)
for i in range(len(values)):
 for j in range(values.shape[1]):
  if np.isfinite(values.iloc[i,j]):ax.text(j,i,f'{values.iloc[i,j]:.0f}%',ha='center',va='center',fontsize=9,fontweight='bold',color='#0C2636' if values.iloc[i,j]<56 else 'white')
ax.set_xticks(range(5),['First month','+1 month','+2 months','+3 months','+4 months']);ax.set_yticks(range(len(values)),values.index);ax.tick_params(length=0);ax.set_title('Customer cohorts: who placed an order again?',fontweight='bold',loc='left',pad=18);fig.colorbar(img,ax=ax,label='Monthly retention (%)',fraction=.036,pad=.04)
save('04_cohort_retention.png')
ct=pd.read_csv(res/'country.csv');non=ct[ct.Country!='United Kingdom'].head(7).iloc[::-1];fig,ax=plt.subplots(figsize=(8,3.7));ax.barh(non.Country,non.Revenue/1000,color=COL['blue']);ax.set_xlabel('Recorded sales value (£ thousands)*');ax.grid(axis='x');ax.set_axisbelow(True)
for i,v in enumerate(non.Revenue/1000):ax.text(v+2,i,f'{v:.0f}k',va='center',fontweight='bold')
ax.set_title('Markets outside the UK (UK is 84.4% of total)',fontweight='bold',loc='left',pad=18);ax.set_xlim(0,215);save('05_non_uk_markets.png')
prod=pd.read_csv(res/'products.csv').head(7).iloc[::-1];fig,ax=plt.subplots(figsize=(9,4.3));ax.barh(prod.Description.str.strip(),prod.Revenue/1000,color=COL['teal']);ax.set_xlabel('Recorded sales value (£ thousands)*');ax.grid(axis='x');ax.set_axisbelow(True)
for i,v in enumerate(prod.Revenue/1000):ax.text(v+1,i,f'{v:.0f}k',va='center',fontweight='bold')
ax.set_xlim(0,130);ax.set_title('Highest-revenue products in this extract',fontweight='bold',loc='left',pad=16);save('06_products.png')
print('Saved six verified, labelled analytical charts')
