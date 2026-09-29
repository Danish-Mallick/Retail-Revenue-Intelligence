"""Editorial README artwork and Seaborn plots, reproduced from verified result CSVs.

No generative-image assets. The cover and all plots are drawn with Python.
Run after scripts/analyze.py and scripts/ml_forecast_comparison.py to refresh results.
"""
from pathlib import Path
import json
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.ticker as ticker
import seaborn as sns
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results'
O = ROOT / 'charts'
O.mkdir(exist_ok=True)
METRICS = json.loads((R / 'verified_metrics.json').read_text())
MON = pd.read_csv(R / 'monthly.csv')
MON = MON[(MON.Month >= '2011-01') & (MON.Month <= '2011-11') & MON.CompleteMonth].copy()
MON['MonthLabel'] = pd.to_datetime(MON.Month).dt.strftime('%b')
assert len(MON) == 11
SEP, NOV = MON[MON.Month=='2011-09'].iloc[0], MON[MON.Month=='2011-11'].iloc[0]
SALES_GROWTH = (NOV.Revenue/SEP.Revenue - 1)*100
ORDER_GROWTH = (NOV.Orders/SEP.Orders - 1)*100
AOV_GROWTH = (NOV.AOV/SEP.AOV - 1)*100
assert abs(SALES_GROWTH-34.05)<.2 and abs(ORDER_GROWTH-52.97)<.2

# Portfolio-specific visual identity: paper, ink, rust, and olive. No dark neon cards.
PAPER = '#FBF8F2'; WHITE = '#FFFFFF'; INK = '#1E2929'; MUTED = '#5C6763'
RUST = '#C65B3B'; RUST_PALE = '#F8E5DD'; OLIVE = '#51715C'; OLIVE_PALE = '#E4EAE1'
GRID = '#D8DAD4'; BLUE = '#496B7E'; LIGHT = '#ECE9E1'
sns.set_theme(style='whitegrid', context='notebook', font='DejaVu Sans', rc={
    'figure.facecolor': PAPER, 'axes.facecolor': PAPER, 'axes.edgecolor': GRID,
    'grid.color': GRID, 'grid.linewidth': .7, 'axes.labelcolor': MUTED,
    'xtick.color': MUTED, 'ytick.color': MUTED, 'text.color': INK,
    'axes.titleweight': 'bold', 'axes.spines.top': False, 'axes.spines.right': False,
})
plt.rcParams.update({'font.family':'DejaVu Sans', 'savefig.facecolor':PAPER})

def save(fig, name):
    fig.savefig(O/name, dpi=146, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=.19)
    plt.close(fig)
    print(name, (O/name).stat().st_size)

# COVER: human-designed editorial composition, with one real Seaborn plot.
fig = plt.figure(figsize=(15.2, 5.25), facecolor=PAPER)
fig.text(.048,.875, 'RETAIL SIGNALS  /  AN ANALYTICAL CASE STUDY', fontsize=12,
         color=RUST, weight='bold', family='DejaVu Sans')
fig.add_artist(plt.Line2D([.048,.952],[.832,.832],transform=fig.transFigure,color=GRID,linewidth=1))
fig.text(.048,.700, 'More orders.',fontsize=42,family='DejaVu Serif',color=INK,weight='bold')
fig.text(.048,.548, 'Smaller baskets.',fontsize=42,family='DejaVu Serif',color=RUST,weight='bold')
fig.text(.048,.434, 'Why did sales increase in autumn 2011?',fontsize=17.2,color=INK)
fig.text(.049,.326, 'I started with an increase in revenue, then checked what changed\n'
                  'in the invoices, customers and the subsequent forecasts.',
         fontsize=12.9, color=MUTED, linespacing=1.7)
fig.text(.048,.135, f'{SALES_GROWTH:+.1f}% sales', color=INK, fontsize=19, weight='bold')
fig.text(.241,.135, f'{ORDER_GROWTH:+.1f}% invoices', color=INK, fontsize=19, weight='bold')
fig.text(.049,.077, 'September to November 2011 · Complete months · Historical extract',
         color=MUTED,fontsize=10.7)
# Single analytical chart at right, intentionally much less busy than old dashboards.
ax = fig.add_axes([.64,.245,.314,.45]); ax.set_facecolor(PAPER)
sns.lineplot(data=MON, x=np.arange(len(MON)), y=MON.Revenue/1000, ax=ax,
             color=OLIVE, linewidth=2.8, marker='o',markersize=5)
ax.set_title('Monthly recorded sales',fontsize=13.5,pad=16,loc='left',color=INK,weight='bold')
ax.set_xticks([0,2,4,6,8,10],['Jan','Mar','May','Jul','Sep','Nov'])
ax.set_ylim(0,1000); ax.set_yticks([0,500,1000],['£0k','£500k','£1m'])
ax.set_xlabel('');ax.set_ylabel('');ax.grid(axis='y',color=GRID);ax.grid(axis='x',visible=False)
ax.spines[['left','bottom']].set_visible(False);ax.tick_params(length=0,labelsize=10)
ax.scatter([8,10],[SEP.Revenue/1000,NOV.Revenue/1000],s=62,color=RUST,zorder=9)
ax.annotate('Sep  £657k',xy=(8,SEP.Revenue/1000),xytext=(5.95,760),fontsize=10.1,
            color=INK,arrowprops={'arrowstyle':'-','color':RUST,'lw':.8})
