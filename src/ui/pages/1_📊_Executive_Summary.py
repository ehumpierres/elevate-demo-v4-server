import streamlit as st
import sys
import os

# Add the components directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.common import get_common_css, get_sample_data, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="Executive Summary",
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

# Business summary section
st.markdown("## Overall State of the Business")

st.markdown("**Company Overview & Goals:** Nestani is a SaaS company at $10M ARR serving healthcare, education, manufacturing, and general business markets, with a new CEO targeting aggressive 50% growth following recent private equity backing. Having found success in healthcare, the company is now exploring new verticals that require different sales motions and go-to-market approaches.")

st.markdown("**Business Trends:** While existing customer renewals remain strong, the company faces challenges with low new prospect close rates and rising churn, with heavy discounting (up to 50% off) suggesting pricing pressure as they work toward ambitious growth targets.")

# Executive Summary Table
summary_data = data["executive_summary_data"]

summary_html = f"""
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
            <td>{summary_data['Overall GTM Health Score']}</td>
            <td><span style="color: #28a745;">▲ {summary_data['Score_Trend']}</span></td>
            <td><span style="color: #28a745; font-weight: bold;">{summary_data['Confidence']}</span></td>
            <td>{summary_data['Notes']}</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(summary_html, unsafe_allow_html=True)

# Key Takeaways
st.markdown("### Key Takeaways")

# Individual takeaway items with diamond bullet points
takeaways_content = [
    {
        "icon": "🎯",
        "title": "Top 3 Insights:",
        "items": [
            "Mid-Market segment shows highest efficiency (2.1x LTV vs SMB) but declining win rates (-9 pts QoQ) suggest messaging/positioning misalignment that needs immediate attention.",
            "Healthcare vertical expansion revenue surged 22% indicating strong product-market fit and successful CS execution - this playbook should be replicated across other verticals.",
            "Marketing is generating high volume but 43% of SMB leads fail ICP criteria, creating sales inefficiency and inflated CAC."
        ]
    },
    {
        "icon": "⚠️",
        "title": "Top 2 Risks:",
        "items": [
            "Continued Mid-Market win rate decline threatens our most profitable segment and could derail 50% growth targets - requires urgent competitive analysis and sales enablement.",
            "Heavy discounting (up to 50% off) combined with rising churn suggests pricing pressure and product-market fit gaps in newer verticals that could erode unit economics."
        ]
    },
    {
        "icon": "🚀",
        "title": "Top Recommended Actions:",
        "items": [
            "Reallocate 20% of SMB paid budget to Mid-Market campaigns (potential +$400K monthly pipeline) - see Recommendations tab for details.",
            "Launch immediate win/loss interviews in FinTech vertical to address compliance feature gaps.",
            "Implement stricter lead scoring to improve SMB lead quality and reduce sales resource waste."
        ]
    },
    {
        "icon": "📈",
        "title": "Additional Trends:",
        "content": "Enterprise motion showing efficiency gains driving overall GTM health score improvement (+5). Onboarding function performing strongest (81 score) suggesting good product stickiness once customers are live. Customer Success confidence remains low despite positive retention trends, indicating data/process gaps in measurement."
    }
]

for takeaway in takeaways_content:
    if "items" in takeaway:
        # For items with numbered lists
        items_html = ""
        for i, item in enumerate(takeaway["items"], 1):
            items_html += f"{i}) {item}<br>"
        
        st.markdown(f"""
        <div class="takeaway-item">
            <div class="takeaway-checkbox">◆</div>
            <div class="takeaway-text">
                <strong>{takeaway['icon']} {takeaway['title']}</strong><br>
                {items_html.rstrip('<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # For single content items
        st.markdown(f"""
        <div class="takeaway-item">
            <div class="takeaway-checkbox">◆</div>
            <div class="takeaway-text">
                <strong>{takeaway['icon']} {takeaway['title']}</strong><br>
                {takeaway['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# AI Assistant button
if st.button("QUESTIONS? ASK THE AI ASSISTANT", key="launch_ai_executive"):
    launch_ai_assistant()

st.markdown("</div>", unsafe_allow_html=True) 