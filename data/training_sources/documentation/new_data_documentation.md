# B2B Sales and Operations Data Documentation

This document provides information about the B2B sales and operations dataset containing six primary data tables that track the complete customer lifecycle from lead generation to ongoing support and financial transactions.

## Database Overview

The database contains six primary tables that track different aspects of B2B customer relationships:

1. **ACCOUNTING_DATA**: Contains financial transaction records and account balances
2. **LEADS**: Tracks lead generation and qualification throughout the sales funnel
3. **OPPORTUNITIES**: Manages sales opportunities from initial contact to closure
4. **POC_TRACKER**: Monitors proof-of-concept implementations and their outcomes
5. **QUOTES**: Stores pricing quotes sent to prospects with product configurations
6. **SUPPORT_TICKETS**: Manages customer support requests and their resolution

These tables are linked primarily through the `CUSTOMER_ID` and `OPP_ID` fields, allowing for comprehensive analysis of the customer journey from initial lead to ongoing support and financial performance.

---

## ACCOUNTING_DATA Table

The ACCOUNTING_DATA table stores financial transaction records for B2B customers, including monthly account balances, revenue recognition, and expense tracking across different account categories.

### Key Field Values:

#### ACCOUNT_TYPE Values:
- "Income"
- "Cost of Goods"
- "Operating Expenses"
- "Net Income"

These values are case sensitive and should be used exactly as shown.

#### INDUSTRY Values:
Common industries include:
- "Healthcare"
- "Education"
- "Manufacturing"
- "Technology"
- "Financial Services"
- "Other"

#### CUSTOMER_TYPE Values:
- "Enterprise"
- "Mid-Market"

### Usage Notes:
- Contains approximately 7,200 financial transaction records
- Transaction dates range from January 2023 to June 2024
- Amount values are stored as FLOAT and represent monthly financial figures
- Each customer typically has 4 records per month (one for each account type)
- Zero amounts may indicate churned customers or inactive periods

---

## LEADS Table

The LEADS table tracks lead generation activities from initial contact through to qualification, containing information about lead sources, qualification dates, and final disposition outcomes.

### Key Field Values:

#### LEAD_SOURCE Values:
- "Cold Outreach"
- "Direct Mail"
- "Content Download"
- "Webinar"
- "Search Engine"
- "Referral"
- "Demo Request"
- "Trade Show"
- "Social Media"
- "Web Form"

#### DISPOSITION_CODE Values:
- "Qualified"
- "Unqualified"
- "Nurture"
- "Bad Data"
- "Duplicate"
- "Recycled"

### Usage Notes:
- Contains approximately 19,500 lead records
- MQL_DATE and SQL_DATE fields may be empty for unqualified leads
- Lead progression: Created → MQL (Marketing Qualified Lead) → SQL (Sales Qualified Lead)
- Multiple leads can exist per customer from different sources and time periods

---

## OPPORTUNITIES Table

The OPPORTUNITIES table tracks sales opportunities from initial contact through to closure, containing information about potential deals, their status, amounts, and associated contact information.

### Key Field Values:

#### STATUS Values:
- "Open"
- "Won"
- "Lost"

These values are case sensitive and should be used exactly as shown.

#### LEAD_SOURCE Values:
- "Direct"
- "Phone Inquiry"
- "Web"
- "Search Engine"
- "Referral"

#### CUSTOMER_TYPE Values:
- "Enterprise"
- "Mid-Market"

### Usage Notes:
- Contains approximately 1,240 opportunity records
- AMOUNT represents the potential revenue value of the opportunity
- Opportunities span from January 2023 to June 2024
- Each opportunity is linked to a specific customer and contact person
- Won opportunities typically convert to recurring revenue in ACCOUNTING_DATA

---

## POC_TRACKER Table

The POC_TRACKER table manages proof-of-concept implementations, tracking their duration, success rates, and primary blocking factors when POCs are unsuccessful.

### Key Field Values:

#### SUCCESS_FLAG Values:
- 1 (Successful POC)
- 0 (Unsuccessful POC)

#### PRIMARY_BLOCKER Values (for unsuccessful POCs):
- "User_Adoption"
- "Resource_Constraints"
- "Missing_Integration"
- "Timeline_Issues"
- "Security_Concerns"
- "Performance_Issues"
- "Budget_Constraints"
- "Technical_Complexity"

