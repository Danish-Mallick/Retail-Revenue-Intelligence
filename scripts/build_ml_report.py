"""Generate a standalone local HTML explanation of the ML forecasting comparison."""
from pathlib import Path
import html,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'results'
sumry=json.loads((D/'ml_comparison_summary.json').read_text())
scores=pd.read_csv(D/'ml_holdout_comparison.csv');choices=pd.read_csv(D/'ml_selected_methods.csv')
agg=scores.loc[scores.Series=='All products'].copy()
labels={'four_week_mean':'Four-week moving average','four_week_repeat':'Repeat the last four weeks','eight_week_damped_trend':'Eight-week damped trend','random_forest':'Random Forest','xgboost':'XGBoost'}
agg['Model']=agg.Method.map(labels)
agg['Selected']='Selected on validation'*(len(agg)) if False else agg.SelectedByValidation.map({True:'Selected in advance',False:'–'})
def n(x):return f'{x:,.1f}'
rows='\n'.join(f'<tr><td>{html.escape(r.Model)}</td><td>{n(r.ValidationWAPE)}%</td><td>{n(r.HoldoutWAPE)}%</td><td>{html.escape(r.Selected)}</td></tr>' for r in agg.itertuples())
sku=[]
for r in choices.itertuples():
 if r.Series=='All products':continue
 z=scores.loc[(scores.Series==r.Series)&(scores.SelectedByValidation)].iloc[0]
 b=scores.loc[(scores.Series==r.Series)&(scores.Method=='four_week_mean')].iloc[0]
 sku.append(f'<tr><td>{html.escape(r.Product)}</td><td>{html.escape(labels[r.SelectedByValidation])}</td><td>{n(z.HoldoutWAPE)}%</td><td>{n(b.HoldoutWAPE)}%</td></tr>')
