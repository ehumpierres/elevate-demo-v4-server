import streamlit as st
import sys
import os

# Add the components directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.common import get_common_css, get_sample_data, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="Insights & Patterns",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply common CSS
st.markdown(get_common_css(), unsafe_allow_html=True)

# Add navigation header
add_navigation_header("Insights & Patterns")

# Get sample data
data = get_sample_data()

# Main content
st.markdown('<div class="content-section">', unsafe_allow_html=True)

st.markdown("""
<div class="gtm-section-description">
    <strong>Key Insights & Patterns:</strong> This section highlights the most important patterns and trends in your GTM data, categorized by their strategic significance. Each insight includes context on why it matters for your business strategy.
</div>
""", unsafe_allow_html=True)

# Insights Table
st.subheader("Strategic Insights Analysis")

insights_html = """
<table class="insights-table">
    <thead>
        <tr>
            <th>What We Observed</th>
            <th>Meaning</th>
            <th>Why It Matters</th>
        </tr>
    </thead>
    <tbody>
"""

for insight in data["insights"]:
    meaning_class = f"meaning-{insight['meaning'].lower().replace(' ', '-')}"
    insights_html += f"""
        <tr>
            <td>{insight['what']}</td>
            <td><span class="{meaning_class}">{insight['meaning']}</span></td>
            <td>{insight['why_it_matters']}</td>
        </tr>
    """

insights_html += """
    </tbody>
</table>
"""

st.markdown(insights_html, unsafe_allow_html=True)

# Additional patterns
st.subheader("Emerging Patterns")

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">🔄 Cross-Functional Trends</h5>
    <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
        <li><strong>Onboarding Excellence:</strong> 81 health score suggests strong product-market fit once customers engage</li>
        <li><strong>Revenue Operations Impact:</strong> +5 trend improvement indicates better cross-functional coordination</li>
        <li><strong>Data Visibility Gaps:</strong> Customer Success showing results but low confidence in measurement</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">📊 Segment Performance Patterns</h5>
    <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
        <li><strong>Enterprise Momentum:</strong> +7 trend with 8.2:1 LTV:CAC showing strong efficiency gains</li>
        <li><strong>Mid-Market Efficiency vs. Conversion:</strong> Highest LTV:CAC but declining win rates signal opportunity</li>
        <li><strong>SMB Volume vs. Quality:</strong> High lead volume but poor fit rates creating resource strain</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">⚡ Leading Indicators</h5>
    <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
        <li><strong>Vertical Expansion Success:</strong> 22% growth in HealthTech suggests replicable playbook</li>
        <li><strong>Pricing Pressure Signals:</strong> Discounting up to 50% may indicate competitive/positioning challenges</li>
        <li><strong>Process Optimization Impact:</strong> Sales Ops improvements (+3) starting to show in pipeline efficiency</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Questions section
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 12px; border: 2px solid #FF8C42;">
    <h4 style="color: #333; margin-bottom: 1rem;">Questions? Ask the AI Assistant!</h4>
    <p style="color: #666; margin-bottom: 1.5rem;">
        Need deeper analysis of these patterns? Our AI assistant can help you explore correlations, identify root causes, and suggest next steps.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Launch AI Assistant", key="launch_ai_insights"):
    launch_ai_assistant()

st.markdown("</div>", unsafe_allow_html=True) 