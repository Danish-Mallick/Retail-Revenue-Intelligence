# LinkedIn Featured and Projects — copy-ready

**Project name**  
Retail Revenue Intelligence | SQL, Python & Power BI

**Featured item title**  
Retail Signals — What Actually Drove the Autumn Sales Increase?

**Featured item description**  
I investigated a historical online retail transaction dataset and started with a simple question: when sales jumped in autumn 2011, were customers spending more or placing more orders? I found that September–November sales rose 34.1% while invoice count grew 53.0% and average order value fell 12.4%.

The next step was customer behaviour. I separated the retrospective contribution of repeat buyers from actual month-by-month cohort activity, then examined RFM-style groups and geographic concentration. The project includes documented date repair, PostgreSQL queries, Python analysis, a two-page Power BI starter project and a standalone interactive dashboard.

**Featured image:** `charts/LinkedIn_Featured_Sales.png`. It is a **verified-data dashboard design preview**, not a Power BI screenshot. Add the link to the GitHub repository as a **separate Featured link** after reviewing and making the repository public.

**Suggested LinkedIn skills:** SQL · PostgreSQL · Python · pandas · Power BI · DAX · Data Visualization · Cohort Analysis · Customer Segmentation · Data Cleaning

**Do not claim:** deployed Power BI report, predictive churn model, return/cancellation analysis, actual profit or unverified original dataset ownership. Review and run the actual work before publishing it as your own portfolio project.

### Optional forecasting add-on for a second Featured image

I added a forecasting experiment after finishing the revenue and customer analysis. I tested whether weekly recorded units could have predicted the late-autumn surge, using five earlier rolling windows to select among simple methods before evaluating an untouched four-week November–December 2011 period. The selected aggregate method recorded 13.4% historical WAPE versus 15.2% for a trailing-average baseline, but both underestimated the seasonal rise. SKU-level results were mixed. This is an honest historical backtest using sales as a proxy for demand, not a live demand-forecasting system.

Artwork: `charts/07_demand_forecast_backtest.png`


## Optional update after running the forecasting comparison

If you mention forecasting in the LinkedIn project, a defensible version is:

> I extended the sales investigation by comparing three statistical forecasting rules with Random Forest and XGBoost. I kept the same five historical validation windows and a separate four-week holdout so I could check whether the extra complexity actually helped. Random Forest had the lowest aggregate validation error (19.1% WAPE), but the simpler damped trend produced a lower error on the final holdout (13.4% versus 15.7% for the selected RF). The result made me more cautious about treating a single model's validation performance as proof it will generalize.

Do not imply the dashboard image itself is a deployed Power BI screenshot. The ML experiment is in `report/ml_forecast_comparison.html`, and full code is in `scripts/ml_forecast_comparison.py`.
