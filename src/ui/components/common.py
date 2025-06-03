import streamlit as st
import pandas as pd
import numpy as np

def get_common_css():
    """Return the common CSS styling for all pages"""
    return """
<style>
    /* Hide sidebar completely */
    .css-1d391kg {
        display: none;
    }
    
    /* Main container styling - remove all top padding/margin */
    .main .block-container {
        padding-top: 0 !important;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 1rem;
        max-width: 100%;
        margin-top: 0 !important;
    }
    
    /* Remove default streamlit spacing */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    /* Remove any top margins from streamlit */
    .stApp > header {
        display: none;
    }
    
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Purple header styling */
    .gtm-header {
        background: linear-gradient(90deg, #8B4AAE 0%, #6B2C7D 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px 10px 0 0;
        margin-bottom: 0;
        margin-top: 0;
        text-align: left;
    }
    
    .gtm-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }
    
    /* Navigation buttons styling - seamless tabs */
    .nav-buttons {
        background-color: #f8f9fa;
        border-radius: 0 0 10px 10px;
        padding: 0;
        margin: 0 0 1rem 0;
        display: flex;
        gap: 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Individual navigation button styling - seamless tabs */
    .nav-buttons .stButton {
        flex: 1;
        margin: 0 !important;
    }
    
    .nav-buttons .stButton > button {
        background-color: #9e9e9e !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 15px 20px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        margin: 0 !important;
        width: 100% !important;
        height: 50px !important;
        box-shadow: none !important;
        transition: background-color 0.2s ease !important;
        border-right: 1px solid #8e8e8e !important;
    }
    
    /* Remove border from last button */
    .nav-buttons .stButton:last-child > button {
        border-right: none !important;
    }
    
    .nav-buttons .stButton > button:hover {
        background-color: #7e7e7e !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Active/disabled button (current page) */
    .nav-buttons .stButton > button:disabled {
        background-color: #FF8C42 !important;
        color: white !important;
        opacity: 1 !important;
        cursor: default !important;
        border-right: 1px solid #e6752a !important;
    }
    
    /* Content area styling */
    .content-section {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        min-height: 0;
    }
    
    /* Business summary styling */
    .business-summary {
        margin-bottom: 2rem;
    }
    
    .business-summary h2 {
        color: #333;
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    .business-summary h3 {
        color: #333;
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .business-summary p {
        color: #666;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    
    /* Table styling */
    .summary-table, .gtm-functions-table, .gtm-motions-table, .internal-functions-table,
    .insights-table, .recommendations-table, .decision-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 2rem 0;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e3e6f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .summary-table th, .gtm-functions-table th, .gtm-motions-table th, .internal-functions-table th,
    .insights-table th, .recommendations-table th, .decision-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .summary-table th:last-child, .gtm-functions-table th:last-child, .gtm-motions-table th:last-child, 
    .internal-functions-table th:last-child, .insights-table th:last-child, .recommendations-table th:last-child, 
    .decision-table th:last-child {
        border-right: none;
    }
    
    .summary-table td, .gtm-functions-table td, .gtm-motions-table td, .internal-functions-table td,
    .insights-table td, .recommendations-table td, .decision-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .summary-table td:last-child, .gtm-functions-table td:last-child, .gtm-motions-table td:last-child,
    .internal-functions-table td:last-child, .insights-table td:last-child, .recommendations-table td:last-child,
    .decision-table td:last-child {
        border-right: none;
    }
    
    .summary-table tr:last-child td, .gtm-functions-table tr:last-child td, .gtm-motions-table tr:last-child td,
    .internal-functions-table tr:last-child td, .insights-table tr:last-child td, .recommendations-table tr:last-child td,
    .decision-table tr:last-child td {
        border-bottom: none;
    }
    
    /* Key takeaways styling */
    .key-takeaways {
        margin-top: 2rem;
    }
    
    .key-takeaways h3 {
        color: #333;
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    
    .takeaway-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 1rem;
        padding: 0.8rem;
        background-color: #f8f9fa;
        border-radius: 6px;
        border-left: 4px solid #FF8C42;
    }
    
    .takeaway-checkbox {
        margin-right: 1rem;
        margin-top: 0.2rem;
        color: #FF8C42;
        font-size: 1.1rem;
        font-weight: bold;
    }
    
    .takeaway-text {
        color: #555;
        line-height: 1.5;
        flex: 1;
    }
    
    /* AI Assistant button - prominent orange styling */
    .ai-assistant-button {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 16px 32px !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        margin: 2rem 0 !important;
        box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        width: auto !important;
        min-height: auto !important;
    }
    
    /* Override Streamlit default button styling for action buttons */
    .stButton > button:not(.nav-buttons .stButton > button) {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 16px 32px !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
        box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        width: auto !important;
        min-height: auto !important;
    }
    
    .stButton > button:hover:not(.nav-buttons .stButton > button) {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6) !important;
        background: linear-gradient(90deg, #FF6B1A 0%, #FF8C42 100%) !important;
    }
    
    .stButton > button:focus:not(.nav-buttons .stButton > button) {
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6) !important;
        outline: none !important;
    }
    
    /* Follow-up question buttons - transparent styling */
    .stColumns button[key*="follow_up"] {
        background: transparent !important;
        color: #FF8C42 !important;
        border: 2px solid #FF8C42 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        margin: 0.5rem !important;
        box-shadow: none !important;
    }
    
    .stColumns button[key*="follow_up"]:hover {
        background: rgba(255, 140, 66, 0.1) !important;
        transform: none !important;
        box-shadow: 0 2px 8px rgba(255, 140, 66, 0.2) !important;
    }
    
    /* GTM Section description */
    .gtm-section-description {
        color: #666;
        font-size: 1rem;
        line-height: 1.6;
        margin: 1.5rem 0 2rem 0;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #FF8C42;
    }
    
    /* Meaning badges */
    .meaning-risk {
        background-color: #dc3545;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .meaning-opportunity {
        background-color: #28a745;
        color: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .meaning-early-signal {
        background-color: #ffc107;
        color: black;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
"""

