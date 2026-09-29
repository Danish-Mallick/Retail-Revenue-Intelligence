"""Create & execute a reviewable notebook that uses published aggregate results.

Training is rerunnable by running scripts/ml_forecast_comparison.py after supplying
original CSV locally; notebook needs no customer-level source file in GitHub.
"""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient
R=Path(__file__).resolve().parents[1];N=R/'notebooks/retail_ml_forecast_comparison.ipynb'
book=nbf.v4.new_notebook();cells=[]
md=lambda x:cells.append(nbf.v4.new_markdown_cell(x))
code=lambda x:cells.append(nbf.v4.new_code_cell(x))
md('''# I tried machine learning to forecast retail sales. Did it improve the result?

This notebook is the result-review companion to the [training script](../scripts/ml_forecast_comparison.py). The script is the **source of truth** for model fitting and model selection. These cells read the published *aggregate* comparison results; the raw customer-level retail extract is not in this repository.

I started with three statistical methods. The eight-week damped trend was chosen from the original three and achieved 13.4% WAPE on a held-out November test. I then introduced Random Forest and XGBoost to test whether learned patterns from other active products could improve the four-week forecast. I did **not** change the test window.''')
md('''## 1. Reusing exactly the same test design

Both ML models use horizon-aware direct forecasts. They train on past completed weeks only, with lagged sales, four- and eight-week statistics and calendar features known at prediction time. The panel contains the 120 SKUs selected solely on early activity before 30 May 2011 and an additional all-products series.

**Five validation origins:** 30 May, 27 June, 25 July, 22 August and 19 September 2011. Each predicts the *next four weeks*. The final holdout is **7 November–4 December 2011**; nothing from those four weeks is used to choose a method or set hyperparameters.

All figures refer to *observed sold units*, not unconstrained demand.''')
code("""from pathlib import Path
import pandas as pd
from IPython.display import display
root = Path.cwd().resolve().parent if Path.cwd().name == 'notebooks' else Path.cwd().resolve()
assert (root / 'results/ml_holdout_comparison.csv').exists(), 'Run from repository root or notebooks folder'
results = root / 'results'
comparison = pd.read_csv(results / 'ml_holdout_comparison.csv')
validation = pd.read_csv(results / 'ml_validation_folds.csv')
choices = pd.read_csv(results / 'ml_selected_methods.csv')
print('Validation records:', len(validation), '| reported series:', comparison.Series.nunique())
print('Same five origins:', sorted(validation.Origin.unique().tolist()))
""")
md('''## 2. Why the final test changed the story

I selected a method using **validation WAPE**, not the final test WAPE. That matters here because the earlier validation and the final test favour different methods.''')
code("""aggregate = comparison.query('Series == "All products"').copy()
aggregate['ValidationWAPE'] = aggregate.ValidationWAPE.round(2)
aggregate['HoldoutWAPE'] = aggregate.HoldoutWAPE.round(2)
display(aggregate[['Method','ValidationWAPE','HoldoutWAPE','SelectedByValidation']].sort_values('ValidationWAPE').reset_index(drop=True))""")
md('''## 3. What happened on the four held-out weeks?

Random Forest won the earlier validation among all five methods, but on this one separate test the damped trend produced a lower error. Showing both is more informative than advertising the lowest test number as if it had been selected in advance.''')
code("""holdout = pd.read_csv(results / 'ml_holdout_weeks.csv')
p = holdout.query('Series == "All products"').pivot(index='WeekStart',columns='Method',values='ForecastUnits')
actual = holdout.query('Series == "All products" and Method == "four_week_mean"').set_index('WeekStart')['ActualUnits']
display(pd.concat([actual.rename('ActualUnits'),p],axis=1).round(1))
""")
md('''## 4. Would the product-level conclusion be the same?

No. The initial set of five products was selected from early-history purchasing frequency. Validation chose a different method depending on the series. Their holdout errors below are diagnostic observations: they were *not* used to reselect the models.''')
code("""winners = comparison.query('SelectedByValidation == True and Series != "All products"').copy()
baseline = comparison.query('Method == "four_week_mean" and Series != "All products"')[['Series','HoldoutWAPE']].rename(columns={'HoldoutWAPE':'BaselineTestWAPE'})
display(winners[['Series','Product','Method','ValidationWAPE','HoldoutWAPE']].merge(baseline,on='Series').round(2))""")
md('''## 5. Reproducing the training—not inventing a current forecast

Install dependencies with `pip install -r requirements.txt` and supply the **same filtered extract** as `data/raw/Online Retail.csv`. Then run:

```bash
python scripts/demand_forecast.py --source 'data/raw/Online Retail.csv'
python scripts/ml_forecast_comparison.py --source 'data/raw/Online Retail.csv'
python scripts/plot_ml_comparison.py
python scripts/build_ml_report.py
```

The script uses fixed Random Forest (140 trees, max depth 9) and XGBoost (170 trees, max depth 4) configurations rather than tuning on the final holdout. The feature construction is in `features()`, full historical fold construction in `panel_training()`, and four-week direct prediction in `predict_ml()`.

**What I would need before production:** several years of comparable sales, known stock availability, promotion calendars, a realistic replenishment horizon, and repeated forward tests. The data are a filtered historical extract and cannot establish actual lost demand.''')
book.cells=cells;book.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'}}
NotebookClient(book,timeout=90,kernel_name='python3',resources={'metadata':{'path':str(R)}}).execute()
nbf.write(book,N)
print('Wrote executed',N,'cells:',len(book.cells))
