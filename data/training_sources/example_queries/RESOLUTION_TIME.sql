 -- Query to get the average resolution time for each customer.
  FROM
    B2B_CORRELATED_DATA.CORRELATED_SCHEMA.SUPPORT_TICKETS t
  JOIN
    B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA f ON t.CUSTOMER_ID = f.CUSTOMER_ID
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