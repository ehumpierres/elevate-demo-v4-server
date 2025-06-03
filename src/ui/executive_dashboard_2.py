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
import re
import traceback
import json
import httpx
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import AI Assistant components
try:
    from src.companion import Companion
    from config.config import update_model, OPENROUTER_MODEL, OPENROUTER_API_URL, API_TIMEOUT
    from src.llm_api import LlmApi
    from config.persona import get_system_prompt as get_arabella_prompt
    from config.motions_analyst import get_system_prompt as get_motions_analyst_prompt
    from src.ui.vanna_calls import clear_all_caches, test_snowflake_connection
    AI_AVAILABLE = True
except ImportError as e:
    print(f"AI Assistant components not available: {e}")
    AI_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="GTM Health Summary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize AI Assistant session state variables
if AI_AVAILABLE:
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    
    if "ai_user_id" not in st.session_state:
        st.session_state.ai_user_id = None
    
    if "ai_companion" not in st.session_state:
        st.session_state.ai_companion = None
    
    if "ai_loading" not in st.session_state:
        st.session_state.ai_loading = False
    
    if "ai_current_model" not in st.session_state:
        st.session_state.ai_current_model = OPENROUTER_MODEL if 'OPENROUTER_MODEL' in globals() else "openai/gpt-4o-2024-11-20"
    
    if "ai_follow_up_questions" not in st.session_state:
        st.session_state.ai_follow_up_questions = []
    
    if "ai_llm_api" not in st.session_state:
        st.session_state.ai_llm_api = None
    
    if "ai_waiting_for_followup" not in st.session_state:
        st.session_state.ai_waiting_for_followup = False
    
    if "ai_selected_follow_up" not in st.session_state:
        st.session_state.ai_selected_follow_up = None
    
    if "ai_selected_analyst" not in st.session_state:
        st.session_state.ai_selected_analyst = "Sales Motion Strategy Agent"

# AI Assistant helper functions
def fix_revenue_text_spacing(text):
    """Fix spacing issues in revenue text formatting"""
    if not text:
        return text
    
    # Fix "KinMonth" pattern (e.g., "747KinJanuary" -> "747K in January")
    text = re.sub(r'(\d+[KMB])in([A-Za-z]+)', r'\1 in \2', text)
    
    # Fix "K(Month)" pattern (e.g., "747K(Jan)" -> "747K (Jan)")
    text = re.sub(r'(\d+[KMB])\(([A-Za-z]+)\)', r'\1 (\2)', text)
    
    # Fix "Kto" pattern (e.g., "747Kto886K" -> "747K to 886K")
    text = re.sub(r'(\d+[KMB])to(\d+[KMB])', r'\1 to \2', text)
    
    # Fix "Kby" pattern (e.g., "886Kby December" -> "886K by December")
    text = re.sub(r'(\d+[KMB])by([A-Za-z]+)', r'\1 by \2', text)
    
    # Fix no space after "→" symbol
    text = re.sub(r'→([A-Za-z])', r'→ \1', text)
    
    # Fix any missing spaces between parentheses and words
    text = re.sub(r'\)([A-Za-z])', r') \1', text)
    
    return text

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

