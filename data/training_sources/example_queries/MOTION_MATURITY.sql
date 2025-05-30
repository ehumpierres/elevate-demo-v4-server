-- Which motions need immediate attention based on benchmark gaps?

SELECT 
    'Early Funnel - MQL to SQL' as metric_category,
    ROUND(COUNT(l.sql_date) * 100.0 / COUNT(l.mql_date), 2) as current_performance,
    12.0 as mature_benchmark,
    ROUND((COUNT(l.sql_date) * 100.0 / COUNT(l.mql_date)) - 12.0, 2) as gap_to_benchmark,
    CASE 
        WHEN COUNT(l.sql_date) * 100.0 / COUNT(l.mql_date) >= 12 THEN 'At Benchmark'
        WHEN COUNT(l.sql_date) * 100.0 / COUNT(l.mql_date) >= 8 THEN 'Moderate Gap'
        ELSE 'Critical Gap'
    END as priority_level
FROM leads l
WHERE l.mql_date IS NOT NULL

UNION ALL

SELECT 
    'Mid Funnel - POC Success Rate',
    ROUND(AVG(success_flag) * 100, 2),
    75.0,
    ROUND((AVG(success_flag) * 100) - 75.0, 2),
    CASE 
        WHEN AVG(success_flag) * 100 >= 75 THEN 'At Benchmark'
        WHEN AVG(success_flag) * 100 >= 60 THEN 'Moderate Gap'
        ELSE 'Critical Gap'
    END
FROM poc_tracker

UNION ALL

SELECT 
    'Late Funnel - Average Discount',
    ROUND(AVG(q.discount_pct), 2),
    6.0,
    ROUND(AVG(q.discount_pct) - 6.0, 2),
    CASE 
        WHEN AVG(q.discount_pct) <= 6 THEN 'At Benchmark'
        WHEN AVG(q.discount_pct) <= 12 THEN 'Moderate Gap'
        ELSE 'Critical Gap'
    END
FROM quotes q
JOIN opportunities o ON q.opp_id = o.opp_id
WHERE o.status = 'Won'

ORDER BY 
    CASE priority_level 
        WHEN 'Critical Gap' THEN 1 
        WHEN 'Moderate Gap' THEN 2 
        ELSE 3 
    END;