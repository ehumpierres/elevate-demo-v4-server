-- Query to get the top 5 industries by total revenue
SELECT
 INDUSTRY,
 SUM(AMOUNT) AS total_revenue
FROM
 DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA
WHERE
 ACCOUNT_TYPE = 'Income'
GROUP BY
 INDUSTRY
ORDER BY
 total_revenue DESC
LIMIT 5;