def generate_follow_up_questions(response):
    """Generate follow-up questions using the LLM API"""
    if not AI_AVAILABLE:
        return []
    
    try:
        if st.session_state.ai_llm_api is None:
            st.session_state.ai_llm_api = LlmApi()
        
        # Create a simple prompt for getting follow-up questions
        prompt = f"Based on this latest response, show me 4 good questions I should be asking next. Format as a numbered list with just the questions:\n\nLatest response: {response}"
        
        # Use the detailed persona as the system prompt to get more relevant business questions
        system_prompt = """You quantify the costs of misalignment between sales, marketing, and customer success teams, including NRR erosion, CAC inflation, cross-sell shortfalls, sales cycle lengthening, and pipeline leakage. You see the danger of operating in functional silos rather than sharing GTM system KPIs & strategies to ensure that the company as a whole is progressing in a healthy manner. 
You avoid linear thinking in understanding problems and finding solutions. You know that a company is a complex ecosystem, and that any decision has second and third order impacts. You can help companies see when linear thinking is causing them to miss something or pursue less effective solutions. You also work to help companies proactively avoid missteps rather than falling into the trap of reacting to fires by constantly masking symptoms rather than finding and fixing root causes at the system level. You help leaders calculate the impact of various decisions on things like efficiency factors, revenue leakage, missing feedback loops, and customer impact decay.
You provide observations on patterns and trends when you see companies heading for common missteps, and you find opportunities to help companies to shift thinking, create stronger GTM leadership alignment, or make different operational decisions that will help them successfully grow. You recognize the importance of communication and alignment across the GTM org, and lean into the importance of not making assumptions, educating teams on the "why" behind decisions, and the value in taking time to do things right to prevent future issues. You also help navigate and address organizational resistance through executive sponsorship, incremental rollouts, and certification programs.
You recommend technology enablement strategies, including CRM customization and predictive analytics tools alignment. You are able to convey the importance of data hygiene, and how companies with accurate data inputs can leverage them to make smarter decisions. 
You establish appropriate KPIs based on company stage, preventing the 19-37% enterprise value erosion that occurs with KPI-maturity misalignment.
You can translate abstract Revenue Architecture concepts into concrete action plans, drawing from case studies like Channable's 22% increase in deal size through outcome-based selling.
When analyzing problems, you apply mathematical rigor, calculating metrics like GTM Efficiency Factor, CAC payback periods, and CLTV:CAC ratios.

You have deep expertise in key metrics that matter at the "Growth" Stage for companies between $5M and $20M ARR and can provide specific benchmarks for SaaS companies:
- Customer Retention Rate: You know that median SaaS companies achieve 80-85% retention, while top quartile companies exceed 90%. This metric reveals product value and customer satisfaction.
- Gross Revenue Retention: You advise that healthy SaaS companies maintain 85-90% (median) to 95%+ (top quartile) GRR, indicating product/service stickiness.
- Net Revenue Retention: You emphasize that successful companies achieve 100-110% (median) to 120%+ (top quartile) NRR, demonstrating customer success effectiveness.
- Customer Acquisition Cost by GTM Channel: You help companies optimize their channel mix, targeting a minimum 1:3 CAC:LTV ratio, with top performers achieving 1:5+.
- Win Rate: You benchmark sales effectiveness at 20-30% (median) to 40%+ (top quartile) win rates, reflecting competitive positioning.
- Expansion Revenue %: You guide companies to target 20-30% of new ARR from existing customers (median), with top performers exceeding 40%.
- LTV:CAC ratio: You emphasize that sustainable business models maintain a company ratio greater than 3:1.
- Sales Velocity: You help companies measure and improve their revenue generation capacity through the formula: Opportunities × win rate × deal size ÷ sales cycle, targeting month-over-month increases.

You understand that shifting from 'grow at all costs' to engineered growth is crucial in the post-2022 economic landscape where investors demand profitability alongside expansion. And you know that many of today's executives built successful careers on the growth at all costs model, and/or by using outdated methodologies & frameworks, so it's important to use data and hard facts to show why a new approach is needed to create viable, healthy companies.

Based on the above expertise, suggest follow-up questions that dive deeper into revenue architecture, metrics alignment, and GTM optimization."""
        
        # Call the API directly with the detailed system prompt
        payload = {
            "model": st.session_state.ai_current_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300
        }
        
        # Use the existing headers from the LlmApi class
        response = httpx.post(
            OPENROUTER_API_URL,
            headers=st.session_state.ai_llm_api.headers,
            json=payload,
            timeout=API_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            suggestions_text = result["choices"][0]["message"]["content"]
            
            # Extract questions from the numbered list
            questions = []
            for line in suggestions_text.split('\n'):
                # Look for numbered lines (1. Question) or bulleted lines (• Question)
                match = re.search(r'(?:\d+\.|\*|\•)\s*(.*?)(?:\?|$)', line)
                if match:
                    question = match.group(1).strip()
                    if not question.endswith('?'):
                        question += '?'
                    questions.append(question)
            
            # Ensure we have exactly 4 questions
            return questions[:4] if len(questions) >= 4 else questions
        else:
            print("WARNING: Unexpected response structure for follow-up questions")
            return []
    except Exception as e:
        print(f"Error generating follow-up questions: {str(e)}")
        traceback.print_exc()
        return []

def handle_follow_up_click(question):
    """Process the selected follow-up question"""
    # Save the selected question for display
    st.session_state.ai_selected_follow_up = question
    # Clear the follow-up questions list
    st.session_state.ai_follow_up_questions = []
    # Process the question
    process_ai_input(question)
    # Force a rerun to update the UI
    st.rerun()

def process_ai_input(user_input):
    """Process user input with data analysis if enabled"""
    if not AI_AVAILABLE:
        st.error("AI Assistant components are not available. Please check your installation.")
        return
    
    # If we're in phase 2 (waiting for follow-up generation after displaying response)
    if st.session_state.ai_waiting_for_followup:
        with st.spinner("Generating follow-up questions..."):
            # Get the latest response from the conversation history
            latest_response = st.session_state.ai_messages[-1]["content"]
            follow_up_questions = generate_follow_up_questions(latest_response)
            st.session_state.ai_follow_up_questions = follow_up_questions
            
            # Reset the waiting flag and selected follow-up
            st.session_state.ai_waiting_for_followup = False
            st.session_state.ai_loading = False
            st.session_state.ai_selected_follow_up = None
        return
        
    # Otherwise, we're in phase 1: process the input and generate a response
    st.session_state.ai_loading = True
    
    # Process the user input through the enhanced Companion (now includes data analysis)
    with st.spinner("AI Assistant is thinking..."):
        # The Companion now handles data analysis automatically
        result = st.session_state.ai_companion.process_message(user_input)
        
        # Handle the new response format
        if isinstance(result, dict) and "response" in result:
            response = result["response"]
            data_analysis = result.get("data_analysis")
        else:
            # Fallback for simple string response (shouldn't happen with new Companion)
            response = str(result)
            data_analysis = None
        
        # Fix spacing issues in revenue text formatting
        response = fix_revenue_text_spacing(response)
    
    # Add the messages to the conversation history
    st.session_state.ai_messages.append({"role": "user", "content": user_input})
    st.session_state.ai_messages.append({"role": "assistant", "content": response})
    
    # If we have data analysis results, store them in the message for display
    if data_analysis:
        st.session_state.ai_messages[-1]["data"] = data_analysis.get("results", [])
        st.session_state.ai_messages[-1]["sql"] = data_analysis.get("sql", "")
        st.session_state.ai_messages[-1]["row_count"] = data_analysis.get("row_count", 0)
        st.session_state.ai_messages[-1]["execution_time"] = data_analysis.get("execution_time_ms", 0)
    
    # Set flag to indicate we need to generate follow-up questions after rendering
    st.session_state.ai_waiting_for_followup = True
    
    # We need to rerun to render the response before generating follow-up questions
    st.rerun()

# Custom CSS for the new dashboard design
st.markdown("""
<style>
    /* Hide sidebar completely - comprehensive approach */
    .css-1d391kg {
        display: none;
    }
    
    /* Additional sidebar hiding selectors */
    .sidebar .sidebar-content {
        display: none !important;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    .css-1d391kg, .css-1lcbmhc, .css-1outpf7, .css-17lntkn {
        display: none !important;
    }
    
    /* Hide any sidebar containers */
    div[data-testid="stSidebar"] {
        display: none !important;
    }
    
    .stSidebar {
        display: none !important;
    }
    
    /* Ensure main content takes full width without sidebar */
    .main .block-container {
        margin-left: 0 !important;
        padding-left: 2rem !important;
        max-width: 100% !important;
    }
    
    /* Remove any sidebar-related margins from main content */
    .stApp > div {
        margin-left: 0 !important;
    }
    
    /* Remove ALL top spacing and margins - most aggressive approach */
    .stApp {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    .stApp > header {
        display: none !important;
    }
    
    .stApp > div {
        margin-top: 0 !important;
        padding-top: 0 !important;
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
    
    /* Remove any default element spacing */
    .element-container:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Force the GTM header to stick to the very top */
    .gtm-header {
        margin-top: 0 !important;
        padding-top: 1rem;
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
    
    /* Chat input submit button specific styling */
    .stChatInput button,
    div[data-testid="stChatInput"] button,
    .stChatInput [data-testid="stButton"] button,
    .st-emotion-cache-1eqiftn button,
    .st-emotion-cache-1eqiftn div[data-testid="stButton"] button {
        background: linear-gradient(90deg, #FF8C42 0%, #FF6B1A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        margin: 0 !important;
        box-shadow: 0 3px 10px rgba(255, 140, 66, 0.4) !important;
        transition: all 0.2s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        width: auto !important;
        min-height: 40px !important;
    }
    
    .stChatInput button:hover,
    div[data-testid="stChatInput"] button:hover,
    .stChatInput [data-testid="stButton"] button:hover,
    .st-emotion-cache-1eqiftn button:hover,
    .st-emotion-cache-1eqiftn div[data-testid="stButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(255, 140, 66, 0.6) !important;
        background: linear-gradient(90deg, #FF6B1A 0%, #FF8C42 100%) !important;
    }
    
    .stChatInput button:focus,
    div[data-testid="stChatInput"] button:focus,
    .stChatInput [data-testid="stButton"] button:focus,
    .st-emotion-cache-1eqiftn button:focus,
    .st-emotion-cache-1eqiftn div[data-testid="stButton"] button:focus {
        box-shadow: 0 5px 15px rgba(255, 140, 66, 0.6) !important;
        outline: none !important;
    }
    
    /* Follow-up question buttons specific styling - white background with dark gray text */
    .stColumns button[key*="ai_follow_up"],
    button[key*="follow_up"],
    .stColumns div[data-testid="stButton"] button[key*="ai_follow_up"],
    .stColumns .stButton button[key*="ai_follow_up"] {
        background: white !important;
        color: #333333 !important;
        border: 2px solid #e0e0e0 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        margin: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        width: 100% !important;
        min-height: auto !important;
    }
    
    .stColumns button[key*="ai_follow_up"]:hover,
    button[key*="follow_up"]:hover,
    .stColumns div[data-testid="stButton"] button[key*="ai_follow_up"]:hover,
    .stColumns .stButton button[key*="ai_follow_up"]:hover {
        background: #f8f9fa !important;
        color: #333333 !important;
        border: 2px solid #cccccc !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    .stColumns button[key*="ai_follow_up"]:focus,
    button[key*="follow_up"]:focus,
    .stColumns div[data-testid="stButton"] button[key*="ai_follow_up"]:focus,
    .stColumns .stButton button[key*="ai_follow_up"]:focus {
        background: white !important;
        color: #333333 !important;
        border: 2px solid #999999 !important;
        outline: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Ultra specific follow-up button override - highest specificity */
    div[data-testid="stColumns"] div[data-testid="stButton"] button[key*="ai_follow_up"],
    .stColumns .stButton > button[key*="ai_follow_up"],
    .element-container .stColumns .stButton > button[key*="ai_follow_up"],
    div.stColumns div[data-testid="stButton"] > button[key*="ai_follow_up"],
    .stApp .stColumns button[key*="ai_follow_up"] {
        background: white !important;
        color: #333333 !important;
        border: 2px solid #e0e0e0 !important;
        padding: 12px 24px !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        margin: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        width: 100% !important;
        min-height: auto !important;
    }
    
    div[data-testid="stColumns"] div[data-testid="stButton"] button[key*="ai_follow_up"]:hover,
    .stColumns .stButton > button[key*="ai_follow_up"]:hover,
    .element-container .stColumns .stButton > button[key*="ai_follow_up"]:hover,
    div.stColumns div[data-testid="stButton"] > button[key*="ai_follow_up"]:hover,
    .stApp .stColumns button[key*="ai_follow_up"]:hover {
        background: #f8f9fa !important;
        color: #333333 !important;
        border: 2px solid #cccccc !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to launch AI Assistant
def launch_ai_assistant():
    """Navigate directly to AI Assistant tab"""
    st.success("🤖 **Ready to chat with the AI Assistant!**")
    st.info("👆 **Click the 'AI Assistant' tab above** to start your conversation with Arabella or the Sales Motion Strategy Agent.")
    st.markdown("""
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
        <p style="margin: 0; color: #856404; font-weight: 500;">
            💡 <strong>What you can do in the AI Assistant:</strong><br>
            • Ask questions about your GTM data and performance<br>
            • Get strategic insights and recommendations<br>
            • Analyze trends and patterns in your business metrics<br>
            • Explore scenario planning and growth strategies
        </p>
    </div>
    """, unsafe_allow_html=True)

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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Executive Summary", 
    "GTM Health Scores", 
    "Insights & Patterns", 
    "Recommendations", 
    "Decision Register",
    "AI Assistant"
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

with tab6:
    st.markdown('<div class="content-section">', unsafe_allow_html=True)
    
    if not AI_AVAILABLE:
        st.error("""
        🚨 **AI Assistant Not Available**
        
        The AI Assistant components could not be loaded. This might be due to:
        - Missing dependencies in requirements.txt
        - Configuration issues with API keys
        - Import errors with the companion modules
        
        Please check your installation and configuration.
        """)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # AI Assistant section
        st.markdown("## Elevate AI Companion")
        st.caption("An intelligent business strategist with integrated data analysis and memory capabilities")
        
        # User identification and setup
        if st.session_state.ai_user_id is None:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Get Started")
                user_id = st.text_input("Enter your username to begin:", key="ai_username")
                
                # Analyst selector
                analyst_options = ["Arabella (Business Architect)", "Sales Motion Strategy Agent"]
                selected_analyst = st.selectbox(
                    "Select AI Assistant:",
                    options=analyst_options,
                    index=analyst_options.index(st.session_state.ai_selected_analyst),
                    key="ai_analyst_selector"
                )
                st.session_state.ai_selected_analyst = selected_analyst
                
                # Start buttons
                col_start1, col_start2 = st.columns([1, 1], gap="small")
                
                # Regular start button
                if col_start1.button("Start Session", key="ai_start_session") and user_id:
                    st.session_state.ai_user_id = user_id
                    st.session_state.ai_companion = Companion(user_id, analyst_type=st.session_state.ai_selected_analyst)
                    st.session_state.ai_llm_api = LlmApi()
                    st.rerun()
                
                # Warm start button
                if col_start2.button("Status Update and Start", key="ai_warm_start") and user_id:
                    st.session_state.ai_user_id = user_id
                    st.session_state.ai_companion = Companion(user_id, analyst_type=st.session_state.ai_selected_analyst)
                    st.session_state.ai_llm_api = LlmApi()
                    # Process initial warm start prompt
                    initial_prompt = "Give me a status of the most recent financial milestones and business risks, and show me the revenue for the last quarter, be succinct"
                    process_ai_input(initial_prompt)
                    st.rerun()
            
            with col2:
                st.markdown("### AI Assistant Features")
                st.markdown("""
                **🎯 Strategic Analysis**
                - Revenue architecture optimization
                - GTM health assessment
                - Market positioning insights
                
                **📊 Data Integration**
                - Real-time Snowflake queries
                - Automated visualizations
                - Performance metrics analysis
                
                **💡 Intelligent Recommendations**
                - Actionable next steps
                - Risk identification
                - Growth opportunities
                """)
        
        else:
            # Active session - show chat interface
            col_header1, col_header2 = st.columns([3, 1])
            
            with col_header1:
                st.write(f"**Active User:** {st.session_state.ai_user_id}")
                st.write(f"**AI Assistant:** {st.session_state.ai_selected_analyst}")
            
            with col_header2:
                if st.button("End Session", key="ai_end_session"):
                    # Reset AI session state
                    st.session_state.ai_user_id = None
                    st.session_state.ai_companion = None
                    st.session_state.ai_messages = []
                    st.session_state.ai_follow_up_questions = []
                    st.session_state.ai_loading = False
                    st.rerun()
            
            # Settings expander
            with st.expander("⚙️ Settings & Data Connection"):
                # Analyst selector - allow switching during active session
                st.subheader("AI Assistant Selection")
                analyst_options = ["Arabella (Business Architect)", "Sales Motion Strategy Agent"]
                selected_analyst = st.selectbox(
                    "Select AI Assistant:",
                    options=analyst_options,
                    index=analyst_options.index(st.session_state.ai_selected_analyst),
                    key="ai_analyst_selector_active"
                )
                
                # Update analyst if changed (reinitialize companion)
                if selected_analyst != st.session_state.ai_selected_analyst:
                    st.session_state.ai_selected_analyst = selected_analyst
                    # Reinitialize companion with new analyst
                    if st.session_state.ai_companion:
                        st.session_state.ai_companion = Companion(st.session_state.ai_user_id, analyst_type=selected_analyst)
                        st.success(f"Switched to {selected_analyst}")
                
                st.divider()
                
                # Model selector
                st.subheader("Model Settings")
                model_options = ["openai/o3", "openai/gpt-4o-2024-11-20"]
                selected_model = st.selectbox(
                    "Select LLM Model:",
                    options=model_options,
                    index=model_options.index(st.session_state.ai_current_model),
                    key="ai_model_selector"
                )
                
                # Update model if changed
                if selected_model != st.session_state.ai_current_model:
                    with st.spinner(f"Switching to {selected_model}..."):
                        update_model(selected_model)
                        st.session_state.ai_current_model = selected_model
                        st.success(f"Model switched to {selected_model}")
                
                st.divider()
                
                # Data connection section
                st.subheader("Data Connection")
                
                # Data connection buttons
                col_test, col_reconnect, col_train = st.columns(3)
                
                # Test Snowflake Connection button
                if col_test.button("Test Snowflake", key="ai_test_snowflake"):
                    with st.spinner("Testing connection..."):
                        try:
                            result = test_snowflake_connection()
                            if isinstance(result, dict) and result.get("success", False):
                                st.success("✅ Connected successfully!")
                                with st.expander("Connection Details"):
                                    st.write(f"**Database:** {result.get('database')}")
                                    st.write(f"**Schema:** {result.get('schema')}")
                                    st.write(f"**Tables:** {result.get('table_count', 0)}")
                            else:
                                st.error("❌ Connection failed")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                # Reconnect button
                if col_reconnect.button("Reconnect", key="ai_reconnect"):
                    with st.spinner("Reconnecting..."):
                        try:
                            clear_all_caches()
                            st.success("✅ Reconnected!")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                # Train model button
                if col_train.button("🎓 Train AI", key="ai_train"):
                    with st.spinner("Training AI model... This may take several minutes."):
                        try:
                            from src.vanna_scripts.vanna_snowflake import VannaSnowflake
                            vanna = VannaSnowflake()
                            training_result = vanna.train()
                            if training_result:
                                st.success("🎉 Training completed!")
                            else:
                                st.error("❌ Training failed!")
                            vanna.close()
                        except Exception as e:
                            st.error(f"❌ Training error: {str(e)}")
            
            # Chat interface
            st.markdown("### 💬 Chat with AI Assistant")
            
            # Display chat messages
            for message in st.session_state.ai_messages:
                with st.chat_message(message["role"]):
                    # Apply fix_revenue_text_spacing to all displayed messages
                    formatted_content = fix_revenue_text_spacing(message["content"])
                    st.write(formatted_content)
                    
                    # If this message has data attached, display it
                    if "data" in message and message["data"]:
                        st.subheader("📊 Data Analysis Results")
                        
                        try:
                            df = pd.DataFrame(message["data"])
                            
                            if not df.empty:
                                # Set row indices to start from 1
                                df.index = np.arange(1, len(df) + 1)
                                
                                # Format and display the data
                                formatted_df = format_numeric_values(df)
                                st.dataframe(formatted_df, use_container_width=True)
                                
                                # Show query metadata
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Rows", message.get("row_count", len(df)))
                                with col2:
                                    st.metric("Time", f"{message.get('execution_time', 0)}ms")
                                with col3:
                                    st.metric("Columns", len(df.columns))
                                
                                # Show the SQL query used
                                if "sql" in message and message["sql"]:
                                    with st.expander("SQL Query"):
                                        st.code(message["sql"], language="sql")
                                
                                # Create visualization
                                create_visualization(df)
                            else:
                                st.info("Query executed successfully but returned no data.")
                                
                        except Exception as e:
                            st.error(f"Error displaying data: {e}")
                            with st.expander("Raw Data"):
                                st.json(message["data"])
            
            # Check if we need to process follow-up questions after displaying the response
            if st.session_state.ai_waiting_for_followup:
                process_ai_input(None)
            
            # FOLLOW-UP QUESTIONS DISABLED - Hidden from UI
            # Display follow-up question bubbles if available
            # if st.session_state.ai_follow_up_questions:
            #     st.write("**💡 Suggested Follow-up Questions:**")
            #     cols = st.columns(len(st.session_state.ai_follow_up_questions))
            #     for i, question in enumerate(st.session_state.ai_follow_up_questions):
            #         if cols[i].button(question, key=f"ai_follow_up_{i}", use_container_width=True):
            #             handle_follow_up_click(question)
            # elif st.session_state.ai_selected_follow_up and st.session_state.ai_loading:
            #     st.write("**Processing Question:**")
            #     st.info(st.session_state.ai_selected_follow_up)
            
            # Chat input area
            user_input = st.chat_input(
                "Ask me anything about business strategy or your data...",
                disabled=st.session_state.ai_loading or st.session_state.ai_waiting_for_followup,
                key="ai_chat_input"
            )
            
            # Process input when submitted
            if user_input:
                process_ai_input(user_input)
                st.rerun()
            
            # Loading indicator
            if st.session_state.ai_loading:
                st.markdown("![Loading](https://i.gifer.com/ZKZx.gif)")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("**GTM Health Summary Dashboard** | Last updated: June 2025 | Version 1.0") 