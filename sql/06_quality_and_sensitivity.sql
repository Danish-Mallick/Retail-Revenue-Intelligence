-- Verify how many rows had a verifiable ambiguous-date component inversion.
SELECT COUNT(*) AS rows,
       COUNT(*) FILTER (WHERE invoice_date <> parsed_ts) AS repaired_dates,
       COUNT(DISTINCT invoice_no) AS distinct_invoices,
       COUNT(DISTINCT customer_id) AS distinct_customers
FROM retail.lines;

-- Quantify exact-row duplicate sensitivity, without assuming duplicate lines
-- are invalid: an invoice may genuinely contain an identical line twice.
WITH numbered AS (
 SELECT *, ROW_NUMBER() OVER (
  PARTITION BY invoice_no,stock_code,description,quantity,unit_price,customer_id,
               country,invoice_date_text,original_year,original_month,original_week,
               original_day,original_weekday ORDER BY invoice_no) AS rn
 FROM retail.raw_extract
)
SELECT COUNT(*) FILTER (WHERE rn>1) AS possible_duplicate_rows,
       ROUND(SUM(quantity*unit_price) FILTER (WHERE rn>1),2) AS sensitivity_value
FROM numbered;

-- A few invoices have inconsistent timestamps. Invoice-level work takes
-- the earliest corrected timestamp; flag rather than silently erase.
SELECT invoice_no, COUNT(DISTINCT invoice_date) AS distinct_timestamps
FROM retail.lines GROUP BY invoice_no HAVING COUNT(DISTINCT invoice_date)>1
ORDER BY invoice_no;
