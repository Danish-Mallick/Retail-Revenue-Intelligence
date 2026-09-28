-- Counts and revenues answer different questions; high units != high revenue.
SELECT stock_code, MAX(description) AS one_recorded_description,
       COUNT(DISTINCT invoice_no) AS orders,
       SUM(quantity) AS units, ROUND(SUM(revenue),2) AS observed_revenue
FROM retail.lines
GROUP BY stock_code ORDER BY observed_revenue DESC LIMIT 15;

-- Country totals describe this extract's sales mix, not broader market demand.
SELECT country, COUNT(DISTINCT invoice_no) AS orders,
       COUNT(DISTINCT customer_id) AS customers,
       ROUND(SUM(revenue),2) AS observed_revenue,
       ROUND(100*SUM(revenue)/SUM(SUM(revenue)) OVER (),2) AS share_of_extract_pct
FROM retail.lines
GROUP BY country ORDER BY observed_revenue DESC;
