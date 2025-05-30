-- What are the primary obstacles preventing POC success?

SELECT 
    o.customer_type,
    p.primary_blocker,
    COUNT(*) as blocker_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(PARTITION BY o.customer_type), 2) as pct_of_failures,
    AVG(p.duration_days) as avg_failed_poc_days
FROM poc_tracker p
JOIN opportunities o ON p.opp_id = o.opp_id
WHERE p.success_flag = 0
GROUP BY o.customer_type, p.primary_blocker
ORDER BY o.customer_type, blocker_count DESC;