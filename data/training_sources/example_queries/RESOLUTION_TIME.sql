-- Query to get the average resolution time for each customer.
WITH customer_metrics AS (
  SELECT
    t.CUSTOMER_ID,
    AVG(DATEDIFF('day', t.CREATED_DATE, t.UPDATED_DATE)) AS avg_resolution_days,
    SUM(CASE WHEN f.ACCOUNT_TYPE = 'Income' THEN f.AMOUNT ELSE 0 END) AS total_revenue
  FROM
    DEMO_V4.CORRELATED_SCHEMA.SUPPORT_TICKETS t
  JOIN
    DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA f ON t.CUSTOMER_ID = f.CUSTOMER_ID
  GROUP BY
    t.CUSTOMER_ID
)

SELECT
  CASE
    WHEN avg_resolution_days < 1 THEN 'Same Day'
    WHEN avg_resolution_days < 3 THEN '1-3 Days'
    WHEN avg_resolution_days < 7 THEN '3-7 Days'
    ELSE 'Over 7 Days'
  END AS resolution_time_bucket,
  COUNT(*) AS customer_count,
  AVG(total_revenue) AS avg_revenue_per_customer
FROM
  customer_metrics
GROUP BY
  resolution_time_bucket
ORDER BY
  CASE
    WHEN resolution_time_bucket = 'Same Day' THEN 1
    WHEN resolution_time_bucket = '1-3 Days' THEN 2
    WHEN resolution_time_bucket = '3-7 Days' THEN 3
    ELSE 4
  END;