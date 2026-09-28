-- Be precise: 'returning' here means purchasing in a month AFTER a customer's
-- first observed month within this extract. This is NOT lifetime-new acquisition.
WITH invoices AS (
 SELECT invoice_no, MIN(customer_id) AS customer_id,
        DATE_TRUNC('month',MIN(invoice_date))::date AS month,
        SUM(revenue) AS invoice_value
 FROM retail.lines GROUP BY invoice_no
), first_seen AS (
 SELECT customer_id, MIN(month) AS first_observed_month
 FROM invoices GROUP BY customer_id
)
SELECT i.month,
       ROUND(SUM(i.invoice_value) FILTER (WHERE i.month=f.first_observed_month),2) AS first_observed_month_revenue,
       ROUND(SUM(i.invoice_value) FILTER (WHERE i.month>f.first_observed_month),2) AS later_month_returning_revenue,
       ROUND(100*SUM(i.invoice_value) FILTER (WHERE i.month>f.first_observed_month)/NULLIF(SUM(i.invoice_value),0),1) AS later_month_returning_share_pct,
       COUNT(DISTINCT i.customer_id) AS active_customers
FROM invoices i JOIN first_seen f USING (customer_id)
GROUP BY i.month ORDER BY i.month;
