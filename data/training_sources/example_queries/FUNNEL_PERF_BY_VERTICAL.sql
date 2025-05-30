-- Which vertical × segment combinations have the most mature end-to-end motions?
WITH funnel_metrics AS (
    SELECT 
        o.customer_type,
        -- Approximate vertical from product bundle
        CASE 
            WHEN q.product_bundle_code LIKE 'HEALTH%' THEN 'Healthcare'
            WHEN q.product_bundle_code LIKE 'EDU%' THEN 'Education'
            ELSE 'General'
        END as vertical,
        COUNT(DISTINCT l.lead_id) as total_leads,
        COUNT(DISTINCT CASE WHEN l.sql_date IS NOT NULL THEN l.lead_id END) as sqls,
        COUNT(DISTINCT p.poc_id) as pocs_run,
        COUNT(DISTINCT CASE WHEN p.success_flag = 1 THEN p.poc_id END) as successful_pocs,
        COUNT(DISTINCT CASE WHEN o.status = 'Won' THEN o.opp_id END) as won_deals,
        AVG(CASE WHEN o.status = 'Won' THEN q.discount_pct END) as avg_won_discount
    FROM opportunities o
    LEFT JOIN leads l ON o.customer_id = l.customer_id
    LEFT JOIN poc_tracker p ON o.opp_id = p.opp_id
    LEFT JOIN quotes q ON o.opp_id = q.opp_id
    WHERE o.status IN ('Won', 'Lost')
    GROUP BY o.customer_type, vertical
)
SELECT 
    customer_type,
    vertical,
    ROUND(sqls * 100.0 / NULLIF(total_leads, 0), 2) as lead_to_sql_pct,
    ROUND(successful_pocs * 100.0 / NULLIF(pocs_run, 0), 2) as poc_success_pct,
    ROUND(won_deals * 100.0 / NULLIF(sqls, 0), 2) as sql_to_close_pct,
    ROUND(avg_won_discount, 2) as avg_discount_pct,
    CASE 
        WHEN sqls * 100.0 / NULLIF(total_leads, 0) >= 12 
         AND successful_pocs * 100.0 / NULLIF(pocs_run, 0) >= 75 
         AND avg_won_discount <= 6 THEN 'Mature Motion'
        ELSE 'Immature Motion'
    END as motion_maturity
FROM funnel_metrics
ORDER BY motion_maturity DESC, lead_to_sql_pct DESC;
