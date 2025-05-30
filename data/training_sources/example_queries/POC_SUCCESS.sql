-- Can we prove value quickly across different segments?
SELECT 
    o.customer_type,
    CASE 
        WHEN o.amount < 50000 THEN 'Small Deal'
        WHEN o.amount < 150000 THEN 'Medium Deal'
        ELSE 'Large Deal'
    END as deal_size_band,
    COUNT(*) as total_pocs,
    AVG(p.duration_days) as avg_poc_days,
    ROUND(AVG(p.success_flag) * 100, 2) as poc_success_pct,
    COUNT(CASE WHEN p.success_flag = 0 THEN p.primary_blocker END) as failures
FROM poc_tracker p
JOIN opportunities o ON p.opp_id = o.opp_id
GROUP BY o.customer_type, deal_size_band
ORDER BY poc_success_pct DESC;