-- Query to get the correlation between ticket severity and financial value, and how does this impact future transactions after ticket resolution.
WITH customer_financials AS (
 SELECT
   CUSTOMER_ID,
   SUM(CASE WHEN ACCOUNT_TYPE = 'Income' THEN AMOUNT ELSE 0 END) AS total_income,
   COUNT(DISTINCT CASE WHEN ACCOUNT_TYPE = 'Income' THEN BALANCE_ID END) AS income_transaction_count,
   AVG(CASE WHEN ACCOUNT_TYPE = 'Income' THEN AMOUNT ELSE NULL END) AS avg_income_value
 FROM
   B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA
 GROUP BY
   CUSTOMER_ID
),

ticket_metrics AS (
 SELECT
   CUSTOMER_ID,
   COUNT(*) AS total_tickets,
   SUM(CASE WHEN PRIORITY IN ('High', 'Urgent', 'Critical') THEN 1 ELSE 0 END) AS high_priority_tickets,
   AVG(DATEDIFF('day', CREATED_DATE, UPDATED_DATE)) AS avg_resolution_time,
   MAX(UPDATED_DATE) AS last_ticket_date
 FROM
   B2B_CORRELATED_DATA.CORRELATED_SCHEMA.SUPPORT_TICKETS
 WHERE
   TICKET_STATUS IN ('Resolved', 'Closed')
 GROUP BY
   CUSTOMER_ID
),

post_ticket_transactions AS (
 SELECT
   t.CUSTOMER_ID,
   COUNT(*) AS post_ticket_transaction_count,
   SUM(f.AMOUNT) AS post_ticket_revenue,
   AVG(f.AMOUNT) AS avg_post_ticket_transaction_value
 FROM
   ticket_metrics t
 JOIN
   B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA f ON t.CUSTOMER_ID = f.CUSTOMER_ID
 WHERE
   f.ACCOUNT_TYPE = 'Income'
   AND f.TRANSACTION_DATE > t.last_ticket_date
 GROUP BY
   t.CUSTOMER_ID
)

SELECT
 cf.CUSTOMER_ID,
 f.CUSTOMER_NAME,
 f.INDUSTRY,
 f.CUSTOMER_TYPE,
 cf.total_income,
 cf.income_transaction_count,
 cf.avg_income_value,
 tm.total_tickets,
 tm.high_priority_tickets,
 tm.avg_resolution_time,
 ROUND(tm.total_tickets * 1.0 / cf.income_transaction_count, 4) AS tickets_per_transaction_ratio,
 pt.post_ticket_transaction_count,
 pt.post_ticket_revenue,
 pt.avg_post_ticket_transaction_value,
 ROUND((pt.avg_post_ticket_transaction_value - cf.avg_income_value) / cf.avg_income_value * 100, 2) AS transaction_value_change_pct
FROM
 customer_financials cf
JOIN
 B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA f ON cf.CUSTOMER_ID = f.CUSTOMER_ID
JOIN
 ticket_metrics tm ON cf.CUSTOMER_ID = tm.CUSTOMER_ID
LEFT JOIN
 post_ticket_transactions pt ON cf.CUSTOMER_ID = pt.CUSTOMER_ID
GROUP BY
 cf.CUSTOMER_ID, f.CUSTOMER_NAME, f.INDUSTRY, f.CUSTOMER_TYPE, cf.total_income, cf.income_transaction_count,
 cf.avg_income_value, tm.total_tickets, tm.high_priority_tickets, tm.avg_resolution_time, pt.post_ticket_transaction_count,
 pt.post_ticket_revenue, pt.avg_post_ticket_transaction_value
ORDER BY
 transaction_value_change_pct DESC;  
