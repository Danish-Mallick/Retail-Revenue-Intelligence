-- Retention denominator = distinct customers first observed in the cohort month.
-- Positive counts represent activity in that specific subsequent calendar month,
-- not cumulative retention. The Dec-2011 observation period is incomplete.
WITH activity AS (
 SELECT DISTINCT customer_id, DATE_TRUNC('month',invoice_date)::date AS activity_month
 FROM retail.lines
), labeled AS (
 SELECT customer_id, activity_month,
        MIN(activity_month) OVER (PARTITION BY customer_id) AS cohort_month
 FROM activity
), indexed AS (
 SELECT *, (EXTRACT(YEAR FROM age(activity_month,cohort_month))*12
                  +EXTRACT(MONTH FROM age(activity_month,cohort_month)))::int AS month_index
 FROM labeled
), cohort_size AS (
 SELECT cohort_month, COUNT(*) AS cohort_size
 FROM indexed WHERE month_index=0 GROUP BY 1
)
SELECT i.cohort_month, i.month_index,
       c.cohort_size, COUNT(DISTINCT i.customer_id) AS returning_customers,
       ROUND(100*COUNT(DISTINCT i.customer_id)::numeric/NULLIF(c.cohort_size,0),2) AS retention_pct
FROM indexed i JOIN cohort_size c USING (cohort_month)
GROUP BY 1,2,3 ORDER BY 1,2;