ax.annotate('Nov  £881k',xy=(10,NOV.Revenue/1000),xytext=(7.5,990),fontsize=10.1,
            color=INK,arrowprops={'arrowstyle':'-','color':RUST,'lw':.8})
fig.add_artist(plt.Line2D([.616,.616],[.2,.75],transform=fig.transFigure,color=GRID,linewidth=1))
fig.text(.953,.101,'SQL   ·   PYTHON   ·   FORECASTING   ·   POWER BI',ha='right',fontsize=10.4,color=OLIVE,weight='bold')
save(fig,'Retail_Signals_Editorial_Cover.png')

# FIG 1: monthly orders and average order value, not two incomparable units on one y axis.
fig,axs=plt.subplots(1,2,figsize=(13.2,4.7),gridspec_kw={'wspace':.27})
fig.suptitle('Did revenue grow because customers placed more orders or spent more per order?',
             x=.06,y=1.055,ha='left',fontsize=14.4,weight='bold',color=INK)
for ax, metric, label, color, unit in [
    (axs[0],'Orders','Monthly invoice count',OLIVE,'invoices'),
    (axs[1],'AOV','Average value per invoice',RUST,'GBP*')]:
    sns.lineplot(data=MON, x='MonthLabel',y=metric,ax=ax, color=color,marker='o',linewidth=2.6,markersize=6)
    ax.set_title(label,loc='left',fontsize=12.9,pad=15,color=INK)
    ax.set_xlabel('');ax.set_ylabel(unit);ax.grid(axis='y');ax.grid(axis='x',visible=False)
    ax.spines[['left','bottom']].set_visible(False)
    ax.tick_params(axis='x',labelsize=9)
    ax.set_ylim(0,MON[metric].max()*1.21)
    x9=8;x11=10
    ax.scatter([x9,x11],[float(SEP[metric]),float(NOV[metric])],s=61,zorder=7,color=RUST)
    for n,obs in [(8,SEP),(10,NOV)]:
        txt=(f'{int(obs[metric]):,}' if metric=='Orders' else f'£{float(obs[metric]):,.0f}')
        ax.annotate(txt,(n,float(obs[metric])),xytext=(-8,12),textcoords='offset points',
                    fontsize=9.5,weight='bold',ha='right',color=INK)
fig.text(.062,-.055,
    f'From September to November, invoice count rose {ORDER_GROWTH:.1f}%, while average order value fell {abs(AOV_GROWTH):.1f}%.',
    fontsize=11.4,color=MUTED)
save(fig,'12_invoices_vs_order_value_seaborn.png')

# FIG 2: first-observed customer segments: customer share vs sales share (same denominator per measure).
segments=pd.read_csv(R/'segments.csv')
segments['CustomerSharePct']=100*segments.Customers/segments.Customers.sum()
select=['Champions','Developing','Recent buyers','Loyal active','Dormant (rule-based)','At risk (rule-based)']
segments['Segment']=pd.Categorical(segments.Segment,categories=select,ordered=True)
long=segments.melt(id_vars='Segment',value_vars=['CustomerSharePct','RevenueSharePct'],
                   var_name='Measure',value_name='Share (%)')
long['Measure']=long['Measure'].map({'CustomerSharePct':'Share of customers','RevenueSharePct':'Share of recorded sales'})
fig,ax=plt.subplots(figsize=(11.8,5.0))
sns.barplot(data=long,x='Share (%)',y='Segment',hue='Measure',orient='h',ax=ax,
            order=select,palette={'Share of customers':OLIVE,'Share of recorded sales':RUST})
ax.set_title('Do the customer groups that generate sales represent most customers?',loc='left',pad=19,fontsize=13.3,color=INK)
ax.set_xlabel('Percentage of identified customers / recorded sales');ax.set_ylabel('')
ax.grid(axis='x');ax.grid(axis='y',visible=False);ax.set_axisbelow(True)
ax.spines[['left','bottom']].set_visible(False);ax.legend(loc='lower center',bbox_to_anchor=(.48,-.20),ncol=2,frameon=False,fontsize=9.2)
ax.set_xlim(0,66)
for rect in ax.patches:
    if rect.get_width()>0:
        ax.text(rect.get_width()+.5,rect.get_y()+rect.get_height()/2,
                f'{rect.get_width():.1f}%',va='center',fontsize=8.7,color=INK)
champ=segments[segments.Segment=='Champions'].iloc[0]
fig.text(.11,-.092,f"'Champions' are {champ.CustomerSharePct:.1f}% of identified customers, but contribute {champ.RevenueSharePct:.1f}% of recorded sales.",
         fontsize=10.9,color=MUTED)
save(fig,'13_customer_concentration_seaborn.png')

