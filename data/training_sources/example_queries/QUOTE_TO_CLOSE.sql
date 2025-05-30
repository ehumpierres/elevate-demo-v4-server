-- Which contract terms drive higher win rates and better pricing?

SELECT 
    q.term_months,
    COUNT(DISTINCT q.opp_id) as opportunities_quoted,
    COUNT(CASE WHEN o.status = 'Won' THEN 1 END) as won_deals,
    ROUND(COUNT(CASE WHEN o.status = 'Won' THEN 1 END) * 100.0 / COUNT(DISTINCT q.opp_id), 2) as quote_to_close_pct,
    AVG(CASE WHEN o.status = 'Won' THEN q.discount_pct END) as won_avg_discount,
    AVG(CASE WHEN o.status = 'Won' THEN o.amount END) as won_avg_deal_size
FROM quotes q
JOIN opportunities o ON q.opp_id = o.opp_id
WHERE o.status IN ('Won', 'Lost')
GROUP BY q.term_months
ORDER BY quote_to_close_pct DESC;