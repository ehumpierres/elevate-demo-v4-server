-- Query to get the number of support tickets and total revenue for each customer.
SELECT
  s.CUSTOMER_ID,
  f.CUSTOMER_NAME,
  f.INDUSTRY,
  f.CUSTOMER_TYPE,
  COUNT(s.TICKET_ID) AS ticket_count,
  SUM(CASE WHEN f.ACCOUNT_TYPE = 'Income' THEN f.AMOUNT ELSE 0 END) AS total_revenue
FROM
  DEMO_V4.CORRELATED_SCHEMA.SUPPORT_TICKETS s
JOIN
  DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA f ON s.CUSTOMER_ID = f.CUSTOMER_ID
GROUP BY
  s.CUSTOMER_ID, f.CUSTOMER_NAME, f.INDUSTRY, f.CUSTOMER_TYPE
ORDER BY
  ticket_count DESC
LIMIT 10;