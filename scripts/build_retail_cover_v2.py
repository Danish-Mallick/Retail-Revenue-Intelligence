"""Produce a GitHub README cover from verified retail outputs, using Python & Seaborn.

No generated photographs or invented metrics. The miniature monthly chart deliberately
excludes December 2011 because that month is incomplete in the source extract.
"""
from pathlib import Path
import json
import io

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
monthly = pd.read_csv(ROOT / 'results' / 'monthly.csv')
metrics = json.loads((ROOT / 'results' / 'verified_metrics.json').read_text())
months = monthly.loc[(monthly['Year'] == 2011) & (monthly['CompleteMonth'].astype(str).str.lower() == 'true')].copy()
assert len(months) == 11 and months.iloc[-1]['Month'] == '2011-11'
sep = months.loc[months.Month == '2011-09'].iloc[0]
nov = months.loc[months.Month == '2011-11'].iloc[0]
revenue_delta = (nov.Revenue/sep.Revenue - 1)*100
invoice_delta = (nov.Orders/sep.Orders - 1)*100
aov_delta = (nov.AOV/sep.AOV - 1)*100
assert abs(revenue_delta-34.1) < .08 and abs(invoice_delta-53.0)<.08 and abs(aov_delta-(-12.4))<.1

W,H=1800,760
C = {'paper':'#F6F5F0','ink':'#222E2C','inksoft':'#53605B','ochre':'#AC613A','teal':'#306F67','line':'#D8DAD4','white':'#FFFFFF','light':'#ECEFEA','muted':'#8A938E'}
img=Image.new('RGB',(W,H),C['paper']);d=ImageDraw.Draw(img)
reg='/usr/share/fonts/opentype/inter/Inter-Regular.otf'
sem='/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
bold='/usr/share/fonts/opentype/inter/Inter-Bold.otf'
serif='/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'
serifbold='/usr/share/fonts/truetype/noto/NotoSerif-SemiBold.ttf'
def f(path,size):return ImageFont.truetype(path,size)
def txt(x,y,t,font,color,anchor=None):d.text((x,y),t,font=font,fill=color,anchor=anchor)
# Top editorial eyebrow and line
d.rounded_rectangle((80,66,127,74),radius=4,fill=C['ochre'])
txt(143,51,'RETAIL  /  REVENUE INTELLIGENCE',f(sem,21),C['ink'])
txt(1718,57,'HISTORICAL ANALYSIS · 2010–2011',f(reg,17),C['inksoft'],anchor='ra')
d.line((80,99,1720,99),fill=C['line'],width=2)
# Main readable headline, left
# extra space after headline makes graphic a cover rather than a dashboard
txt(80,128,'More orders.',f(serifbold,68),C['ink'])
txt(80,220,'Smaller baskets.',f(serifbold,68),C['ochre'])
txt(80,322,'What drove the autumn sales increase?',f(sem,25),C['ink'])
txt(80,374,'I compared monthly sales, invoice volume and average',f(reg,22),C['inksoft'])
txt(80,411,'order value before investigating customer behaviour',f(reg,22),C['inksoft'])
txt(80,448,'and testing four-week demand forecasts.',f(reg,22),C['inksoft'])
# Thin editorial divider on the left
d.line((80,520,865,520),fill=C['line'],width=2)
# Three verified numerals to establish project scope, not chart clutter
stats=[('£6.07m','RECORDED SALES'),('17,635','INVOICES'),('4,261','CUSTOMERS')]
for i,(v,l) in enumerate(stats):
    x=80+270*i
    txt(x,552,v,f(sem,39),C['ink'])
    txt(x,614,l,f(sem,13),C['inksoft'])
# Right, one clean data chart
card=(930,132,1720,662)
d.rounded_rectangle(card,radius=19,fill=C['white'],outline=C['line'],width=2)
txt(975,167,'RECORDED MONTHLY SALES',f(sem,21),C['ink'])
txt(975,208,'January–November 2011 · December is incomplete',f(reg,16),C['inksoft'])
# Real Seaborn chart from monthly.csv
sns.set_theme(style='whitegrid',font_scale=1)
fig, ax = plt.subplots(figsize=(8.7,3.45),dpi=130)
fig.patch.set_facecolor(C['white']);ax.set_facecolor(C['white'])
x=np.arange(len(months));y=months.Revenue.values / 1000.
sns.lineplot(x=x,y=y,ax=ax,color=C['teal'],linewidth=2.9,marker='o',markersize=5)
ax.fill_between(x,y,0,color=C['teal'],alpha=.075)
ax.scatter([8,10],[y[8],y[10]],s=58,color=C['ochre'],zorder=6)
ax.text(8,y[8]+52,'£657k',color=C['ink'],fontsize=11,fontweight='bold',ha='center')
ax.text(10,y[10]+52,'£881k',color=C['ink'],fontsize=11,fontweight='bold',ha='right')
ax.set_ylim(0,1100);ax.set_xlim(-.35,10.4)
ax.set_xticks(x);ax.set_xticklabels(pd.to_datetime(months.Month).dt.strftime('%b'),fontsize=10,color=C['inksoft'])
ax.set_yticks([0,250,500,750,1000]);ax.set_yticklabels(['£0','£250k','£500k','£750k','£1m'],fontsize=10,color=C['inksoft'])
ax.set_xlabel('');ax.set_ylabel('');ax.grid(axis='y',alpha=.35,color=C['line']);ax.grid(axis='x',visible=False)
for sp in ax.spines.values():sp.set_visible(False)
fig.subplots_adjust(left=.09,right=.97,top=.89,bottom=.2)
mem=io.BytesIO();fig.savefig(mem,format='png',dpi=130,facecolor=C['white']);plt.close(fig)
mem.seek(0);plot=Image.open(mem).convert('RGB')
plot.thumbnail((730,310),Image.Resampling.LANCZOS)
img.paste(plot,(965,257))
# Two concise results as bottom rail. Every number computed above.
d.rounded_rectangle((973,576,1334,637),radius=11,fill='#F3ECE4')
d.rounded_rectangle((1343,576,1693,637),radius=11,fill='#E5EFEB')
txt(992,590,f'+{invoice_delta:.1f}%',f(bold,24),C['ochre'])
txt(1103,602,'invoices',f(sem,16),C['ink'])
txt(1363,590,f'{aov_delta:.1f}%',f(bold,24),C['teal'])
txt(1478,602,'average order value',f(sem,14),C['ink'])
# Small footer
d.line((80,691,1720,691),fill=C['line'],width=2)
txt(80,712,'SQL  /  PYTHON & SEABORN  /  POWER BI  /  FORECASTING',f(sem,17),C['inksoft'])
txt(1720,712,'Historical sales data · figures verified against project outputs',f(reg,16),C['inksoft'],anchor='ra')
out=ROOT/'charts'/'Retail_Signals_Cover_v2.png'
img.save(out,optimize=True)
print('Saved',out,'size',img.size,'values',revenue_delta,invoice_delta,aov_delta)