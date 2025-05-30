-- Should we refine our SMB/Enterprise segmentation based on deal patterns?

SELECT 
    customer_type,
    COUNT(*) as deal_count,
    MIN(amount) as min_deal_size,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount) as q1_deal_size,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median_deal_size,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount) as q3_deal_size,
    MAX(amount) as max_deal_size,
    AVG(amount) as avg_deal_size,
    STDDEV(amount) as deal_size_stddev,
    -- Check for segmentation gaps
    CASE 
        WHEN STDDEV(amount) / AVG(amount) > 0.5 THEN 'High Variance - Consider Sub-Segments'
        ELSE 'Appropriate Segmentation'
    END as segmentation_recommendation
FROM opportunities 
WHERE status = 'Won' AND amount > 0
GROUP BY customer_type
ORDER BY avg_deal_size DESC;