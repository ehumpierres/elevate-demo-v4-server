# Metrics Definitions

- **MRR (Monthly Recurring Revenue):**  
  For the purposes of our analysis, MRR refers to the *Income recorded within a given month* as reported in the `FINANCIAL_DATA` table. Any calculations involving MRR should use the `Income` field as the primary metric.

- **Churn:**  
  Churn represents *lost income* due to account cancellations or downgrades. While churn is not explicitly tracked in the `FINANCIAL_DATA` table, it can be inferred when an account’s income decreases from one month to the next. So instead of calculating gross churn we will have to feel satisfied with net churn. So when a user asks for churn, just calculate the net churn described here. 

  - **Churn Rate** is calculated by dividing the total lost income for a given month by the total income at the beginning of that month (i.e., the end of the prior month). This value should be expressed as a percentage. This is net churn not gross churn (since we don't habe the exact figure of cancelled licenses), but that is ok and iof the user asks for churn rate just give them the net churn as described. 
