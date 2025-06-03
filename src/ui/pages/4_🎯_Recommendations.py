import streamlit as st
import sys
import os

# Add the components directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.common import get_common_css, get_sample_data, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="Recommendations",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply common CSS
st.markdown(get_common_css(), unsafe_allow_html=True)

# Add navigation header
add_navigation_header("Recommendations")

# Get sample data
data = get_sample_data()

# Main content
st.markdown('<div class="content-section">', unsafe_allow_html=True)

st.markdown("""
<div class="gtm-section-description">
    <strong>Strategic Recommendations:</strong> Based on the insights and patterns identified, these are prioritized action items designed to address key opportunities and risks in your GTM operations.
</div>
""", unsafe_allow_html=True)

# Recommendations Table
st.subheader("Priority Action Items")

# Initialize session state for owners if not exists
if 'recommendation_owners' not in st.session_state:
    st.session_state.recommendation_owners = {}

recommendations_html = """
<table class="recommendations-table">
    <thead>
        <tr>
            <th>Recommendation</th>
            <th>Reason</th>
            <th>Risk of Inaction</th>
            <th>Effort Level</th>
            <th>Expected Impact</th>
            <th>Owner</th>
        </tr>
    </thead>
    <tbody>
"""

for i, rec in enumerate(data["recommendations"]):
    recommendations_html += f"""
        <tr>
            <td><strong>{rec['recommendation']}</strong></td>
            <td>{rec['reason']}</td>
            <td>{rec['risk_of_inaction']}</td>
            <td>{rec['effort_level']}</td>
            <td>{rec['expected_impact']}</td>
            <td id="owner-{i}">To be assigned</td>
        </tr>
    """

recommendations_html += """
    </tbody>
</table>
"""

st.markdown(recommendations_html, unsafe_allow_html=True)

# Owner Assignment Section
st.subheader("Assign Owners")

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <p style="color: #666; margin-bottom: 1rem;">
        Assign team members to own these recommendations. Clear ownership drives accountability and execution.
    </p>
</div>
""", unsafe_allow_html=True)

# Owner assignment for each recommendation
for i, rec in enumerate(data["recommendations"]):
    st.markdown(f"**{rec['recommendation']}**")
    
    # Use a unique key for each selectbox
    owner_key = f"owner_rec_{i}"
    current_owner = st.session_state.recommendation_owners.get(i, "")
    
    owner = st.selectbox(
        "Assign Owner:",
        ["", "Marketing Team", "Sales Team", "Customer Success", "Product Team", "Revenue Operations", "Sales Development"],
        index=0 if current_owner == "" else ["", "Marketing Team", "Sales Team", "Customer Success", "Product Team", "Revenue Operations", "Sales Development"].index(current_owner) if current_owner in ["", "Marketing Team", "Sales Team", "Customer Success", "Product Team", "Revenue Operations", "Sales Development"] else 0,
        key=owner_key
    )
    
    if owner:
        st.session_state.recommendation_owners[i] = owner
        st.success(f"✅ Assigned to: {owner}")
    
    st.markdown("---")

# Implementation Priority Matrix
st.subheader("Implementation Priority Matrix")

st.markdown("""
<div style="background-color: #fff; border: 1px solid #e3e6f0; border-radius: 10px; padding: 2rem; margin: 2rem 0;">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
        <div>
            <h5 style="color: #dc3545; margin-bottom: 1rem;">🚨 High Priority (Do First)</h5>
            <ul style="color: #666; line-height: 1.6;">
                <li>Reallocate SMB budget to Mid-Market campaigns</li>
                <li>Launch win/loss interviews for FinTech vertical</li>
            </ul>
        </div>
        <div>
            <h5 style="color: #ffc107; margin-bottom: 1rem;">⚠️ Medium Priority (Do Next)</h5>
            <ul style="color: #666; line-height: 1.6;">
                <li>Improve SMB lead scoring and qualification</li>
                <li>Implement PLG playbook expansion</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Timeline and Dependencies
st.subheader("Suggested Timeline")

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">📅 30-Day Sprint</h5>
    <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
        <li><strong>Week 1-2:</strong> Conduct FinTech win/loss interviews</li>
        <li><strong>Week 2-3:</strong> Analyze SMB to Mid-Market budget reallocation plan</li>
        <li><strong>Week 3-4:</strong> Implement lead scoring improvements</li>
        <li><strong>Week 4:</strong> Begin PLG playbook design</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Questions section
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 12px; border: 2px solid #FF8C42;">
    <h4 style="color: #333; margin-bottom: 1rem;">Questions? Ask the AI Assistant!</h4>
    <p style="color: #666; margin-bottom: 1.5rem;">
        Need help prioritizing these recommendations or creating implementation plans? Our AI assistant can help you develop detailed action plans.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Launch AI Assistant", key="launch_ai_recommendations"):
    launch_ai_assistant()

st.markdown("</div>", unsafe_allow_html=True) 