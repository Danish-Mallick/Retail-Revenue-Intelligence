# Verified analysis outputs

These results were generated using `scripts/analyze.py` against the exact user-supplied 13-column filtered extract with SHA-256 `a4b796f9bd7a07f3881429bcc64165d0d03578a1b9f03a800eb4baebb0737a9a`.

- `verified_metrics.json`: headline source checks, full-window measures, observed start/end dates, duplicate sensitivity, chronology checks.
- `monthly.csv`: source-wide month level. **Dec 2011 is partial** and should not be treated as a full-month comparison.
- `monthly_country.csv`: month-by-invoice-country summary. Countable invoices are unique to one country. Customer counts summed across countries or months **may double-count** customers.
- `country.csv`: all 37 countries' full-window invoice counts, distinct observed customers and sales.
- `products.csv`: stock-code aggregation, revenue, unit count and a modal description; descriptions are not unique product keys.
- `customer_metrics_anonymized.csv`: one row per customer, with original IDs and exact purchase timestamps removed. `CustomerKey` is a sequential project surrogate (not cryptographic anonymization); eight multi-country customers are assigned to their highest-sales country.
- `segments.csv`: six *descriptive* end-of-window customer groups. Thresholds are in `scripts/analyze.py` and `sql/04_rfm_segmentation.sql`.
- `cohort_retention.csv`: first-observed monthly cohorts and exact later-month activity, not acquisition or cumulative survival.
- `invoice_status_summary.csv`: first-observed month versus subsequent-month revenue; based on the first month in this file.

Raw, row-level original transactions are **not** distributed. The file lacks product costs, currency metadata, cancellations/returns and histories outside the observed window. Figures shown as GBP make an explicit source-context assumption.