def get_sample_data():
    """Return all the sample data used across pages"""
    return {
        "executive_summary_data": {
            "Overall GTM Health Score": 68,
            "Score_Trend": 5,
            "Confidence": "High",
            "Notes": "The primary elements driving the upward trend are increased efficiency within the Enterprise sales motion & higher retention in MM."
        },
        
        "key_takeaways": [
            "<strong>🎯 Top 3 Insights:</strong><br>1) Mid-Market segment shows highest efficiency (2.1x LTV vs SMB) but declining win rates (-9 pts QoQ) suggest messaging/positioning misalignment that needs immediate attention.<br>2) Healthcare vertical expansion revenue surged 22% indicating strong product-market fit and successful CS execution - this playbook should be replicated across other verticals.<br>3) Marketing is generating high volume but 43% of SMB leads fail ICP criteria, creating sales inefficiency and inflated CAC.",
            
            "<strong>⚠️ Top 2 Risks:</strong><br>1) Continued Mid-Market win rate decline threatens our most profitable segment and could derail 50% growth targets - requires urgent competitive analysis and sales enablement.<br>2) Heavy discounting (up to 50% off) combined with rising churn suggests pricing pressure and product-market fit gaps in newer verticals that could erode unit economics.",
            
            "<strong>🚀 Top Recommended Actions:</strong><br>1) Reallocate 20% of SMB paid budget to Mid-Market campaigns (potential +$400K monthly pipeline) - see Recommendations tab for details.<br>2) Launch immediate win/loss interviews in FinTech vertical to address compliance feature gaps.<br>3) Implement stricter lead scoring to improve SMB lead quality and reduce sales resource waste.",
            
            "<strong>📈 Additional Trends:</strong><br>Enterprise motion showing efficiency gains driving overall GTM health score improvement (+5). Onboarding function performing strongest (81 score) suggesting good product stickiness once customers are live. Customer Success confidence remains low despite positive retention trends, indicating data/process gaps in measurement."
        ],
        
        "insights": [
            {
                "what": "Win rates in Mid-Market dropped 9 pts QoQ",
                "meaning": "Risk",
                "why_it_matters": "Mid-Market is your highest LTV:CAC segment. A continued decline may signal misalignment in messaging, competitive positioning, or product fit—and threatens efficient growth."
            },
            {
                "what": "Expansion revenue grew 22%—driven by existing HealthTech customers",
                "meaning": "Opportunity", 
                "why_it_matters": "This signals strong product-market fit and CS execution in a key vertical. Reinforces the case for investing in verticalized success playbooks and product-led upsell strategies."
            },
            {
                "what": "43% of SMB leads this month did not match ICP criteria",
                "meaning": "Early Signal",
                "why_it_matters": "Marketing is generating volume, but low-fit leads strain sales resources and lower close rates. Tightening targeting and scoring can reduce CAC and improve sales velocity."
            }
        ],
        
        "recommendations": [
            {
                "recommendation": "Reallocate 20% of SMB Paid Budget to Mid-Market Campaigns",
                "reason": "Mid-Market has 2.1x higher LTV than SMB, but is underfunded (only 28% of spend).",
                "risk_of_inaction": "Continued inefficient CAC in SMB; missed growth in high-efficiency segment.",
                "effort_level": "Medium – requires audience rework + new creative",
                "expected_impact": "High – could lift qualified pipeline by $400K/month",
                "owner": ""
            },
            {
                "recommendation": "Launch Win/Loss Interviews for FinTech Vertical",
                "reason": "Win rates dropped 15 pts; top reason cited = missing compliance features.",
                "risk_of_inaction": "Further revenue loss in a strategic vertical.",
                "effort_level": "Low – 6–8 calls w/ lost prospects over 2 weeks",
                "expected_impact": "Medium – deeper intel to prioritize roadmap + GTM messaging",
                "owner": ""
            },
            {
                "recommendation": "43% of SMB leads this month did not match ICP criteria",
                "reason": "Trial-to-paid conversion doubled in SMB after PLG playbook implementation.",
                "risk_of_inaction": "Underperformance of Mid-Market + self-serve users; CAC stays flat",
                "effort_level": "Medium – coordination with product + CS for onboarding flows",
                "expected_impact": "High – likely CAC reduction + lift in ARR from low-touch channel",
                "owner": ""
            }
        ],
        
        "decision_register": [
            {
                "decision": "Shift 20% SMB paid to Mid-Market",
                "month_finalized": "May 2025",
                "reason_goal": "Improve CAC by reallocating budget to higher-efficiency segment",
                "status": "In progress",
                "observed_impact": "CAC ↓ 8% in MM, lead volume flat",
                "next_steps": "Continue to monitor"
            }
        ]
    }

