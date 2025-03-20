-- Query to get the average deal size for customer types SMB, Enterprise, or Government. In this case, we're looking at the average deal size for customer types that have won opportunities.
SELECT
CUSTOMER_TYPE,
AVG(AMOUNT) AS average_deal_size
FROM
B2B_CORRELATED_DATA.CORRELATED_SCHEMA.OPPORTUNITIES
WHERE
STATUS = 'Won'
GROUP BY
CUSTOMER_TYPE
ORDER BY
average_deal_size DESC;