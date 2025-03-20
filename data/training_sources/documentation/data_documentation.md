# B2B Correlated Data Documentation

This document provides information about the database schema `B2B_CORRELATED_DATA.CORRELATED_SCHEMA`, highlighting the purpose of each table and the specific values found in key categorical fields.

## Database Overview

The database contains three primary tables that track different aspects of B2B customer relationships:

1. **FINANCIAL_DATA**: Contains transaction records and financial information
2. **OPPORTUNITIES**: Tracks sales opportunities throughout their lifecycle
3. **SUPPORT_TICKETS**: Manages customer support requests and their resolution

These tables are linked primarily through the `CUSTOMER_ID` field, allowing for correlation between customer financial transactions, sales opportunities, and support issues.

---

## FINANCIAL_DATA Table

The FINANCIAL_DATA table stores financial transaction records for B2B customers, including account balances, transaction amounts, and categorization of financial activities.

### Key Field Values:

#### ACCOUNT_TYPE Values:
- "Income"
- "Cost of Goods"
- "Operating Expenses"
- "Net Income"

These values are case sensitive and should be used exactly as shown.

#### INDUSTRY Values:
Common industries include:
- "Technology"
- "Healthcare"
- "Manufacturing"
- "Financial Services"
- "Retail"
- "Education"
- "Other"
- "Telecommunications"

#### CUSTOMER_TYPE Values:
- "Enterprise"
- "Mid-Market"
- "SMB" (Small and Medium Business)
- "Strategic"

### Usage Notes:
- Positive AMOUNT values typically represent credits or income
- Negative AMOUNT values typically represent debits or expenses
- The table contains approximately 7,200 transaction records

---

## OPPORTUNITIES Table

The OPPORTUNITIES table tracks sales opportunities from initial contact through to closure, containing information about potential deals, their status, and associated contact information.

### Key Field Values:

#### STATUS Values:
- "Open"
- "Won"
- "Lost"

These values are case sensitive and should be used exactly as shown.

#### LEAD_SOURCE Values:
- "Phone Inquiry"
- "Search Engine"
- "Web"
- "Direct"
- "Referral"

### Usage Notes:
- The table contains approximately 1,253 opportunity records
- Opportunities with STATUS "Closed Won" represent successful sales
- AMOUNT represents the potential revenue value of the opportunity

---

## SUPPORT_TICKETS Table

The SUPPORT_TICKETS table manages customer support interactions, tracking issues raised by customers, their status, and resolution progress.

### Key Field Values:

#### TICKET_STATUS Values:
- "Open"
- "In Progress"
- "Closed"

These values are case sensitive and should be used exactly as shown.

#### PRIORITY Values:
- "Low"
- "Medium"
- "High"

### Usage Notes:
- The table contains approximately 385 support ticket records
- The DESCRIPTION field can contain lengthy text explaining the issue in detail
- Tickets move through a lifecycle from "Open" to either "In Progress" or "Closed"

---

## Data Relationships and Analysis Tips

### Common Relationships:
- All three tables can be joined using the CUSTOMER_ID field
- FINANCIAL_DATA and OPPORTUNITIES share both CUSTOMER_ID and CUSTOMER_NAME fields
- Analysis can correlate customer support issues with financial transactions or sales opportunities

### Typical Analysis Scenarios:
1. Identify high-value customers with the most financial transactions
2. Correlate support ticket volume with customer financial value
3. Analyze the relationship between successful opportunities and support ticket resolution time
4. Identify industry trends in financial transactions or opportunity closure rates
5. Track customer journey from opportunity to financial transactions

### Data Quality Notes:
- All string values (especially STATUS, ACCOUNT_TYPE, and PRIORITY fields) are case sensitive
- Dates are stored in standard DATE format
- AMOUNT values are stored as FLOAT and may need rounding for display purposes