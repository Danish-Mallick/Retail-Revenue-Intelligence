# Source, reproducibility, and what is actually being counted

The project was built from a **user-supplied 13-column `Online Retail.csv` extract**. It contains 384,721 positive-quantity, positive-price rows and no missing `CustomerID`. It resembles a cleaned/filtered derivative of the UCI **Online Retail** dataset, but the precise upstream transformation and redistribution rights of this uploaded file were not provided. It is **not asserted to be identical** to the complete original release.

Related public dataset page (not a guarantee of byte-identical rows): https://archive.ics.uci.edu/dataset/352/online+retail

Original user-supplied source fingerprint (SHA-256):
`a4b796f9bd7a07f3881429bcc64165d0d03578a1b9f03a800eb4baebb0737a9a`

To reproduce the exact output, place that exact version at `data/raw/Online Retail.csv`. The raw file is deliberately excluded from this **GitHub-ready** package; the published results are aggregates, and the Power BI customer table removes the original customer identifiers. The original UCI version includes additional transaction types and may have differently encoded dates, so you **cannot** expect the same totals by downloading any similar-looking CSV from elsewhere.

- **Time span after repair:** 1 Dec 2010, 08:26 through 9 Dec 2011, 12:50. December 2011 is a *partial* month.
- **Mixed date parsing:** in 147,998 rows, the stored month and day are different and both fit within 1–12. Reverse them and rebuild all derived calendar fields; otherwise your monthly charts are wrong. The invoice-number chronology check changes from 21 reversals to zero. Rows with the same day and month (15,101 rows) are unchanged by swapping and not included among the 147,998 modifications.
- **Invoice timestamps:** 30 invoices show multiple corrected timestamps across their lines; choose the earliest corrected timestamp for invoice-level analysis, retain line-level corrected timestamps for line-level analysis.
- **Exact duplicate rows:** 5,178. Main figures retain them because two identical line items can be legitimate. Removing copies after the first subtracts 23,119.37, which is about 0.38% of recorded sales; do not present that sensitivity as proven duplicate fraud.
- **Currency:** the CSV contains no field encoding currency. The dashboard labels amounts as GBP based on the source's UK-retail context **as an explicit assumption**.
- **What is missing:** return/cancellation records, non-positive quantity/price rows, missing-ID orders, product cost, marketing exposure, full customer histories. Accordingly, we cannot estimate refunds, total business sales, profit, acquisition effectiveness, true churn or causal impact.
- **Month-specific cohort:** 'first observed' means the first month present *in this extract*, which may not be the first-ever transaction.
- **RFM segmentation:** the selected thresholds are descriptive business heuristics at the extract end, not a predictive churn algorithm. Classifying customers using their full extract history and then calling that share 'monthly retention' would introduce look-ahead bias.
- **Geographic caveat:** eight customers purchased in more than one country. Their country in the anonymized customer table is the one associated with their highest recorded spend, for one row per customer; the month/country revenue table is invoice-country based, with no such assignment.

Data and code generated as a portfolio case study. Credit and verify rights for the user-supplied original before redistributing raw or row-level derived transactions.
