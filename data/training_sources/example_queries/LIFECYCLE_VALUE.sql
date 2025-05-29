-- Query to get the customer lifecycle value across different segments, from initial opportunity to recurring transactions, and how do support experiences impact that journey.
WITH customer_journey AS (
  SELECT
    f.CUSTOMER_ID,
    f.CUSTOMER_NAME,
    f.INDUSTRY,
    f.CUSTOMER_TYPE,
    MIN(o.OPEN_DATE) AS first_opportunity_date,
    MIN(CASE WHEN o.STATUS = 'Closed Won' THEN o.CLOSE_DATE ELSE NULL END) AS first_win_date,
    MIN(f.TRANSACTION_DATE) AS first_transaction_date,
    MAX(f.TRANSACTION_DATE) AS last_transaction_date,
    DATEDIFF('day', MIN(CASE WHEN o.STATUS = 'Closed Won' THEN o.CLOSE_DATE ELSE NULL END), MAX(f.TRANSACTION_DATE)) AS customer_tenure_days
  FROM
    DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA f
  JOIN
    DEMO_V4.CORRELATED_SCHEMA.OPPORTUNITIES o ON f.CUSTOMER_ID = o.CUSTOMER_ID
  GROUP BY
    f.CUSTOMER_ID, f.CUSTOMER_NAME, f.INDUSTRY, f.CUSTOMER_TYPE
),

financial_metrics AS (
  SELECT
    CUSTOMER_ID,
    COUNT(*) AS total_transactions,
    SUM(CASE WHEN ACCOUNT_TYPE = 'Income' THEN AMOUNT ELSE 0 END) AS total_revenue,
    SUM(CASE WHEN ACCOUNT_TYPE = 'Expense' THEN AMOUNT ELSE 0 END) AS total_expenses,
    SUM(CASE WHEN ACCOUNT_TYPE = 'Income' THEN AMOUNT ELSE 0 END) - SUM(CASE WHEN ACCOUNT_TYPE = 'Expense' THEN AMOUNT ELSE 0 END) AS net_value,
    COUNT(DISTINCT DATE_TRUNC('month', TRANSACTION_DATE)) AS active_months
  FROM
    DEMO_V4.CORRELATED_SCHEMA.FINANCIAL_DATA
  GROUP BY
    CUSTOMER_ID
),

opportunity_metrics AS (
  SELECT
    CUSTOMER_ID,
    COUNT(*) AS total_opportunities,
    COUNT(CASE WHEN STATUS = 'Closed Won' THEN 1 END) AS won_opportunities,
    SUM(CASE WHEN STATUS = 'Closed Won' THEN AMOUNT ELSE 0 END) AS total_opportunity_value,
    ROUND(COUNT(CASE WHEN STATUS = 'Closed Won' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS win_rate
  FROM
    DEMO_V4.CORRELATED_SCHEMA.OPPORTUNITIES
  GROUP BY
    CUSTOMER_ID
),

support_metrics AS (
  SELECT
    CUSTOMER_ID,
    COUNT(*) AS total_tickets,
    COUNT(CASE WHEN PRIORITY IN ('High', 'Urgent', 'Critical') THEN 1 END) AS high_priority_tickets,
    AVG(DATEDIFF('day', CREATED_DATE, UPDATED_DATE)) AS avg_resolution_time,
    COUNT(CASE WHEN TICKET_STATUS IN ('Resolved', 'Closed') THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS resolution_rate
  FROM
    DEMO_V4.CORRELATED_SCHEMA.SUPPORT_TICKETS
  GROUP BY
    CUSTOMER_ID
)

SELECT
  cj.CUSTOMER_ID,
  cj.CUSTOMER_NAME,
  cj.INDUSTRY,
  cj.CUSTOMER_TYPE,
  cj.first_opportunity_date,
  cj.first_win_date,
  cj.first_transaction_date,
  cj.last_transaction_date,
  cj.customer_tenure_days,
  fm.total_transactions,
  fm.total_revenue,
  fm.total_expenses,
  fm.net_value,
  fm.active_months,
  ROUND(fm.total_revenue / NULLIF(fm.active_months, 0), 2) AS monthly_revenue,
  ROUND(fm.net_value / NULLIF(cj.customer_tenure_days, 0) * 30, 2) AS monthly_net_value,
  om.total_opportunities,
  om.won_opportunities,
  om.win_rate,
  om.total_opportunity_value,
  sm.total_tickets,
  sm.high_priority_tickets,
  sm.avg_resolution_time,
  sm.resolution_rate,
  ROUND(fm.total_revenue / NULLIF(sm.total_tickets, 0), 2) AS revenue_per_ticket,
  CASE
    WHEN cj.customer_tenure_days > 365 THEN 'Long-term (>1 year)'
    WHEN cj.customer_tenure_days > 180 THEN 'Medium-term (6-12 months)'
    ELSE 'Short-term (<6 months)'
  END AS tenure_segment
FROM
  customer_journey cj
JOIN
  financial_metrics fm ON cj.CUSTOMER_ID = fm.CUSTOMER_ID
JOIN
  opportunity_metrics om ON cj.CUSTOMER_ID = om.CUSTOMER_ID
LEFT JOIN
  support_metrics sm ON cj.CUSTOMER_ID = sm.CUSTOMER_ID
ORDER BY
  monthly_net_value DESC, customer_tenure_days DESC;
