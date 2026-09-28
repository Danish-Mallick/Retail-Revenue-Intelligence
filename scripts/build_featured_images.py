"""Two precise, data-verified, recruiter-facing graphics, NOT Power BI screenshots."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';OUT=ROOT/'charts';M=json.loads((R/'verified_metrics.json').read_text());W,H=1920,1080
mon=pd.read_csv(R/'monthly.csv'); seg=pd.read_csv(R/'segments.csv'); cohorts=pd.read_csv(R/'cohort_retention.csv')
C={'bg':(10,17,31),'pan':(23,34,53),'pan2':(27,39,61),'edge':(56,71,96), 'white':(249,250,250),'muted':(172,190,206),'dim':(117,140,162),'teal':(95,225,206),'peach':(255,178,144),'blue':(152,172,249),'faint':(56,72,95),'pink':(241,125,156)}
F='/usr/share/fonts/opentype/inter/InterDisplay-'
def font(size,weight='Regular'):
 p=Path(F+weight+'.otf');fb='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if weight in ('Bold','ExtraBold','SemiBold') else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 return ImageFont.truetype(str(p) if p.exists() else fb,size)
def base():
 y,x=np.mgrid[0:H,0:W];b=np.zeros((H,W,3),dtype=np.float32)
 for i,n in enumerate(C['bg']):b[:,:,i]=n
 z=np.exp(-(((x-1530)/1350)**2+((y+80)/730)**2)*3.5)
 b+=z[:,:,None]*np.array([6,11,33],dtype=np.float32)
 return Image.fromarray(np.uint8(np.clip(b,0,255)),'RGB')
def draw_base(img,section,title1,title2,dek,window='DEC 2010 – DEC 2011'):
 d=ImageDraw.Draw(img)
 def txt(x,y,t,n=20,w='Regular',c='white',maxw=None):
  f=font(n,w)
  if maxw:
   while d.textbbox((0,0),t,font=f)[2]>maxw and n>10:n-=1;f=font(n,w)
  d.text((x,y),t,font=f,fill=C.get(c,c))
 def rr(xy,fill='pan',outline='edge',radius=16,width=2):d.rounded_rectangle(xy,radius=radius,fill=C.get(fill,fill),outline=C.get(outline,outline) if outline else None,width=width)
 rr((50,33,108,91),fill='teal',outline=None,radius=13);txt(68,42,'R',35,'ExtraBold','bg')
 txt(124,36,'RETAIL  /  INTELLIGENCE',25,'ExtraBold')
 txt(126,69,'BUSINESS ANALYTICS FIELD NOTES',14,'Medium','dim')
 rr((1480,40,1866,85),fill=(36,47,66),outline=(70,85,110),radius=23)
 txt(1500,51,'HISTORICAL  ·  FILTERED EXTRACT',15,'SemiBold','peach',340)
 d.line((55,114,1866,114),fill=C['edge'],width=2)
 txt(58,142,section,17,'Bold','teal')
 txt(56,186,title1,56,'ExtraBold',maxw=1290)
 txt(56,246,title2,61,'ExtraBold','peach',maxw=1290)
 txt(59,328,dek,20,'Medium','muted',maxw=1360)
 rr((1504,187,1866,286),fill='pan2',radius=16)
 txt(1530,201,'OBSERVATION WINDOW',16,'SemiBold','muted')
 txt(1530,233,window,22,'Bold',maxw=312)
 return d,txt,rr

def card(d,txt,rr,x,y,w,label,val,detail,col):
 rr((x,y,x+w,y+166),fill='pan',radius=18)
 d.rounded_rectangle((x+1,y+1,x+124,y+6),radius=3,fill=C[col])
 txt(x+23,y+22,label,16,'SemiBold','muted',w-46)
 txt(x+19,y+59,val,65,'ExtraBold',col,w-40)
 txt(x+23,y+138,detail,13,'Medium','dim',w-46)

def panel(d,txt,rr,box,num,title,subtitle):
 x0,y0,x1,y1=box;rr(box,fill='pan',radius=18)
 rr((x0+23,y0+23,x0+64,y0+60),fill=(56,55,73),outline=None,radius=7)
 txt(x0+33,y0+29,num,18,'Bold','peach')
 txt(x0+78,y0+25,title,26,'Bold',maxw=x1-x0-109)
 txt(x0+24,y0+66,subtitle,16,'Regular','muted',maxw=x1-x0-54)

def foot(d,txt,rr,signal,note):
 rr((53,941,1866,1032),fill=(35,40,57),outline=(91,77,97),radius=15)
 txt(79,951,'THE SIGNAL',16,'Bold','peach')
 txt(78,979,signal,23,'Bold',maxw=1140)
 txt(1300,952,'READ THIS CORRECTLY',15,'Bold','teal')
 txt(1300,981,note[0],15,'Medium','muted',maxw=535)
 txt(1300,1003,note[1],15,'Medium','muted',maxw=535)
 txt(57,1045,'SQL  /  PYTHON  /  POWER BI   •   DATA-VERIFIED DASHBOARD DESIGN PREVIEW',13,'Medium','dim')

# PAGE 1: Revenue / observed demand
img=base();d,t,rr=draw_base(img,'FIELD NOTE 01  /  SALES DECOMPOSITION', 'Sales climbed in autumn.', 'Were baskets getting bigger?', 'I compared orders with average order value before interpreting revenue.')
K=[('RECORDED SALES','£6.07m','FILTERED EXTRACT  /  ASSUMED GBP','white'),('INVOICES','17,635','DEC 2010 – DEC 9, 2011','teal'),('SALES  /  SEP → NOV','+34.1%','TWO COMPLETE 2011 MONTHS','peach'),('ORDER VALUE  /  SEP → NOV','−12.4%','ORDER-VALUE MOVEMENT','blue')]
for i,v in enumerate(K):card(d,t,rr,55+i*458,370,434,*v)
pa=(55,557,1145,920);pb=(1165,557,1866,920)
panel(d,t,rr,pa,'01','The sales curve','Monthly recorded sales, Jan–Nov 2011 · £ thousands*')
start,end=2011,2011
v=mon[mon.Month.between('2011-01','2011-11')].reset_index(drop=True)
x0,y0=120,848;x1=1077;cap=960
for i,tick in enumerate([0,250,500,750,1000]):
 yy=y0-tick/1000*195
 d.line((x0,yy,x1,yy),fill=C['faint'],width=1)
 t(76,yy-9,str(tick),13,'Medium','dim')
coords=[]
for i,row in v.iterrows():
 xx=x0+i*(x1-x0)/10;yy=y0-(row.Revenue/1000)/1000*195;coords.append((round(xx),round(yy)))
for i in range(len(coords)-1):d.line((*coords[i],*coords[i+1]),fill=C['teal'],width=5)
for i,(xx,yy) in enumerate(coords):
 r=8 if i in [8,10] else 5;d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=C['peach'] if i==10 else C['teal'])
 if i in [0,2,4,6,8,10]:t(xx-14,864,['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV'][i],13,'SemiBold','muted')
for i in [8,10]:
 xx,yy=coords[i];val=v.iloc[i].Revenue/1000
 rr((xx-65,yy-51,xx+51,yy-20),fill='pan2',outline=None,radius=8);t(xx-51,yy-46,f'£{val:,.0f}k',17,'Bold','white')
panel(d,t,rr,pb,'02','Breaking down the increase','September vs November · two complete months')
for k,(lab,sept,nov,diff) in enumerate([('NUMBER OF INVOICES',1669,2553,'+53.0%'),('AVERAGE ORDER VALUE',393.89,345.19,'−12.4%')]):
 y=670+k*120;t(1194,y,lab,15,'SemiBold','muted')
 for j,(month,value,col) in enumerate([('SEP',sept,'blue'),('NOV',nov,'teal')]):
  yy=y+40+j*33;t(1194,yy-3,month,15,'Bold','muted');xstart=1264;wid=410;maxval=max(sept,nov)*1.12
  rr((xstart,yy,xstart+wid,yy+18),fill=(45,59,82),outline=None,radius=5)
  d.rounded_rectangle((xstart,yy,xstart+int(wid*value/maxval),yy+18),radius=4,fill=C[col])
  t(1698,yy-3,f'{value:,.0f}' if k==0 else f'£{value:,.0f}',15,'Bold','white')
 t(1194,y+95,f'Change  {diff}',16,'Bold','peach')
foot(d,t,rr,'Orders grew 53.0%; average order value fell 12.4%.',('The upload has repaired dates and no returns.', 'December 2011 is a partial month.'))
img.save(OUT/'LinkedIn_Featured_Sales.png',optimize=True)

# PAGE 2: Repeat customer + cohort
img=base();d,t,rr=draw_base(img,'FIELD NOTE 02  /  CUSTOMER BEHAVIOUR','Repeat buyers matter.', 'But are cohorts returning?', 'A lifetime-in-extract total and a month-by-month cohort tell different stories.')
K=[('OBSERVED CUSTOMERS','4,261','KNOWN-CUSTOMER FILTERED ROWS','white'),('MULTI-ORDER BUYERS','2,773','65.1% OF OBSERVED CUSTOMERS','teal'),('THEIR REVENUE SHARE','92.1%','RETROSPECTIVE GROUPING','peach'),('CHAMPION-SEGMENT SHARE','54.8%','RULE-BASED  /  FULL WINDOW','blue')]
for i,v in enumerate(K):card(d,t,rr,55+i*458,370,434,*v)
pa=(55,557,943,920);pb=(961,557,1866,920)
panel(d,t,rr,pa,'01','Who contributed revenue?','End-of-observation rule-based groups · share of sales')
ss=seg.sort_values('RevenueSharePct',ascending=False);lab_short={'At risk (rule-based)':'At risk','Dormant (rule-based)':'Dormant','Loyal active':'Loyal active','Recent buyers':'Recent','Developing':'Developing','Champions':'Champions'}
for i,(_,r) in enumerate(ss.iterrows()):
 y=675+i*37;t(82,y,lab_short[r.Segment].upper(),15,'SemiBold','muted',150)
 xx=252;ww=520;rr((xx,y,xx+ww,y+16),fill=(45,58,78),outline=None,radius=5)
 d.rounded_rectangle((xx,y,xx+round(ww*r.RevenueSharePct/60),y+16),radius=4,fill=C['teal'] if i==0 else C['blue'])
 t(793,y-3,f'{r.RevenueSharePct:.1f}%',16,'Bold','white')
panel(d,t,rr,pb,'02','Cohorts: next-month activity','First observed month → later monthly purchasing')
choices=['2010-12','2011-01','2011-02','2011-03','2011-04','2011-05','2011-06','2011-07']
for j,v in enumerate(['COHORT','+1 MONTH','+2 MONTHS','+3 MONTHS']):t(991+j*[0,155,165,173][min(j,3)],654,v,14,'SemiBold','muted')
# Reset precise column offsets for headers.
d.rectangle((982,654,1810,672),fill=C['pan']);
for x,s in [(993,'COHORT'),(1168,'+1 MONTH'),(1362,'+2 MONTHS'),(1556,'+3 MONTHS')]:t(x,657,s,14,'SemiBold','muted')
for i,coh in enumerate(choices):
 yy=691+i*26;t(993,yy,coh,15,'SemiBold','muted')
 for j in range(1,4):
  v=cohorts.loc[(cohorts.FirstObservedMonth==coh)&(cohorts.CohortIndex==j),'RetentionPct']
  if len(v):
   val=float(v.iloc[0]);alpha=min(1,max(0,val/45));color=tuple(int((1-alpha)*a+alpha*b) for a,b in zip(C['pan2'],C['teal']))
   rr((1162+(j-1)*190,yy-1,1326+(j-1)*190,yy+22),fill=color,outline=None,radius=5)
   t(1184+(j-1)*190,yy,f'{val:.1f}%',14,'Bold','bg' if val>25 else 'white')
foot(d,t,rr,'92.1% is a retrospective share—not a retention rate.',('Cohorts are first observed within this file.', 'Segment labels are heuristic, not churn predictions.'))
img.save(OUT/'02_Customer_Intelligence_Preview.png',optimize=True)
print('Saved previews: LinkedIn_Featured_Sales.png / 02_Customer_Intelligence_Preview.png')
