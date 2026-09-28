-- Did autumn revenue rise because there were more orders or larger orders?
-- Exclude December 2011 from a full-month growth narrative: data end on Dec 9.
WITH monthly AS (
 SELECT DATE_TRUNC('month', invoice_date)::date AS month,
        SUM(revenue) AS revenue,
        COUNT(DISTINCT invoice_no) AS orders,
        COUNT(DISTINCT customer_id) AS active_customers
 FROM retail.lines
 GROUP BY 1
)
SELECT month, ROUND(revenue, 2) AS revenue,
       orders, active_customers,
       ROUND(revenue/NULLIF(orders,0),2) AS average_order_value,
       ROUND(100*(revenue/LAG(revenue) OVER (ORDER BY month)-1),1) AS revenue_growth_pct,
       ROUND(100*(orders::numeric/LAG(orders) OVER (ORDER BY month)-1),1) AS order_growth_pct
FROM monthly
ORDER BY month;
