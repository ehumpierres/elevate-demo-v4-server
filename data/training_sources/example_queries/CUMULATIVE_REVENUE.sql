-- This query ranks all customers by their 2023 income revenue in descending order, showing each customer's total revenue, rank position, cumulative revenue, and the percentage of total revenue represented by the cumulative sum.
SELECT 
    cr.CUSTOMER_ID,
    cr.CUSTOMER_NAME,
    cr.TotalRevenue,
    RANK() OVER (ORDER BY cr.TotalRevenue DESC) AS RevenueRank,
    SUM(cr.TotalRevenue) OVER (ORDER BY cr.TotalRevenue DESC ROWS UNBOUNDED PRECEDING) AS CumulativeRevenue,
    ROUND(100 * SUM(cr.TotalRevenue) OVER (ORDER BY cr.TotalRevenue DESC ROWS UNBOUNDED PRECEDING) / tcr.CompanyTotalRevenue, 2) AS CumulativeRevenuePercentage
FROM 
    (SELECT 
        CUSTOMER_ID,
        CUSTOMER_NAME,
        SUM(AMOUNT) AS TotalRevenue
    FROM 
        B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA
    WHERE 
        ACCOUNT_TYPE = 'Income'
        AND TRANSACTION_DATE BETWEEN '2023-01-01' AND '2023-12-31'
    GROUP BY 
        CUSTOMER_ID, CUSTOMER_NAME) cr,
    (SELECT SUM(AMOUNT) AS CompanyTotalRevenue
    FROM B2B_CORRELATED_DATA.CORRELATED_SCHEMA.FINANCIAL_DATA
    WHERE 
        ACCOUNT_TYPE = 'Income'
        AND TRANSACTION_DATE BETWEEN '2023-01-01' AND '2023-12-31') tcr
ORDER BY 
    RevenueRank;