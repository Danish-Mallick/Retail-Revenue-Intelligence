# Machine-learning experiment: decisions and reproducibility

The question is whether a machine-learning model improves **future recorded unit sales forecasts** versus an established statistical benchmark. It is not a competition to find the smallest possible error on the already-seen November test, nor an estimate of stockout-adjusted demand.

## Why use the local Random Forest rather than PySpark?

I used `sklearn.ensemble.RandomForestRegressor` because the weekly feature panel fits comfortably on one machine. DataCamp's `pyspark.ml.regression.RandomForestRegressor` implements the same broad random-forest regression family but is a different implementation intended for distributed Spark pipelines. I tested local Random Forest alongside `xgboost.XGBRegressor`; running Spark here would introduce distributed infrastructure without changing the core question.

## A fair timeline

| Stage | Dates | How it is used |
|---|---|---|
| Pool/SKU selection | 2010-12-06 to 2011-05-29 | Choose 120 active training SKUs (`>=12` early active weeks) and the existing 5 reported SKUs (`>=17` early active weeks) using only previous purchasing frequency. |
| Rolling validation | Forecast origins May 30, Jun 27, Jul 25, Aug 22, Sep 19 | At each origin, train on weeks with complete targets strictly before that origin; predict four subsequent weeks. Errors are pooled across the five nonoverlapping 4-week periods. |
| Separation gap | Oct 17 to Nov 6 | No validation predictions; observations may enter *final training* only. |
| Untouched historical test | Forecast origin Nov 7, through Dec 4 | Report WAPE for all five candidates. Do not use these observations to tune ML or choose the model. |

The first partially observed week and last partially observed week are excluded, leaving 52 complete calendar weeks. One entirely unobserved holiday week is encoded as **zero recorded units** (not zero latent demand). The same time windows and original five evaluation products are used for the three statistical forecasts and both ML models.

## What the model can see

For every training example, all predictor values are available by the corresponding forecast origin: eight historical weekly lags, the last four/eight-week means and standard deviations, recent-vs-older mean difference, counts of positive weeks, log scale of recent sales, known calendar week/month of the predicted week, forecast horizon `1..4`, and a flag distinguishing the aggregate series. The next week's **actual** sales cannot enter as a lag when forecasting weeks two through four. Rather than recursively feeding future observations, the model learns separate horizon-conditioned predictions.

To share information across SKU scales, the learning target is the future weekly quantity divided by the **mean of the eight already observed weeks** (floored at 1 for stability). In training only, the target ratio is capped at 20 to limit extreme spikes. Forecasts multiply predictions by the current known history scale and floor negative outputs at zero. One extra all-product series is pooled with the SKU panel; its training rows have sample weight 2 to ensure it is not entirely overwhelmed by the SKU examples. These are design choices, not guaranteed optimal settings.

Both models are fixed **before** validation: Random Forest has 140 trees, depth 9, minimum leaf size 6 and maximum feature fraction 0.8; XGBoost has 170 trees, depth 4, learning rate 0.055 and regularization lambda 12, subsample 0.9 and column subsample 0.85. Both use seed 42. They are illustrative fixed configurations, not the results of a hyperparameter search.

## Evaluation and interpretation

WAPE is `100 * sum(abs(actual - forecast)) / sum(abs(actual))`. Validation WAPE pools numerator and denominator across all five earlier four-week folds **for each series**. A method is selected separately for all products and each of the five reported SKUs, using only the earliest validation WAPE. A simple deterministic order breaks a hypothetical tie; test scores never break ties.

For all-product units, the **preselected** method was Random Forest (19.08% validation WAPE), but it scored 15.70% on the final test. The older damped trend scored 19.65% on validation and 13.37% on the final test. This demonstrates one-period selection uncertainty; it does not establish that the damped trend would always outperform ML on new data.

The holdout is a **single** four-week period of a single historical year; no 2026 production forecast is claimed. We lack stockouts, promotions, returns/cancellations and reliable longer-term seasonality. Product-level panel examples share calendar effects and should not be interpreted as independent repeated years.

## Reproduce

From repository root, using the exact uploaded 13-column filtered CSV locally stored as `data/raw/Online Retail.csv`:

```bash
pip install -r requirements.txt
python scripts/demand_forecast.py --source 'data/raw/Online Retail.csv'
python scripts/ml_forecast_comparison.py --source 'data/raw/Online Retail.csv'
python scripts/plot_ml_comparison.py
python scripts/build_ml_report.py
python scripts/build_powerbi.py
python -m unittest discover -s tests -v
```

The repository deliberately keeps raw customer-level transactions out of version control. Aggregate fold outcomes and model comparisons in `results/ml_*.csv` allow the methodology and conclusions to be audited without redistributing the source.
