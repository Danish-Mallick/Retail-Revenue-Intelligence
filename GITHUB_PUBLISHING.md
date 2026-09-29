# Publishing to GitHub and LinkedIn

1. Review the analyses, verify the numbers you want to discuss in an interview, and confirm you have the right to use the derived aggregates. The **raw** CSV is not included in this archive.
2. Create an empty repository named `Retail-Revenue-Intelligence`. Upload all files from the **root of this project** (the `README.md` should be at repository root). Keep it private while you review.
3. Test `powerbi/Retail_Revenue_Intelligence.pbip` on **your own** Windows Power BI Desktop. The file is a generated editable PBIP, but the Desktop appearance hasn't been verified in this environment. Do not claim to have published a live Power BI report based only on the preview image.
4. Optional interactive GitHub Pages dashboard: Settings → Pages → Deploy from a branch → `main` → `/(root)`. The root `index.html` is a standalone interactive dashboard with embedded aggregate data and no external dependencies; verify the published result once deployed.
5. Make the repository public after reviewing the README and source notes. Under your LinkedIn profile's **Featured** section, add the repository as a link and the `charts/LinkedIn_Featured_Sales.png` image as a second media item. Use `LINKEDIN_FEATURED_TEXT.md` for concise text that matches what the evidence actually shows.
6. The cover image is a **design preview**. If you take an actual Power BI screenshot, label that separately after your Desktop review.

The demand-forecasting addition is part of the same repository, not a separate project. Rebuild it with `python scripts/demand_forecast.py --source 'data/raw/Online Retail.csv'` then `python scripts/plot_forecast.py` and `python scripts/build_forecast_dashboard.py`. Rebuild the Power BI project with `python scripts/build_powerbi.py`; it now includes a third **Demand Forecasting** page, which still requires validation in Windows Power BI Desktop.


### Additional ML comparison files
The Random Forest and XGBoost extension is included in the same repository. `results/ml_holdout_comparison.csv`, `report/ml_forecast_comparison.html`, and charts `09`–`11` can be reviewed without the original transaction extract. Training again requires the exact filtered source and the extra requirements `scikit-learn` and `xgboost`. The Power BI project includes a fourth **ML Model Comparison** page with frozen verified aggregate snapshots; check the rendering locally in Desktop before using any screenshot as a published report.