### Usage Notes:
- Contains approximately 650 POC records
- Each POC is linked to a specific opportunity via OPP_ID
- DURATION_DAYS is calculated from START_DATE to END_DATE
- PRIMARY_BLOCKER field is empty for successful POCs (SUCCESS_FLAG = 1)
- POC success rate can be calculated by analyzing SUCCESS_FLAG distribution

---

## QUOTES Table

The QUOTES table stores pricing quotes sent to prospects, including product configurations, discount levels, and contract terms offered during the sales process.

### Key Field Values:

#### PRODUCT_BUNDLE_CODE Values:
- "HEALTH_PREMIUM"
- "EDU_STANDARD"
- "CORE_BASIC"

#### TERM_MONTHS Values:
- 12 (Annual contract)
- 24 (Two-year contract)
- 36 (Three-year contract)

### Usage Notes:
- Contains approximately 2,800 quote records
- Each quote is linked to a specific opportunity via OPP_ID
- LIST_PRICE represents the full price before discounts
- DISCOUNT_PCT shows the percentage discount applied (0-50% range typical)
- Multiple quotes per opportunity are common as negotiations progress
- Product bundles align with customer industries (HEALTH for Healthcare, EDU for Education)

---

## SUPPORT_TICKETS Table

The SUPPORT_TICKETS table manages customer support interactions, tracking issues raised by customers, their priority levels, status, and resolution progress.

### Key Field Values:

#### STATUS Values:
- "Open"
- "In Progress"
- "Closed"
- "Resolved"

These values are case sensitive and should be used exactly as shown.

#### PRIORITY Values:
- "Low"
- "Medium"
- "High"

### Usage Notes:
- Contains approximately 600 support ticket records
- Tickets move through lifecycle: Open → In Progress → Resolved/Closed
- SUBJECT field contains brief issue description
- DESCRIPTION field can contain lengthy text explaining the issue in detail
- Each ticket is assigned to a support team member via ASSIGNEE_NAME
- Support ticket volume can indicate customer health and product issues

---

## Data Relationships and Analysis Tips

### Common Relationships:
- All tables can be joined using CUSTOMER_ID for complete customer view
- OPPORTUNITIES and POC_TRACKER link via OPP_ID to track deal progression
- OPPORTUNITIES and QUOTES link via OPP_ID to analyze pricing strategies
- LEADS can be correlated with OPPORTUNITIES through CUSTOMER_ID and date ranges

### Typical Analysis Scenarios:
1. **Lead-to-Revenue Analysis**: Track lead sources through opportunities to closed revenue
2. **POC Success Factors**: Analyze which factors contribute to successful proof-of-concepts
3. **Customer Health Scoring**: Combine support ticket volume with financial performance
4. **Pricing Optimization**: Analyze quote acceptance rates by discount levels and product bundles
5. **Churn Prediction**: Monitor account activity in ACCOUNTING_DATA combined with support patterns

### Data Quality Notes:
- All string values (especially STATUS, PRIORITY, and categorical fields) are case sensitive
- Dates are stored in standard YYYY-MM-DD format
- Amount and price values are stored as FLOAT and may need rounding for display
- Some description fields may be empty - this is normal data variance
- Customer names may have slight variations (e.g., "Ltd." vs "Limited") - use CUSTOMER_ID for reliable joins

---

# Metrics Definitions

- **Lead Conversion Rate:**  
  The percentage of leads that progress from initial creation to qualified status. Calculate by dividing leads with DISPOSITION_CODE "Qualified" by total leads.

- **Opportunity Win Rate:**  
  The percentage of opportunities that result in closed-won deals. Calculate by dividing opportunities with STATUS "Won" by total closed opportunities (Won + Lost).

- **POC Success Rate:**  
  The percentage of proof-of-concepts that are successful. Calculate by dividing POCs with SUCCESS_FLAG = 1 by total POCs.

- **Average Deal Size:**  
  The mean value of won opportunities. Calculate by averaging the AMOUNT field for opportunities with STATUS "Won".

- **Customer Lifetime Value (CLV):**  
  For CLV calculations, use the "Income" entries in ACCOUNTING_DATA summed over the customer's active period.

- **Support Ticket Resolution Time:**  
  Calculate the average time between CREATED_DATE and UPDATED_DATE for tickets with STATUS "Closed" or "Resolved".

- **Quote-to-Close Rate:**  
  The percentage of sent quotes that result in won opportunities. Requires joining QUOTES and OPPORTUNITIES tables on OPP_ID. 