# FIG 3: a quick-to-read month-one cohort plot showing retention with group sizes.
co=pd.read_csv(R/'cohort_retention.csv')
co=co[(co.CohortIndex==1)&(co.FirstObservedMonth<='2011-10')].copy()
co['Month']=pd.to_datetime(co.FirstObservedMonth).dt.strftime('%b %Y')
fig,ax=plt.subplots(figsize=(11.6,4.5))
sns.barplot(data=co,x='Month',y='RetentionPct',color=OLIVE,ax=ax,width=.7)
ax.set_title('Did customers buy again in the month after we first observed them?',loc='left',pad=20,color=INK,fontsize=14)
ax.set_ylim(0,max(46,co.RetentionPct.max()+8));ax.set_xlabel('Month first seen in this extract')
ax.set_ylabel('Purchased again the next month (%)');ax.grid(axis='y');ax.grid(axis='x',visible=False)
ax.set_axisbelow(True);ax.spines[['left','bottom']].set_visible(False)
ax.tick_params(axis='x',rotation=32,labelsize=9)
for i,r in co.reset_index(drop=True).iterrows():
    ax.text(i,float(r.RetentionPct)+.9,f'{r.RetentionPct:.0f}%',ha='center',fontsize=9,weight='bold',color=INK)
fig.subplots_adjust(bottom=.31)
fig.text(.11,.04,'A first-observed purchase may not be a first-ever purchase. November-to-December cohorts are excluded because December is partial.',
         color=MUTED,fontsize=9.4)
save(fig,'14_next_month_return_seaborn.png')

# FIG 4: non-UK composition; removing the dominant UK makes the otherwise-hidden markets legible.
country=pd.read_csv(R/'country.csv');non=country[country.Country!='United Kingdom'].copy()
non['NonUKSharePct']=non.Revenue/non.Revenue.sum()*100
non=non.sort_values('NonUKSharePct',ascending=False).head(7)
fig,ax=plt.subplots(figsize=(10.8,4.5))
sns.barplot(data=non,x='NonUKSharePct',y='Country',color=BLUE,ax=ax)
ax.set_title('Which countries contribute the most sales outside the United Kingdom?',loc='left',pad=18,color=INK,fontsize=13.3)
ax.set_xlabel('Share of recorded sales outside the UK (%)');ax.set_ylabel('');ax.grid(axis='x');ax.grid(axis='y',visible=False)
ax.set_xlim(0, max(non.NonUKSharePct)*1.3);ax.set_axisbelow(True);ax.spines[['left','bottom']].set_visible(False)
for i,share in enumerate(non.NonUKSharePct):
    ax.text(share+.4,i,f'{share:.1f}%',va='center',color=INK,fontsize=10)
fig.text(.11,-.055,'The United Kingdom contributes 84.4% of total recorded sales. This comparison considers only the remaining 15.6%.',
         fontsize=10.8,color=MUTED)
save(fig,'15_non_uk_market_mix_seaborn.png')

# FIG 5: validation versus final out-of-time test, not an in-sample training score.
ml=pd.read_csv(R/'ml_holdout_comparison.csv')
ml=ml[ml.Series=='All products'].copy()
names={'four_week_mean':'Four-week mean','four_week_repeat':'Four-week repeat',
       'eight_week_damped_trend':'Damped trend','random_forest':'Random Forest','xgboost':'XGBoost'}
ml['Model']=ml.Method.map(names)
fig,ax=plt.subplots(figsize=(10.4,5.1))
sns.scatterplot(data=ml,x='ValidationWAPE',y='HoldoutWAPE',hue='Model',
                palette={'Four-week mean':BLUE,'Four-week repeat':'#8A9BA2',
                         'Damped trend':OLIVE,'Random Forest':RUST,'XGBoost':'#C5A362'},
                s=170,ax=ax,edgecolor=PAPER,linewidth=1.3,legend=False)
for row in ml.itertuples(index=False):
    offs={ 'Damped trend':(-8,-17),'Random Forest':(-49,8),
           'XGBoost':(-13,13),'Four-week mean':(9,8),'Four-week repeat':(8,9)}
    dx,dy=offs[row.Model];ax.annotate(row.Model,(row.ValidationWAPE,row.HoldoutWAPE),
                  xytext=(dx,dy),textcoords='offset points',fontsize=9.5,color=INK,
                  weight='bold' if row.Model in ['Damped trend','Random Forest'] else 'normal')
ax.set_title('Did the model selected during validation deliver the smallest test error?',loc='left',pad=20,color=INK,fontsize=13.0)
ax.set_xlabel('Error during earlier validation periods (WAPE, %)');ax.set_ylabel('Error on the November holdout (WAPE, %)')
ax.set_xlim(18.5,23.2);ax.set_ylim(12.5,20.2)
ax.grid(True);ax.spines[['left','bottom']].set_visible(False)
fig.text(.12,-.03,'Random Forest: lowest validation error (19.1%). Damped trend: lowest final-test error (13.4%). Lower is better on both axes.',
         fontsize=10.8,color=MUTED)
save(fig,'16_forecast_validation_vs_test_seaborn.png')

print('All values read from project result files; cover and charts were generated with Python / Seaborn.')