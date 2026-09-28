-- Observed invoice-frequency distribution; useful before defining RFM cuts.
WITH freq AS (
 SELECT customer_id,COUNT(DISTINCT invoice_no) AS orders,
        SUM(revenue) AS revenue FROM retail.lines GROUP BY customer_id
), band AS (
 SELECT CASE WHEN orders=1 THEN '1 order' WHEN orders BETWEEN 2 AND 4 THEN '2-4 orders'
             WHEN orders BETWEEN 5 AND 9 THEN '5-9 orders' ELSE '10+ orders' END AS frequency_band,
        CASE WHEN orders=1 THEN 1 WHEN orders<=4 THEN 2 WHEN orders<=9 THEN 3 ELSE 4 END AS sort_key,
        revenue FROM freq
)
SELECT frequency_band,COUNT(*) AS customers,ROUND(SUM(revenue),2) AS revenue
FROM band GROUP BY frequency_band,sort_key ORDER BY sort_key;
