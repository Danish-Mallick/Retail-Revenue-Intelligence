-- Rule-based, as-of one day after latest observed transaction (2011-12-10).
-- Not a predictive churn or CLV model. Full-window metrics are LOOK-AHEAD
-- information if you try to use these segments for earlier monthly decisions.
WITH invoices AS (
 SELECT customer_id, invoice_no, MIN(invoice_date) AS invoice_date,
        SUM(revenue) AS order_value
 FROM retail.lines GROUP BY 1,2
), metrics AS (
 SELECT customer_id, SUM(order_value) AS monetary_value,
        COUNT(*) AS frequency,
        ((SELECT MAX(invoice_date)::date+1 FROM retail.lines)
            -MAX(invoice_date)::date)::int AS recency_days
 FROM invoices GROUP BY 1
), labeled AS (
 SELECT *, CASE
   WHEN recency_days<=30 AND frequency>=5 THEN 'Champions'
   WHEN recency_days<=90 AND frequency>=5 THEN 'Loyal active'
   WHEN recency_days>90 AND frequency>=3 THEN 'At risk (rule-based)'
   WHEN recency_days>90 THEN 'Dormant (rule-based)'
   WHEN recency_days<=30 THEN 'Recent buyers'
   ELSE 'Developing'
 END AS segment FROM metrics
)
SELECT segment, COUNT(*) AS customers,
       ROUND(SUM(monetary_value),2) AS observed_revenue,
       ROUND(AVG(frequency),2) AS average_invoice_frequency,
       ROUND(AVG(recency_days),2) AS average_recency_days
FROM labeled
GROUP BY segment ORDER BY observed_revenue DESC;
