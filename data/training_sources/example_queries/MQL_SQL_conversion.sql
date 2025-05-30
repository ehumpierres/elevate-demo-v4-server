-- Which customer segments and lead sources are delivering qualified pipeline most efficiently?
SELECT 
    o.customer_type,
    l.lead_source,
    COUNT(*) as total_leads,
    COUNT(l.mql_date) as mqls,
    COUNT(l.sql_date) as sqls,
    ROUND(COUNT(l.sql_date) * 100.0 / COUNT(l.mql_date), 2) as mql_to_sql_pct,
    ROUND(COUNT(l.mql_date) * 100.0 / COUNT(*), 2) as lead_to_mql_pct
FROM leads l
JOIN opportunities o ON l.customer_id = o.customer_id
WHERE l.mql_date IS NOT NULL
GROUP BY o.customer_type, l.lead_source
ORDER BY mql_to_sql_pct DESC;