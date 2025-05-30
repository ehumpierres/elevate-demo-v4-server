-- Which lead sources are underperforming and need messaging/ICP refinement?
SELECT 
    lead_source,
    COUNT(*) as total_mqls,
    COUNT(sql_date) as sqls,
    ROUND(COUNT(sql_date) * 100.0 / COUNT(*), 2) as conversion_pct,
    CASE 
        WHEN COUNT(sql_date) * 100.0 / COUNT(*) >= 12 THEN 'Mature'
        WHEN COUNT(sql_date) * 100.0 / COUNT(*) >= 8 THEN 'Developing' 
        ELSE 'Immature'
    END as maturity_status
FROM leads 
WHERE mql_date IS NOT NULL
GROUP BY lead_source
ORDER BY conversion_pct DESC;