import streamlit as st
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from components.common import get_common_css, get_sample_data, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="GTM Health Summary",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply common CSS
st.markdown(get_common_css(), unsafe_allow_html=True)

# Add navigation header
add_navigation_header("Executive Summary")

# Get sample data
data = get_sample_data()

# Main content
st.markdown('<div class="content-section">', unsafe_allow_html=True)

# Business summary
st.markdown("""
<div class="business-summary">
    <h3>Business Summary</h3>
    <p>Our GTM operations are showing strong momentum with an overall health score of 68, driven primarily by increased efficiency within the Enterprise sales motion and higher retention in the Mid-Market segment.</p>
    <p>Key areas requiring attention include declining win rates in Mid-Market (-9 pts QoQ) despite high efficiency, and opportunity for improved lead quality in SMB where 43% of leads don't match ICP criteria.</p>
</div>
""", unsafe_allow_html=True)

# Executive Summary Table
st.subheader("Executive Summary Metrics")

summary_data = data["executive_summary_data"]

summary_html = f"""
<table class="summary-table">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Value</th>
            <th>Trend</th>
            <th>Confidence</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Overall GTM Health Score</td>
            <td>{summary_data['Overall GTM Health Score']}</td>
            <td>+{summary_data['Score_Trend']}</td>
            <td>{summary_data['Confidence']}</td>
            <td>{summary_data['Notes']}</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(summary_html, unsafe_allow_html=True)

# Key Takeaways
st.markdown("""
<div class="key-takeaways">
    <h4>Key Takeaways</h4>
</div>
""", unsafe_allow_html=True)

for takeaway in data["key_takeaways"]:
    st.markdown(f"""
    <div class="takeaway-item">
        <span class="takeaway-checkbox">✓</span>
        <div class="takeaway-text">{takeaway}</div>
    </div>
    """, unsafe_allow_html=True)

# Quick Navigation Cards
st.subheader("Explore Your GTM Performance")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #FF8C42;">
        <h4 style="color: #333; margin-bottom: 1rem;">📈 GTM Health Scores</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            Detailed performance metrics across all GTM functions, motions, and internal operations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Health Scores", key="nav_health_scores", use_container_width=True):
        st.switch_page("pages/2_📈_GTM_Health_Scores.py")

with col2:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #FF8C42;">
        <h4 style="color: #333; margin-bottom: 1rem;">💡 Insights & Patterns</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            Strategic insights, trends, and patterns identified in your GTM data with business impact analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Insights", key="nav_insights", use_container_width=True):
        st.switch_page("pages/3_💡_Insights_Patterns.py")

with col3:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #FF8C42;">
        <h4 style="color: #333; margin-bottom: 1rem;">🎯 Recommendations</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            Actionable recommendations with priority rankings, effort levels, and owner assignments.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Recommendations", key="nav_recommendations", use_container_width=True):
        st.switch_page("pages/4_🎯_Recommendations.py")

# Second row of navigation cards
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #FF8C42;">
        <h4 style="color: #333; margin-bottom: 1rem;">📋 Decision Register</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            Track decisions made, their implementation status, observed impact, and lessons learned.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("View Decisions", key="nav_decisions", use_container_width=True):
        st.switch_page("pages/5_📋_Decision_Register.py")

with col5:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #FF8C42;">
        <h4 style="color: #333; margin-bottom: 1rem;">🤖 AI Assistant</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            Chat with expert AI analysts for deeper insights, data analysis, and strategic guidance.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Launch AI Assistant", key="nav_ai_assistant", use_container_width=True):
        st.switch_page("pages/6_🤖_AI_Assistant.py")

with col6:
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #e3e6f0;">
        <h4 style="color: #333; margin-bottom: 1rem;">📊 Quick Stats</h4>
        <p style="color: #666; margin-bottom: 1.5rem;">
            <strong>Overall Health:</strong> 68 (+5)<br>
            <strong>Top Function:</strong> Onboarding (81)<br>
            <strong>Priority Actions:</strong> 3
        </p>
    </div>
    """, unsafe_allow_html=True)

# Questions section
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 12px; border: 2px solid #FF8C42;">
    <h4 style="color: #333; margin-bottom: 1rem;">Questions? Ask the AI Assistant!</h4>
    <p style="color: #666; margin-bottom: 1.5rem;">
        Get deeper insights, analyze trends, or explore specific metrics with our AI-powered assistant. 
        Click the button below to chat with an expert analyst about your GTM performance.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Launch AI Assistant", key="launch_ai_executive_main"):
    st.switch_page("pages/6_🤖_AI_Assistant.py")

# Footer with app info
st.markdown("""
<div style="margin-top: 4rem; padding: 2rem; background-color: #f1f3f6; border-radius: 10px; text-align: center;">
    <h5 style="color: #333; margin-bottom: 1rem;">GTM Health Summary Dashboard</h5>
    <p style="color: #666; margin: 0;">
        Navigate through the sections above to explore your Go-To-Market performance, insights, and recommendations. 
        Use the AI Assistant for real-time analysis and strategic guidance.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) 