def format_numeric_values(df):
    """Format DataFrame numeric values with thousands separators and two decimal places"""
    if df is None or df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    formatted_df = df.copy()
    
    # Process numeric columns
    for col in df.select_dtypes(include=['number']).columns:
        # Format integers without decimal places
        if pd.api.types.is_integer_dtype(df[col]):
            formatted_df[col] = df[col].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
        # Format floats with two decimal places
        else:
            formatted_df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")
    
    return formatted_df

def create_visualization(df):
    """Create a simple visualization of the data using Streamlit's native plotting"""
    if df is None or df.empty:
        return
    
    # Get numeric columns for plotting
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if not numeric_cols:
        st.info("No numeric columns available for visualization.")
        return
    
    # Select a column for x-axis (date-like if available, otherwise first column)
    x_col = None
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower() or "month" in col.lower():
            x_col = col
            break
    
    # If no date-like column found, use the first column
    if x_col is None:
        x_col = df.columns[0]
    
    # Select the first numeric column for y-axis
    y_col = numeric_cols[0]
    
    # Create the chart using Streamlit's native plotting
    st.subheader("Data Visualization")
    st.bar_chart(df, x=x_col, y=y_col)

def add_navigation_header(current_page):
    """Add the common header and navigation to each page"""
    st.markdown("""
    <div class="gtm-header">
        <h1>GTM Health Summary</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Add navigation buttons in tab style
    st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
    cols = st.columns(6)
    
    pages = [
        ("Executive Summary", "pages/1_📊_Executive_Summary.py"),
        ("GTM Health Scores", "pages/2_📈_GTM_Health_Scores.py"),
        ("Insights & Patterns", "pages/3_💡_Insights_Patterns.py"),
        ("Recommendations", "pages/4_🎯_Recommendations.py"),
        ("Decision Register", "pages/5_📋_Decision_Register.py"),
        ("AI Assistant", "pages/6_🤖_AI_Assistant.py")
    ]
    
    for i, (name, path) in enumerate(pages):
        with cols[i]:
            if name == current_page:
                st.button(name, disabled=True, use_container_width=True, key=f"nav_{i}_disabled")
            else:
                if st.button(name, key=f"nav_{i}", use_container_width=True):
                    st.switch_page(path)
    
    st.markdown("</div>", unsafe_allow_html=True)

def launch_ai_assistant():
    """Navigate to AI Assistant page"""
    st.switch_page("pages/6_🤖_AI_Assistant.py") 