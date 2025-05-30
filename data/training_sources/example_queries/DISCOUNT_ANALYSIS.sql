-- Do we command pricing power or are we discounting excessively?
SELECT 
    o.customer_type,
    q.product_bundle_code,
    COUNT(*) as quote_count,
    AVG(q.discount_pct) as avg_discount_pct,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY q.discount_pct) as median_discount,
    COUNT(CASE WHEN o.status = 'Won' THEN 1 END) as won_deals,
    ROUND(COUNT(CASE WHEN o.status = 'Won' THEN 1 END) * 100.0 / COUNT(*), 2) as win_rate_pct,
    CASE 
        WHEN AVG(q.discount_pct) <= 6 THEN 'Mature Pricing'
        WHEN AVG(q.discount_pct) <= 12 THEN 'Developing'
        ELSE 'Immature Pricing'
    END as pricing_maturity
FROM quotes q
JOIN opportunities o ON q.opp_id = o.opp_id
WHERE o.status IN ('Won', 'Lost')
GROUP BY o.customer_type, q.product_bundle_code
ORDER BY avg_discount_pct ASC;