-- Query to get the average sales cycle duration (in days) for each industry.
SELECT
INDUSTRY,
AVG(DATEDIFF('day', OPEN_DATE, CLOSE_DATE)) AS avg_sales_cycle_days
FROM
DEMO_V4.CORRELATED_SCHEMA.OPPORTUNITIES
WHERE
STATUS IN ('Won', 'Lost')
GROUP BY
INDUSTRY
ORDER BY
avg_sales_cycle_days DESC;