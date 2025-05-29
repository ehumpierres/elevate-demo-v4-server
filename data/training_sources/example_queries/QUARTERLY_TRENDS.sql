-- Query to get the quarterly revenue trend over the past three years, including transaction count.
SELECT
  DATE_TRUNC('quarter', TRANSACTION_DATE) AS quarter,
  SUM(AMOUNT) AS quarterly_revenue,
  COUNT(*) AS transaction_count
FROM
  DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA
WHERE
  ACCOUNT_TYPE = 'Income'
  AND TRANSACTION_DATE >= DATEADD('year', -3, CURRENT_DATE())
GROUP BY
  quarter
ORDER BY
  quarter;