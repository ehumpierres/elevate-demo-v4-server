import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import webbrowser
import subprocess
import sys
import os

# Page configuration
st.set_page_config(
    page_title="GTM Health Summary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the new dashboard design
st.markdown("""
<style>
    /* Hide sidebar completely */
    .css-1d391kg {
        display: none;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Remove default streamlit spacing */
    .element-container {
        margin-bottom: 0 !important;
    }
    
    .stTabs {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Purple header styling */
    .gtm-header {
        background: linear-gradient(90deg, #8B4AAE 0%, #6B2C7D 100%);
        color: white;
        padding: 0.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 0;
        text-align: left;
    }
    
    .gtm-header h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #f8f9fa;
        border-radius: 0 0 10px 10px;
        padding: 0;
        margin-top: 0;
        margin-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #9e9e9e;
        color: white;
        border-radius: 0;
        padding: 15px 25px;
        margin: 0;
        border: none;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF8C42 !important;
        color: white !important;
    }
    
    /* Tab content area */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 0;
        margin: 0;
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
    
    /* Hide empty content sections */
    .content-section:empty {
        display: none;
    }
    
    /* Business summary styling */
    .business-summary {
        margin-bottom: 2rem;
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
    .summary-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 2rem 0;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e3e6f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .summary-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .summary-table th:last-child {
        border-right: none;
    }
    
    .summary-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .summary-table td:last-child {
        border-right: none;
    }
    
    .summary-table tr:last-child td {
        border-bottom: none;
    }
    
    /* Key takeaways styling */
    .key-takeaways {
        margin-top: 2rem;
    }
    
    .key-takeaways h4 {
        color: #333;
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }
    
    .takeaway-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 0.8rem;
        padding: 0.5rem;
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
        line-height: 1.4;
        flex: 1;
    }
    
    /* AI Assistant button - More Prominent */
    .ai-assistant-button {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%);
        color: white;
        border: none;
        padding: 16px 32px;
        border-radius: 12px;
        font-size: 1.2rem;
        font-weight: 700;
        cursor: pointer;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .ai-assistant-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6);
        background: linear-gradient(90deg, #FF6B1A 0%, #FF8C42 100%);
    }
    
    /* Metrics styling */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        border: 1px solid #e3e6f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-trend {
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .trend-up {
        color: #28a745;
    }
    
    .trend-down {
        color: #dc3545;
    }
    
    .trend-neutral {
        color: #6c757d;
    }
    
    /* Chart containers */
    .chart-container {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Recommendation cards */
    .recommendation-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #FF8C42;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .recommendation-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .recommendation-content {
        color: #666;
        line-height: 1.6;
    }
    
    /* Insight cards */
    .insight-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .insight-warning {
        border-left: 4px solid #ffc107;
    }
    
    .insight-success {
        border-left: 4px solid #28a745;
    }
    
    .insight-danger {
        border-left: 4px solid #dc3545;
    }
    
    /* Decision register table styling */
    .decision-table {
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
    
    .decision-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .decision-table th:last-child {
        border-right: none;
    }
    
    .decision-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .decision-table td:last-child {
        border-right: none;
    }
    
    .decision-table tr:last-child td {
        border-bottom: none;
    }
    
    /* Record Decision button - More Prominent */
    .record-decision-btn {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%);
        color: white;
        border: none;
        padding: 16px 32px;
        border-radius: 12px;
        font-size: 1.2rem;
        font-weight: 700;
        cursor: pointer;
        margin: 2rem 0;
        box-shadow: 0 6px 20px rgba(255, 140, 66, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .record-decision-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6);
        background: linear-gradient(90deg, #FF6B1A 0%, #FF8C42 100%);
    }
    
    /* Recommendations table styling */
    .recommendations-table {
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
    
    .recommendations-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .recommendations-table th:last-child {
        border-right: none;
    }
    
    .recommendations-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .recommendations-table td:last-child {
        border-right: none;
    }
    
    .recommendations-table tr:last-child td {
        border-bottom: none;
    }
    
    .recommendations-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .recommendations-table .recommendation-col {
        font-weight: 600;
        width: 18%;
    }
    
    .recommendations-table .reason-col {
        width: 16%;
    }
    
    .recommendations-table .risk-col {
        width: 16%;
    }
    
    .recommendations-table .effort-col {
        width: 16%;
    }
    
    .recommendations-table .impact-col {
        width: 16%;
    }
    
    .recommendations-table .owner-col {
        width: 18%;
    }
    
    /* Insights table styling */
    .insights-table {
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
    
    .insights-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .insights-table th:last-child {
        border-right: none;
    }
    
    .insights-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
    }
    
    .insights-table td:last-child {
        border-right: none;
    }
    
    .insights-table tr:last-child td {
        border-bottom: none;
    }
    
    .insights-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .insights-table .what-col {
        font-weight: 600;
        width: 30%;
    }
    
    .insights-table .meaning-col {
        width: 15%;
        text-align: center;
    }
    
    .insights-table .why-col {
        width: 55%;
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
    
    /* GTM Functions table styling */
    .gtm-functions-table {
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
    
    .gtm-functions-table th {
        background-color: #f1f3f6;
        padding: 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        font-size: 0.95rem;
    }
    
    .gtm-functions-table th:last-child {
        border-right: none;
    }
    
    .gtm-functions-table td {
        padding: 15px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        vertical-align: top;
        font-size: 0.9rem;
        line-height: 1.5;
        min-height: 50px;
    }
    
    .gtm-functions-table td:last-child {
        border-right: none;
    }
    
    .gtm-functions-table tr:last-child td {
        border-bottom: none;
    }
    
    .gtm-functions-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .gtm-functions-table .function-col {
        font-weight: 600;
        width: 20%;
    }
    
    .gtm-functions-table .score-col {
        width: 15%;
        text-align: center;
    }
    
    .gtm-functions-table .trend-col {
        width: 15%;
        text-align: center;
    }
    
    .gtm-functions-table .confidence-col {
        width: 15%;
        text-align: center;
    }
    
    .gtm-functions-table .notes-col {
        width: 35%;
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
    
    /* GTM Motions table styling */
    .gtm-motions-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 3rem 0 2rem 0;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e3e6f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .gtm-motions-table th {
        background-color: #f1f3f6;
        padding: 12px 8px;
        text-align: center;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        font-size: 0.85rem;
        vertical-align: middle;
    }
    
    .gtm-motions-table th:last-child {
        border-right: none;
    }
    
    .gtm-motions-table td {
        padding: 12px 8px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        text-align: center;
        font-size: 0.85rem;
        line-height: 1.4;
        min-width: 40px;
    }
    
    .gtm-motions-table td:last-child {
        border-right: none;
    }
    
    .gtm-motions-table tr:last-child td {
        border-bottom: none;
    }
    
    .gtm-motions-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .gtm-motions-table .motion-name {
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        width: 120px;
    }
    
    .gtm-motions-table .score-cell {
        font-weight: 600;
        width: 50px;
    }
    
    .gtm-motions-table .trend-cell {
        width: 50px;
    }
    
    /* Header grouping for dual columns */
    .gtm-motions-table .header-group {
        border-bottom: 2px solid #e3e6f0;
    }
    
    /* Internal Functions table styling */
    .internal-functions-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 3rem 0 2rem 0;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e3e6f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .internal-functions-table th {
        background-color: #f1f3f6;
        padding: 12px 10px;
        text-align: center;
        font-weight: 600;
        border-bottom: 2px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        font-size: 0.85rem;
        vertical-align: middle;
        line-height: 1.3;
    }
    
    .internal-functions-table th:last-child {
        border-right: none;
    }
    
    .internal-functions-table td {
        padding: 15px 10px;
        border-bottom: 1px solid #e3e6f0;
        border-right: 1px solid #e3e6f0;
        text-align: center;
        font-size: 0.9rem;
        line-height: 1.4;
        min-height: 50px;
    }
    
    .internal-functions-table td:last-child {
        border-right: none;
    }
    
    .internal-functions-table tr:last-child td {
        border-bottom: none;
    }
    
    .internal-functions-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .internal-functions-table .function-name {
        font-weight: 600;
        text-align: left;
        padding-left: 15px;
        width: 100px;
    }
    
    .internal-functions-table .eval-cell {
        width: 110px;
    }
    
    /* Override Streamlit default button styling */
    .stButton > button,
    button[kind="primary"],
    button[kind="secondary"], 
    .stButton button,
    div[data-testid="stButton"] > button,
    .element-container button {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 16px 32px !important;
        border-radius: 12px !important;
        font-size: 1.2rem !important;
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
    
    .stButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover,
    .stButton button:hover,
    div[data-testid="stButton"] > button:hover,
    .element-container button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6) !important;
        background: linear-gradient(90deg, #FF6B1A 0%, #FF8C42 100%) !important;
    }
    
    .stButton > button:focus,
    button[kind="primary"]:focus,
    button[kind="secondary"]:focus,
    .stButton button:focus,
    div[data-testid="stButton"] > button:focus,
    .element-container button:focus {
        box-shadow: 0 8px 25px rgba(255, 140, 66, 0.6) !important;
        outline: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to launch AI Assistant
def launch_ai_assistant():
    """Launch the holistic UI in a new browser tab"""
    try:
        # Get the current working directory
        current_dir = os.getcwd()
        holistic_ui_path = os.path.join(current_dir, "src", "ui", "holistic_ui.py")
        
        # Check if the file exists
        if os.path.exists(holistic_ui_path):
            # Launch streamlit run command for the holistic UI
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                holistic_ui_path, 
                "--server.port", "8502",  # Use a different port
                "--server.headless", "true"
            ])
            
            # Open the URL in a new browser tab
            import time
            time.sleep(2)  # Give streamlit time to start
            webbrowser.open_new_tab("http://localhost:8502")
            
            st.success("🚀 AI Assistant launched in a new tab!")
        else:
            st.error(f"Could not find holistic_ui.py at {holistic_ui_path}")
    except Exception as e:
        st.error(f"Error launching AI Assistant: {str(e)}")

# Sample data for the dashboard
executive_summary_data = {
    "Overall GTM Health Score": 68,
    "Score_Trend": 5,
    "Confidence": "High",
    "Notes": "The primary elements driving the upward trend are increased efficiency within the Enterprise sales motion & higher retention in MM."
}

key_takeaways = [
    "<strong>🎯 Top 3 Insights:</strong><br>1) Mid-Market segment shows highest efficiency (2.1x LTV vs SMB) but declining win rates (-9 pts QoQ) suggest messaging/positioning misalignment that needs immediate attention.<br>2) Healthcare vertical expansion revenue surged 22% indicating strong product-market fit and successful CS execution - this playbook should be replicated across other verticals.<br>3) Marketing is generating high volume but 43% of SMB leads fail ICP criteria, creating sales inefficiency and inflated CAC.",
    
    "<strong>⚠️ Top 2 Risks:</strong><br>1) Continued Mid-Market win rate decline threatens our most profitable segment and could derail 50% growth targets - requires urgent competitive analysis and sales enablement.<br>2) Heavy discounting (up to 50% off) combined with rising churn suggests pricing pressure and product-market fit gaps in newer verticals that could erode unit economics.",
    
    "<strong>🚀 Top Recommended Actions:</strong><br>1) Reallocate 20% of SMB paid budget to Mid-Market campaigns (potential +$400K monthly pipeline) - see Recommendations tab for details.<br>2) Launch immediate win/loss interviews in FinTech vertical to address compliance feature gaps.<br>3) Implement stricter lead scoring to improve SMB lead quality and reduce sales resource waste.",
    
    "<strong>📈 Additional Trends:</strong><br>Enterprise motion showing efficiency gains driving overall GTM health score improvement (+5). Onboarding function performing strongest (81 score) suggesting good product stickiness once customers are live. Customer Success confidence remains low despite positive retention trends, indicating data/process gaps in measurement."
]

# GTM Health component data
gtm_components = {
    "GTM_Functions": ["Marketing", "Prospecting", "Sales", "Onboarding", "Customer Success", "Account Management"],
    "Score": ["", "", "", "", "", ""],
    "Trend": ["", "", "", "", "", ""],
    "Confidence": ["", "", "", "", "", ""],
    "Notes": ["", "", "", "", "", ""]
}

# Core metrics data
core_metrics = {
    "Metric": ["Monthly Growth Rate", "Net Revenue Retention", "CAC (Overall)", "Win Rate"],
    "Current": ["6.2%", "112%", "$31K", "26%"],
    "Benchmark": ["5-8%", "100-110%", "$25K-$35K", "20-30%"],
    "Status": ["Within Range", "Above Benchmark", "Within Range", "Within Range"]
}

# Recommendations data
recommendations = [
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
]

# Insights data
insights = [
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
]

# Decision Register data
decision_register = [
    {
        "decision": "Shift 20% SMB paid to Mid-Market",
        "month_finalized": "May 2025",
        "reason_goal": "Improve CAC by reallocating budget to higher-efficiency segment",
        "status": "In progress",
        "observed_impact": "CAC ↓ 8% in MM, lead volume flat",
        "next_steps": "Continue to monitor"
    }
]

# Main header
st.markdown("""
<div class="gtm-header">
    <h1>GTM Health Summary</h1>
</div>
""", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Executive Summary", 
    "GTM Health Scores", 
    "Insights & Patterns", 
    "Recommendations", 
    "Decision Register"
])

with tab1:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Business summary section
    st.markdown("""
    <div class="business-summary">
        <h2>Overall State of the Business</h2>
        <p>

**Company Overview & Goals:** Nestani is a SaaS company at $10M ARR serving healthcare, education, manufacturing, and general business markets, with a new CEO targeting aggressive 50% growth following recent private equity backing. Having found success in healthcare, the company is now exploring new verticals that require different sales motions and go-to-market approaches.

**Business Trends:** While existing customer renewals remain strong, the company faces challenges with low new prospect close rates and rising churn, with heavy discounting (up to 50% off) suggesting pricing pressure as they work toward ambitious growth targets.
</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary table
    st.markdown("""
    <table class="summary-table">
        <thead>
            <tr>
                <th></th>
                <th>Score (100=max)</th>
                <th>Trend (from last month)</th>
                <th>Confidence</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Overall GTM Health Score</strong></td>
                <td>68</td>
                <td><span style="color: #28a745;">▲ 5</span></td>
                <td><span style="color: #28a745; font-weight: bold;">High</span></td>
                <td>The primary elements driving the upward trend are increased efficiency within the Enterprise sales motion & higher retention in Mid-market.</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # Key takeaways section
    st.markdown("""
    <div class="key-takeaways">
        <h3>Key Takeaways</h3>
    """, unsafe_allow_html=True)
    
    for takeaway in key_takeaways:
        st.markdown(f"""
        <div class="takeaway-item">
            <div class="takeaway-checkbox">◆</div>
            <div class="takeaway-text">{takeaway}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # AI Assistant button
    if st.button("Questions? Ask the AI Assistant", key="ai_assistant_exec", help="Launch the AI Assistant in a new tab"):
        launch_ai_assistant()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Section title and description
    st.markdown("## GTM Health Scores & GTM Motions")
    
    st.markdown("""
    <div class="gtm-section-description">
        Below are core measures that provide insight on how the health of the GTM System is performing by looking at each GTM function, how each GTM Motion is performing across the end to end journey, and some core GTM metrics.
    </div>
    """, unsafe_allow_html=True)
    
    # GTM Functions table
    st.markdown("""
    <table class="gtm-functions-table">
        <thead>
            <tr>
                <th class="function-col">GTM Functions</th>
                <th class="score-col">Score</th>
                <th class="trend-col">Trend</th>
                <th class="confidence-col">Confidence</th>
                <th class="notes-col">Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="function-col">Marketing</td>
                <td class="score-col"><strong>72</strong></td>
                <td class="trend-col"><span style="color: #28a745;">▲ 4</span></td>
                <td class="confidence-col"><span style="color: #28a745; font-weight: bold;">High</span></td>
                <td class="notes-col">Volume generation is strong, but lead quality needs improvement - 43% of SMB leads don't match ICP criteria</td>
            </tr>
            <tr>
                <td class="function-col">Prospecting</td>
                <td class="score-col"><strong>58</strong></td>
                <td class="trend-col"><span style="color: #28a745;">▲ 7</span></td>
                <td class="confidence-col"><span style="color: #ffc107; font-weight: bold;">Medium</span></td>
                <td class="notes-col">Improving outbound efforts showing momentum, but still underperforming compared to other functions</td>
            </tr>
            <tr>
                <td class="function-col">Sales</td>
                <td class="score-col"><strong>61</strong></td>
                <td class="trend-col"><span style="color: #dc3545;">▼ 2</span></td>
                <td class="confidence-col"><span style="color: #ffc107; font-weight: bold;">Medium</span></td>
                <td class="notes-col">Mid-Market win rates declining (-9 pts QoQ), requiring urgent attention to messaging and competitive positioning</td>
            </tr>
            <tr>
                <td class="function-col">Onboarding</td>
                <td class="score-col"><strong>81</strong></td>
                <td class="trend-col"><span style="color: #28a745;">▲ 3</span></td>
                <td class="confidence-col"><span style="color: #28a745; font-weight: bold;">High</span></td>
                <td class="notes-col">Strongest performing function - excellent time-to-value and customer stickiness once users are live</td>
            </tr>
            <tr>
                <td class="function-col">Customer Success</td>
                <td class="score-col"><strong>64</strong></td>
                <td class="trend-col"><span style="color: #28a745;">▲ 3</span></td>
                <td class="confidence-col"><span style="color: #dc3545; font-weight: bold;">Low</span></td>
                <td class="notes-col">Positive outcomes but measurement gaps affecting confidence - need better data visibility and process standardization</td>
            </tr>
            <tr>
                <td class="function-col">Account Management</td>
                <td class="score-col"><strong>69</strong></td>
                <td class="trend-col"><span style="color: #28a745;">▲ 6</span></td>
                <td class="confidence-col"><span style="color: #ffc107; font-weight: bold;">Medium</span></td>
                <td class="notes-col">Strong expansion revenue growth in HealthTech vertical, but need better coverage in other segments</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # GTM Motions table
    st.markdown("""
    <table class="gtm-motions-table">
        <thead>
            <tr class="header-group">
                <th rowspan="2" class="motion-name">GTM Motion</th>
                <th colspan="2">Overall Score</th>
                <th colspan="2">Lead Quality</th>
                <th colspan="2">Conversion Flow</th>
                <th colspan="2">Sales Efficiency</th>
                <th colspan="2">Time to 1st Impact (Onboarding)</th>
                <th colspan="2">Retention</th>
                <th colspan="2">Expansion</th>
                <th colspan="2">Team Alignment</th>
            </tr>
            <tr>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
                <th class="score-cell">Score</th>
                <th class="trend-cell">Trend</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="motion-name">Inbound PLG</td>
                <td class="score-cell"><strong>74</strong></td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 8</span></td>
                <td class="score-cell">82</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 5</span></td>
                <td class="score-cell">78</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 12</span></td>
                <td class="score-cell">71</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="score-cell">85</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="score-cell">73</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 1</span></td>
                <td class="score-cell">68</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="score-cell">76</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 6</span></td>
            </tr>
            <tr>
                <td class="motion-name">Mid-Market</td>
                <td class="score-cell"><strong>65</strong></td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 3</span></td>
                <td class="score-cell">72</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="score-cell">59</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 9</span></td>
                <td class="score-cell">58</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 5</span></td>
                <td class="score-cell">79</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 1</span></td>
                <td class="score-cell">69</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="score-cell">81</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 7</span></td>
                <td class="score-cell">62</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 2</span></td>
            </tr>
            <tr>
                <td class="motion-name">Enterprise</td>
                <td class="score-cell"><strong>71</strong></td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 5</span></td>
                <td class="score-cell">68</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="score-cell">74</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="score-cell">76</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 8</span></td>
                <td class="score-cell">72</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="score-cell">75</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 6</span></td>
                <td class="score-cell">67</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="score-cell">73</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 7</span></td>
            </tr>
            <tr>
                <td class="motion-name">Channel Partners</td>
                <td class="score-cell"><strong>52</strong></td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 1</span></td>
                <td class="score-cell">48</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 3</span></td>
                <td class="score-cell">55</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="score-cell">49</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 2</span></td>
                <td class="score-cell">58</td>
                <td class="trend-cell"><span style="color: #28a745;">▲ 1</span></td>
                <td class="score-cell">54</td>
                <td class="trend-cell">—</td>
                <td class="score-cell">46</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 4</span></td>
                <td class="score-cell">51</td>
                <td class="trend-cell"><span style="color: #dc3545;">▼ 1</span></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # Category descriptions dropdown
    with st.expander("📋 Category Definitions & Descriptions"):
        st.markdown("""
        **Category - Description**
        
        • **Overall Score** - explain the inputs/formula (match the score on Exec Summary Page)
        
        • **Lead Quality** - % of leads qualified & converting
        
        • **Conversion Flow** - smoothness & time from MQL - SQL - Win
        
        • **Sales Efficiency** - CAC, Payback, AE Productivity
        
        • **Time to 1st Impact** - Time to onboarding + impact achieved?
        
        • **Retention** - $ and logo retention (both)
        
        • **Expansion** - time to expansion, how many expand
        
        • **Team Alignment** - Clarity of roles, handoffs, collaboration, friction
        """)
    
    # Internal Functions evaluation table
    st.markdown("""
    <table class="internal-functions-table">
        <thead>
            <tr class="header-group">
                <th rowspan="2" class="function-name">Internal Function</th>
                <th colspan="2">Overall Score</th>
                <th colspan="2">Coverage & Capacity</th>
                <th colspan="2">Process Execution</th>
                <th colspan="2">Effectiveness & Conversion</th>
                <th colspan="2">Strategic Fit & Targeting</th>
                <th colspan="2">Data Insights & Hygiene</th>
                <th colspan="2">Impact & Outcomes</th>
            </tr>
            <tr>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
                <th class="eval-cell">Score</th>
                <th class="eval-cell">Trend</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="function-name">Marketing</td>
                <td class="eval-cell"><strong>72</strong></td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="eval-cell">78</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="eval-cell">75</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 5</span></td>
                <td class="eval-cell">69</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="eval-cell">68</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 1</span></td>
                <td class="eval-cell">74</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 6</span></td>
                <td class="eval-cell">71</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 4</span></td>
            </tr>
            <tr>
                <td class="function-name">Sales</td>
                <td class="eval-cell"><strong>61</strong></td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 2</span></td>
                <td class="eval-cell">65</td>
                <td class="eval-cell">—</td>
                <td class="eval-cell">58</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 4</span></td>
                <td class="eval-cell">63</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 3</span></td>
                <td class="eval-cell">59</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 5</span></td>
                <td class="eval-cell">62</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 1</span></td>
                <td class="eval-cell">60</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 2</span></td>
            </tr>
            <tr>
                <td class="function-name">CS</td>
                <td class="eval-cell"><strong>64</strong></td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="eval-cell">59</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 2</span></td>
                <td class="eval-cell">68</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="eval-cell">71</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 6</span></td>
                <td class="eval-cell">66</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="eval-cell">58</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 3</span></td>
                <td class="eval-cell">73</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 8</span></td>
            </tr>
            <tr>
                <td class="function-name">Account Mgmt</td>
                <td class="eval-cell"><strong>69</strong></td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 6</span></td>
                <td class="eval-cell">72</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="eval-cell">67</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="eval-cell">74</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 9</span></td>
                <td class="eval-cell">71</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 5</span></td>
                <td class="eval-cell">64</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="eval-cell">76</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 11</span></td>
            </tr>
            <tr>
                <td class="function-name">RevOps</td>
                <td class="eval-cell"><strong>66</strong></td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 2</span></td>
                <td class="eval-cell">63</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 1</span></td>
                <td class="eval-cell">69</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 3</span></td>
                <td class="eval-cell">64</td>
                <td class="eval-cell"><span style="color: #dc3545;">▼ 1</span></td>
                <td class="eval-cell">67</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 4</span></td>
                <td class="eval-cell">70</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 5</span></td>
                <td class="eval-cell">65</td>
                <td class="eval-cell"><span style="color: #28a745;">▲ 2</span></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # Internal Functions evaluation legend
    with st.expander("📊 Internal Functions Evaluation Framework"):
        st.markdown("""
        **Component Definitions & Sample Functional Adaptations**
        
        **Coverage & Capacity**
        - *What it Captures:* Do we have the right people in the right roles, focused on the right areas?
        - *Sample Adaptations:* Sales: CRM coverage, CS: CSM-to-account ratio, Marketing: Org per expansion, RevOps: Time to insight
        
        **Process Execution**
        - *What it Captures:* Are our workflows being followed effectively and consistently?
        - *Sample Adaptations:* Sales: Win rate, Marketing: Conversion flow, CS: NRR by cohort, RevOps: Time to insight
        
        **Effectiveness & Conversion** 
        - *What it Captures:* Are we converting effort into outcomes in a measurable way?
        - *Sample Adaptations:* Sales: Win rate, Marketing: MQL conversion, CS: Expansion flow, RevOps: Predictive churn identification
        
        **Strategic Fit & Targeting**
        - *What it Captures:* Are we working with the right customers/segments/ICP for the motion to succeed?
        - *Sample Adaptations:* Sales: Win rate by ICP, Marketing: ICP attribution, CS: NRR by cohort
        
        **Data Insights & Hygiene**
        - *What it Captures:* Do we have the data, insights, and agility to learn and optimize quickly?
        - *Sample Adaptations:* Sales: New ARR, Marketing: Pipeline $ created, CS: NRR
        
        **Impact & Outcomes**
        - *What it Captures:* Are we driving the right business outcomes (growth, retention, efficiency)?
        - *Sample Adaptations:* Sales: New ARR, Marketing: Pipeline $ created, CS: NRR
        """)
    
    # AI Assistant button
    if st.button("Questions? Ask the AI Assistant", key="ai_assistant_scores"):
        launch_ai_assistant()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Section title
    st.markdown("## Key Insights and Patterns")
    
    # Insights table
    st.markdown("""
    <table class="insights-table">
        <thead>
            <tr>
                <th class="what-col">What</th>
                <th class="meaning-col">Meaning</th>
                <th class="why-col">Why It Matters</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="what-col">Win rates in Mid-Market dropped 9 pts QoQ</td>
                <td class="meaning-col"><span class="meaning-risk">Risk</span></td>
                <td class="why-col">Mid-Market is your highest LTV:CAC segment. A continued decline may signal misalignment in messaging, competitive positioning, or product fit—and threatens efficient growth.</td>
            </tr>
            <tr>
                <td class="what-col">Expansion revenue grew 22%—driven by existing HealthTech customers</td>
                <td class="meaning-col"><span class="meaning-opportunity">Opportunity</span></td>
                <td class="why-col">This signals strong product-market fit and CS execution in a key vertical. Reinforces the case for investing in verticalized success playbooks and product-led upsell strategies.</td>
            </tr>
            <tr>
                <td class="what-col">43% of SMB leads this month did not match ICP criteria</td>
                <td class="meaning-col"><span class="meaning-early-signal">Early Signal</span></td>
                <td class="why-col">Marketing is generating volume, but low-fit leads strain sales resources and lower close rates. Tightening targeting and scoring can reduce CAC and improve sales velocity.</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # AI Assistant button
    if st.button("Questions? Ask the AI Assistant", key="ai_assistant_insights"):
        launch_ai_assistant()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Recommendations table
    st.markdown("""
    <table class="recommendations-table">
        <thead>
            <tr>
                <th class="recommendation-col">Recommendation</th>
                <th class="reason-col">Reason</th>
                <th class="risk-col">Risk of Inaction</th>
                <th class="effort-col">Effort Level</th>
                <th class="impact-col">Expected Impact</th>
                <th class="owner-col">Owner</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="recommendation-col">Reallocate 20% of SMB Paid Budget to Mid-Market Campaigns</td>
                <td class="reason-col">Mid-Market has 2.1x higher LTV than SMB, but is underfunded (only 28% of spend).</td>
                <td class="risk-col">Continued inefficient CAC in SMB; missed growth in high-efficiency segment.</td>
                <td class="effort-col">Medium – requires audience rework + new creative</td>
                <td class="impact-col">High – could lift qualified pipeline by $400K/month</td>
                <td class="owner-col"></td>
            </tr>
            <tr>
                <td class="recommendation-col">Launch Win/Loss Interviews for FinTech Vertical</td>
                <td class="reason-col">Win rates dropped 15 pts; top reason cited = missing compliance features.</td>
                <td class="risk-col">Further revenue loss in a strategic vertical.</td>
                <td class="effort-col">Low – 6–8 calls w/ lost prospects over 2 weeks</td>
                <td class="impact-col">Medium – deeper intel to prioritize roadmap + GTM messaging</td>
                <td class="owner-col"></td>
            </tr>
            <tr>
                <td class="recommendation-col">43% of SMB leads this month did not match ICP criteria</td>
                <td class="reason-col">Trial-to-paid conversion doubled in SMB after PLG playbook implementation.</td>
                <td class="risk-col">Underperformance of Mid-Market + self-serve users; CAC stays flat</td>
                <td class="effort-col">Medium – coordination with product + CS for onboarding flows</td>
                <td class="impact-col">High – likely CAC reduction + lift in ARR from low-touch channel</td>
                <td class="owner-col"></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # AI Assistant button
    if st.button("Questions? Ask the AI Assistant", key="ai_assistant_recommendations"):
        launch_ai_assistant()
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    # Decision register table
    st.markdown("""
    <table class="decision-table">
        <thead>
            <tr>
                <th>Decision</th>
                <th>Month Finalized</th>
                <th>Reason/Goal</th>
                <th>Status</th>
                <th>Observed Impact</th>
                <th>Next Steps</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Shift 20% SMB paid to Mid-Market</td>
                <td>May 2025</td>
                <td>Improve CAC by reallocating budget to higher-efficiency segment</td>
                <td>In progress</td>
                <td>CAC ↓ 8% in MM, lead volume flat</td>
                <td>Continue to monitor</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
    
    # Record a New Decision button
    if st.button("Record a New Decision", key="record_decision", help="Add a new strategic decision to track"):
        st.info("Decision recording form would open here. This would allow you to input:\n\n• Decision details\n• Timeline and rationale\n• Expected outcomes\n• Responsible parties\n• Success metrics")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("**GTM Health Summary Dashboard** | Last updated: June 2025 | Version 1.0") 