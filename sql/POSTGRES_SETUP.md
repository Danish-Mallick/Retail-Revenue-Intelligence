# Running the SQL locally

Use PostgreSQL 14+ and `psql`. Create an empty database, e.g. `createdb online_retail_portfolio`, then create `data/raw/` and place the **same provided 13-column filtered extract** there as `Online Retail.csv`. From the repository root:

```bash
psql -d online_retail_portfolio -f sql/00_schema_and_date_repair.sql
psql -d online_retail_portfolio -f sql/01_revenue_decomposition.sql
psql -d online_retail_portfolio -f sql/02_returning_customer_revenue.sql
psql -d online_retail_portfolio -f sql/03_customer_cohorts.sql
psql -d online_retail_portfolio -f sql/04_rfm_segmentation.sql
```

The first script contains `\copy`, a **psql** meta-command (it will not work verbatim in a generic SQL editor). If you prefer pgAdmin, import the 13 original columns into `retail.raw_extract` in the exact schema order, then create the view from the second half of `00_schema_and_date_repair.sql`. The analysis deliberately works with the attached filtered extract. The original unfiltered UCI Online Retail release may have returns, missing customer IDs and different date formatting, so substituting that file without adapting the pipeline will not reproduce these exact figures.
