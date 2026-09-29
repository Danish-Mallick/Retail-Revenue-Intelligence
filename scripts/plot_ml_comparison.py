"""Rebuild the three visual summaries from the aggregate, reproducible ML outputs."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results';CH=ROOT/'charts';CH.mkdir(exist_ok=True)
P={'bg':'#101A2D','panel':'#1C2B42','fg':'#F1F7FC','muted':'#A8BBCD','grid':'#385068','teal':'#70E6D0','peach':'#FFB187','purple':'#A7A8F8','pink':'#F38AA5','gray':'#879AAE'}
plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':P['bg'],'axes.facecolor':P['panel'], 'axes.edgecolor':P['grid'], 'axes.labelcolor':P['muted'],'text.color':P['fg'], 'xtick.color':P['muted'],'ytick.color':P['muted'],'font.size':11,'savefig.facecolor':P['bg']})
COL={'four_week_mean':P['gray'],'four_week_repeat':'#C2A2CB','eight_week_damped_trend':P['peach'],'random_forest':P['teal'],'xgboost':P['pink']}
LABEL={'four_week_mean':'4-week mean','four_week_repeat':'4-week repeat','eight_week_damped_trend':'8-week damped trend','random_forest':'Random Forest','xgboost':'XGBoost'}

def finish(fig,path):
 fig.savefig(CH/path,dpi=170,bbox_inches='tight',pad_inches=.24)
 plt.close(fig);print('Chart:',CH/path)

hold=pd.read_csv(D/'ml_holdout_weeks.csv');cmp=pd.read_csv(D/'ml_holdout_comparison.csv');sel=pd.read_csv(D/'ml_selected_methods.csv')
agg=hold.loc[hold.Series=='All products'].copy();scores=cmp.loc[cmp.Series=='All products'].set_index('Method')
order=['four_week_mean','eight_week_damped_trend','random_forest','xgboost']
fig=plt.figure(figsize=(15.2,8.3));fig.patch.set_facecolor(P['bg'])
fig.text(.053,.948,'RETAIL SIGNALS    /    MODEL EXPERIMENT',size=11,weight='bold',color=P['teal'])
fig.text(.053,.885,'Can ML anticipate the late-autumn surge?',size=26,weight='bold')
fig.text(.053,.838,'Weekly observed units versus four candidate forecasts on the untouched November test.',size=12,color=P['muted'])
ax=fig.add_axes([.075,.27,.85,.43]);ax.set_facecolor(P['panel']);ax.grid(axis='y',color=P['grid'],alpha=.58);ax.set_axisbelow(True)
actual=agg.loc[agg.Method=='four_week_mean'].sort_values('WeekStart');weeks=pd.to_datetime(actual.WeekStart)
ax.plot(weeks,actual.ActualUnits/1000,color=P['fg'],lw=3.4,marker='o',markersize=11,label='Observed units',zorder=12)
for model in order:
 rows=agg.loc[agg.Method==model].sort_values('WeekStart')
 ax.plot(weeks,rows.ForecastUnits/1000,lw=2.4,marker='o',markersize=6,color=COL[model],label=f'{LABEL[model]}  ({scores.loc[model,"HoldoutWAPE"]:.1f}% test WAPE)')
ax.set_ylabel('Units sold / thousands',labelpad=10)
ax.set_xlim(weeks.iloc[0]-pd.Timedelta(days=1),weeks.iloc[-1]+pd.Timedelta(days=1))
ax.set_xticks(weeks);ax.set_xticklabels([d.strftime('%d %b') for d in weeks])
ax.spines[['top','right']].set_visible(False)
handles, labels = ax.get_legend_handles_labels()
fig.legend(handles,labels,ncol=2,loc='upper left',bbox_to_anchor=(.073,.80),fontsize=10,frameon=False,labelcolor=P['fg'])
fig.text(.054,.205,'SELECTED BY EARLIER VALIDATION',size=11,color=P['teal'],weight='bold')
fig.text(.054,.151,'Random Forest  ·  19.1% validation WAPE',size=17,weight='bold')
fig.text(.054,.090,'Its test WAPE was 15.7%; the damped trend scored 13.4% on the test.',size=11,color=P['muted'])
fig.text(.054,.042,'Result: adding ML did not establish a better out-of-sample aggregate forecast on this historical test.',size=10,color=P['muted'])
finish(fig,'09_ml_forecast_comparison.png')

fig=plt.figure(figsize=(14,8.2));fig.patch.set_facecolor(P['bg'])
fig.text(.06,.941,'MODEL VALIDATION  ≠  FINAL TEST',size=11,weight='bold',color=P['teal'])
fig.text(.06,.886,'Why the validation winner was not the test winner',size=22,weight='bold')
fig.text(.06,.838,'Same five historical validation windows for each method; no method selected using the final test.',color=P['muted'],size=11)
ax=fig.add_axes([.12,.29,.8,.46]);ax.set_facecolor(P['panel']);ax.grid(axis='y',color=P['grid'],alpha=.55);ax.set_axisbelow(True)
order2=['four_week_mean','four_week_repeat','eight_week_damped_trend','random_forest','xgboost']
x=np.arange(len(order2));w=.33
ax.bar(x-w/2,[scores.loc[m,'ValidationWAPE'] for m in order2],width=w,color=P['purple'],label='Rolling validation WAPE')
ax.bar(x+w/2,[scores.loc[m,'HoldoutWAPE'] for m in order2],width=w,color=[COL[m] for m in order2],label='Final holdout WAPE')
ax.set_xticks(x);ax.set_xticklabels(['4wk mean','4wk repeat','Damped trend','Random Forest','XGBoost'])
ax.set_ylabel('WAPE / lower is better');ax.set_ylim(0,27);ax.spines[['top','right']].set_visible(False)
ax.legend(ncol=2,frameon=False,loc='upper right',labelcolor=P['fg'])
for xx,model in zip(x,order2):
 va=scores.loc[model,'ValidationWAPE'];te=scores.loc[model,'HoldoutWAPE']
 ax.text(xx-w/2,va+.45,f'{va:.1f}',color=P['fg'],ha='center',size=9)
 ax.text(xx+w/2,te+.45,f'{te:.1f}',color=P['fg'],ha='center',size=9)
fig.text(.06,.168,'DECISION',size=11,color=P['teal'],weight='bold')
fig.text(.06,.116,'RF was selected on validation, but damped trend had lower error on the untouched test.',size=15,weight='bold')
fig.text(.06,.060,'One year of sales and one final test are not enough to claim a robust winning forecasting algorithm.',size=10,color=P['muted'])
finish(fig,'10_ml_validation_vs_test.png')

fig=plt.figure(figsize=(14,8.1));fig.patch.set_facecolor(P['bg'])
fig.text(.06,.946,'PRODUCT-LEVEL  /  OUT-OF-TIME TEST',size=11,weight='bold',color=P['teal'])
fig.text(.06,.882,'Does the same model help every product?',size=23,weight='bold')
fig.text(.06,.832,'Validation selected a method independently for each of five products. These are their test errors.',size=11,color=P['muted'])
ax=fig.add_axes([.41,.26,.50,.51]);ax.set_facecolor(P['panel']);ax.grid(axis='x',alpha=.65,color=P['grid']);ax.set_axisbelow(True)
small=cmp.loc[cmp.Series!='All products'];sku_order=sel.loc[sel.Series!='All products','Series'].tolist()[::-1]
short={'85123A':'Heart T-light holder','22423':'3-tier cake stand','47566':'Party bunting','84879':'Bird ornament','85099B':'Red retrospot bag'}
for j,k in enumerate(sku_order):
 a=small.loc[(small.Series==k)&(small.Method=='four_week_mean')].iloc[0]
 b=small.loc[(small.Series==k)&(small.SelectedByValidation)].iloc[0]
 ax.plot([a.HoldoutWAPE,b.HoldoutWAPE],[j,j],color=P['grid'],lw=4,zorder=1)
 ax.scatter([a.HoldoutWAPE],[j],s=170,color=P['gray'],zorder=3)
 ax.scatter([b.HoldoutWAPE],[j],s=170,color=P['teal'],zorder=4)
 ax.text(-.04,j,short[k],transform=ax.get_yaxis_transform(),ha='right',va='center',color=P['fg'],size=11)
 ax.text(max(b.HoldoutWAPE,a.HoldoutWAPE)+1.0,j,f'{LABEL[b.Method]}',ha='left',va='center',color=P['teal'],size=9)
ax.set_yticks([]);ax.set_xlim(0,51);ax.set_ylim(-.65,len(sku_order)-.3)
ax.set_xlabel('Holdout WAPE (%)  —  lower is better')
ax.spines[['top','right','left']].set_visible(False)
fig.text(.055,.13,'● Simple 4-week mean',color=P['gray'],size=12)
fig.text(.055,.086,'● Method chosen on validation',color=P['teal'],size=12)
fig.text(.055,.041,'A selected model may still do worse on the untouched holdout. SKU demand is noisy and intermittent.',color=P['muted'],size=10)
finish(fig,'11_ml_product_holdout.png')
