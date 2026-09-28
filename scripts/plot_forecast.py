"""Rebuild historical out-of-time forecast visuals from aggregated CSV outputs."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results';OUT=ROOT/'charts';OUT.mkdir(exist_ok=True)
BG='#0c1424';PANEL='#18273d';WHITE='#f5f7fd';MUTED='#aec0d1';TEAL='#64decd';PEACH='#ffb18e';PINK='#f18b9d';BLUE='#9fb2ff';EDGE='#304761'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'text.color':WHITE,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':EDGE})

history=pd.read_csv(R/'forecast_weekly_history.csv',parse_dates=['WeekStart'])
holdout=pd.read_csv(R/'forecast_holdout_weeks.csv',parse_dates=['WeekStart'])
eval_df=pd.read_csv(R/'forecast_evaluation.csv')
sum_df=eval_df.set_index('Series')
test=holdout.query('Series == "All products"').sort_values('WeekStart')
all_products=sum_df.loc['All products']
fig=plt.figure(figsize=(16,9),dpi=145,facecolor=BG)
fig.text(.063,.938,'RETAIL / INTELLIGENCE     •     DEMAND FORECASTING',fontsize=13,fontweight='bold',color=TEAL)
fig.text(.063,.872,'Could I have anticipated the November surge?',fontsize=29,fontweight='bold',color=WHITE)
fig.text(.063,.825,'Historical 4-week holdout, 7 Nov–4 Dec 2011 · weekly observed sold units across all products',fontsize=12,color=MUTED)
for x,lab,val,sub,col in [(.063,'HOLDOUT ACTUAL',f"{all_products.ActualTotal:,.0f}",'OBSERVED UNITS',WHITE),(.30,'SELECTED FORECAST',f"{all_products.ForecastTotal:,.0f}",all_products.SelectedMethod.replace('_',' ').upper(),TEAL),(.537,'MODEL ERROR',f"{all_products.HoldoutWAPE:.1f}%",'HOLDOUT WAPE',PEACH),(.774,'BASELINE ERROR',f"{all_products.BaselineHoldoutWAPE:.1f}%",'TRAILING 4-WEEK MEAN',BLUE)]:
 box=FancyBboxPatch((x,.626),.217,.17,boxstyle='round,pad=.009,rounding_size=.014',facecolor=PANEL,edgecolor=EDGE,transform=fig.transFigure,linewidth=1.3)
 fig.add_artist(box)
 fig.text(x+.014,.752,lab,fontsize=10,fontweight='bold',color=MUTED)
 fig.text(x+.014,.677,val,fontsize=26,fontweight='bold',color=col)
 fig.text(x+.014,.645,sub,fontsize=9,color=MUTED)
ax=fig.add_axes([.081,.203,.846,.386],facecolor=PANEL)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y',alpha=.18,color=WHITE)
ax.set_axisbelow(True)
xx=np.arange(len(test));width=.25
ax.bar(xx-width,test.ActualUnits/1000,width=width,color=WHITE,label='Observed')
ax.bar(xx,test.ForecastUnits/1000,width=width,color=TEAL,label='Selected forecast')
ax.bar(xx+width,test.BaselineUnits/1000,width=width,color=BLUE,alpha=.75,label='Simple baseline')
ax.set_xticks(xx,[pd.Timestamp(t).strftime('%-d %b') for t in test.WeekStart],fontsize=12)
ax.set_ylabel('Thousand observed units / week',fontsize=11)
ax.legend(frameon=False,loc='upper left',ncol=3,labelcolor=MUTED,bbox_to_anchor=(.01,1.01))
ax.set_ylim(0,max(test.ActualUnits.max(),test.ForecastUnits.max(),test.BaselineUnits.max())/1000*1.16)
for i,row in enumerate(test.itertuples()):
 ax.text(i-width,row.ActualUnits/1000+2.3,f'{row.ActualUnits/1000:.0f}k',ha='center',color=WHITE,fontsize=10,fontweight='bold')
fig.text(.064,.105,'THE FINDING',fontsize=10,color=PEACH,fontweight='bold')
comparison=('The selected method reduced error slightly, but still underpredicted late-autumn sales.' if all_products.HoldoutWAPE < all_products.BaselineHoldoutWAPE else 'The selected method did not beat the simple baseline on the untouched final test.')
fig.text(.064,.067,comparison,fontsize=14,fontweight='bold',color=WHITE)
fig.text(.065,.029,'Experimental backtest · positive recorded sales are NOT true unconstrained demand · one historical year · no stockout/promo variables',fontsize=10,color=MUTED)
fig.savefig(OUT/'07_demand_forecast_backtest.png',dpi=145,facecolor=fig.get_facecolor(),bbox_inches='tight',pad_inches=.3);plt.close(fig)
# Evaluation image: no favorable cherry-picking of SKUs.
sku=eval_df.query('Series != "All products"').iloc[::-1]
fig=plt.figure(figsize=(12.2,6.6),dpi=145,facecolor=BG)
fig.text(.07,.924,'SKU CHECK / OBSERVED UNIT SALES',fontsize=11,fontweight='bold',color=TEAL)
fig.text(.07,.855,'A different result at product level',fontsize=25,fontweight='bold',color=WHITE)
fig.text(.07,.804,'Final Nov–Dec 2011 holdout · lower WAPE means less absolute error',fontsize=12,color=MUTED)
ax=fig.add_axes([.33,.19,.59,.52],facecolor=BG)
y=np.arange(len(sku));h=.3
ax.barh(y-h/2,sku.HoldoutWAPE,height=h,color=TEAL,label='Selected model')
ax.barh(y+h/2,sku.BaselineHoldoutWAPE,height=h,color=BLUE,alpha=.7,label='4-week mean')
ax.set_yticks(y,sku.Series)
ax.set_xlim(0,36)
ax.set_xlabel('Holdout WAPE (%)',fontsize=11)
ax.xaxis.grid(True,color=WHITE,alpha=.1);ax.set_axisbelow(True)
ax.spines[['top','right','left']].set_visible(False)
ax.legend(frameon=False,loc='upper right',labelcolor=MUTED)
for k,row in enumerate(sku.itertuples()):
 ax.text(max(row.HoldoutWAPE,row.BaselineHoldoutWAPE)+.7,k,f'{row.HoldoutWAPE:.1f}%',va='center',color=WHITE,fontsize=11)
fig.text(.07,.104,'Most products selected the simple mean. A modest aggregate improvement does not imply every SKU improved.',fontsize=11,color=WHITE)
fig.text(.07,.054,'Five popular SKUs preselected from the first 25 weeks; no hindsight use of November demand in choosing the SKUs.',fontsize=10,color=MUTED)
fig.savefig(OUT/'08_sku_forecast_validation.png',dpi=145,facecolor=fig.get_facecolor(),bbox_inches='tight',pad_inches=.2);plt.close(fig)
print('Saved forecast charts')
