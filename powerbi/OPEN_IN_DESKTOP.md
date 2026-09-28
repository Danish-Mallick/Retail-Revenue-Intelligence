# Power BI: open the editable 2-page PBIP

Double-click **Retail_Revenue_Intelligence.pbip** with an up-to-date Power BI Desktop version supporting PBIP/TMDL. The project includes two pages: **Sales and Markets** and **Customers and Cohorts**.

This report imports *compressed, embedded* precomputed CSV snapshots. It needs no access to your raw third-party retail CSV and does not depend on your local file paths. The snapshots come from the actual Python analysis in `results/` (sales by month/country, anonymized customer metrics, first-following-month cohort summary).

**To refresh** after updating the user-supplied raw extract, run `python scripts/analyze.py --source 'data/raw/Online Retail.csv'` followed by `python scripts/build_powerbi.py`; reopen the PBIP. The snapshot tables are not live ETL connections. This is an editable Power BI project; I generated and structurally validated the definitions but did **not** open/verify them on Windows Power BI Desktop. In Desktop, verify visuals and filters before claiming it as an interactive deployed report or sharing screenshots.

The customer page and cohort bar use separate precomputed tables. Customer country assigns the highest-sales country to the **eight cross-country customers**; the cohort chart is globally aggregated and unaffected by the customer-country slicer. Do not imply the slicer changes cohort retention. The source excludes cancellations and unknown customers, and excludes part of December 2011.