sku_rows='\n'.join(sku)
css='''
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#eaf2fb;background:#0b1627}
*{box-sizing:border-box}body{margin:0}.wrap{width:min(1100px,94%);margin:auto}
header{padding:52px 0 36px;background:linear-gradient(125deg,#142039,#1e1c36 68%,#23192d)}
small.eyebrow{font-weight:800;letter-spacing:.12em;color:#80e9d3}
h1{font-size:clamp(32px,5vw,58px);line-height:1.08;letter-spacing:-.03em;margin:14px 0}
p{line-height:1.75;color:#b8cadc}strong{color:#fff}a{color:#8be8df}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}
.kpi{background:#1c2b42;border:1px solid #3a4a64;border-radius:14px;padding:18px}.kpi b{font-size:30px;color:#80e9d3;display:block;margin:7px 0}.kpi label{color:#b2c2d7;font-size:13px}
section{margin:40px 0}.panel{background:#15233a;border:1px solid #30425c;border-radius:16px;padding:22px 24px;margin-top:18px}
h2{font-size:27px;margin:0 0 12px;letter-spacing:-.02em}img{max-width:100%;height:auto;display:block;border-radius:10px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:13px 9px;border-bottom:1px solid #3a4862;font-size:14px}th{color:#7fe7d4}td{color:#eaf1fc}.overflow{overflow-x:auto}
.caveat{border-left:4px solid #ffbe91;padding:12px 18px;background:#2c2c3e}footer{color:#95aabe;padding:20px 0 45px}
@media(max-width:700px){.kpis{grid-template-columns:repeat(2,1fr)}header{padding-top:30px}.panel{padding:15px}}
'''
page=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Retail Signals · Does ML help?</title><style>{css}</style></head><body><header><div class="wrap"><small class="eyebrow">RETAIL SIGNALS / EXPERIMENT 02</small><h1>Would machine learning<br>actually forecast better?</h1><p>I had already tested simple forecasting rules against a historical four-week sales holdout. I wanted to see whether Random Forest or XGBoost could learn patterns that the simple rules missed—without changing the test period or accidentally using future sales.</p>
<div class="kpis"><div class="kpi"><label>EARLIER VALIDATION SELECTED</label><b>Random Forest</b><label>19.1% validation WAPE</label></div><div class="kpi"><label>SELECTED RF / FINAL TEST</label><b>15.7%</b><label>WAPE on untouched weeks</label></div><div class="kpi"><label>DAMPED TREND / FINAL TEST</label><b>13.4%</b><label>Lower test error, not preselected</label></div><div class="kpi"><label>FOUR-WEEK MEAN / FINAL TEST</label><b>15.2%</b><label>Simple historical baseline</label></div></div></div></header>
<main class="wrap"><section><h2>What I compared</h2><p>I kept the same five nonoverlapping, four-week historical validation periods and the same separate November 7–December 4, 2011 test as the original statistical experiment. Alongside the four-week average, four-week repeat and eight-week damped trend, I trained two ML models: <strong>Random Forest</strong> and <strong>XGBoost</strong>. The ML models share patterns across {sumry['pool_size']} active SKUs chosen entirely from early history, plus a separate aggregate-sales series. Their features are available at the forecast date: earlier weekly sales, moving statistics, target-week calendar information and forecast horizon.</p><p>Both ML methods make direct predictions for weeks one through four. I fixed their hyperparameters before evaluation and did not use the final test to adjust them. Every candidate was evaluated with WAPE, then a method was chosen separately for total sales and each of five previously chosen products.</p><div class="panel"><img src="../charts/09_ml_forecast_comparison.png" alt="Actual and forecast units in the final four test weeks"></div></section>
<section><h2>The result was not the one I expected</h2><p>Random Forest had the lowest aggregate error on the earlier validation periods, so it was selected under the predefined rule. On the genuinely untouched test, however, the eight-week damped trend had a lower error. Had I simply displayed the lowest test score as my model selection, I would have exaggerated the result.</p><div class="panel"><div class="overflow"><table><thead><tr><th>Candidate</th><th>Earlier validation WAPE</th><th>Final test WAPE</th><th>Selection status</th></tr></thead><tbody>{rows}</tbody></table></div></div><div class="panel"><img src="../charts/10_ml_validation_vs_test.png" alt="Historical model validation and untouched test WAPE"></div></section>
<section><h2>Did ML behave differently at product level?</h2><p>Yes, although the pattern was mixed. Validation chose XGBoost for one of the five products, Random Forest for two, and the simpler rules for the other two. Different products responded differently on the final test. I kept the early-history SKU-selection rule from the earlier experiment, rather than hand-picking products after seeing the test results.</p><div class="panel"><div class="overflow"><table><thead><tr><th>Product</th><th>Method selected on validation</th><th>Selected-method test WAPE</th><th>Simple-baseline test WAPE</th></tr></thead><tbody>{sku_rows}</tbody></table></div></div><div class="panel"><img src="../charts/11_ml_product_holdout.png" alt="Holdout WAPE for preselected methods versus a simple baseline across five products"></div></section>
<section><h2>What I learned—and what remains missing</h2><p>The comparison argues against assuming complex models will automatically win. The strongest method during one validation window is not guaranteed to generalize to a different period. I would want more seasons and promotion and stock-availability records before designing a production replenishment forecast. The existing dataset covers approximately one year and is filtered to positive sold quantities: <strong>it does not measure customers' unmet demand</strong>.</p><p class="caveat"><strong>Methodological caution:</strong> This is a single historical, offline test on relatively active products. Hyperparameters were set in advance, not searched extensively. An empty observed week was treated as zero recorded units, not proof that true demand was zero. These are illustrative out-of-time results, not a current-market forecast.</p><p><a href="../notebooks/retail_ml_forecast_comparison.ipynb">Executed comparison notebook</a> · <a href="../scripts/ml_forecast_comparison.py">Reproducible training code</a> · <a href="../results/ml_validation_folds.csv">Validation evidence</a> · <a href="../README.md">Full investigation</a></p></section></main><footer class="wrap">SQL / PYTHON / SCIKIT-LEARN / XGBOOST  ·  HISTORICAL DATA SCIENCE CASE STUDY</footer></body></html>'''
p=ROOT/'report/ml_forecast_comparison.html';p.write_text(page,encoding='utf8');print('Generated',p)
