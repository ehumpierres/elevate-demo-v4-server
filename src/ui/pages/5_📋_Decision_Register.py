import streamlit as st
import sys
import os

# Add the components directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.common import get_common_css, get_sample_data, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="Decision Register",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply common CSS
st.markdown(get_common_css(), unsafe_allow_html=True)

# Add navigation header
add_navigation_header("Decision Register")

# Get sample data
data = get_sample_data()

# Main content
st.markdown('<div class="content-section">', unsafe_allow_html=True)

st.markdown("""
<div class="gtm-section-description">
    <strong>Decision Register:</strong> Track the decisions made based on previous recommendations, their implementation status, observed impact, and next steps. This creates accountability and learning from past actions.
</div>
""", unsafe_allow_html=True)

# Decision Register Table
st.subheader("Active Decisions & Outcomes")

decision_html = """
<table class="decision-table">
    <thead>
        <tr>
            <th>Decision Made</th>
            <th>Month Finalized</th>
            <th>Reason/Goal</th>
            <th>Status</th>
            <th>Observed Impact</th>
            <th>Next Steps</th>
        </tr>
    </thead>
    <tbody>
"""

for decision in data["decision_register"]:
    status_color = "green" if "progress" in decision["status"].lower() else "orange"
    decision_html += f"""
        <tr>
            <td><strong>{decision['decision']}</strong></td>
            <td>{decision['month_finalized']}</td>
            <td>{decision['reason_goal']}</td>
            <td><span style="color: {status_color}; font-weight: 600;">{decision['status']}</span></td>
            <td>{decision['observed_impact']}</td>
            <td>{decision['next_steps']}</td>
        </tr>
    """

decision_html += """
    </tbody>
</table>
"""

st.markdown(decision_html, unsafe_allow_html=True)

# Add New Decision Section
st.subheader("Log New Decision")

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <p style="color: #666; margin-bottom: 1rem;">
        Capture new decisions as they're made to maintain a clear record of strategic choices and their outcomes.
    </p>
</div>
""", unsafe_allow_html=True)

# Simple form for new decisions
with st.form("new_decision_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        new_decision = st.text_input("Decision Made")
        month_finalized = st.text_input("Month Finalized", placeholder="e.g., June 2025")
        reason_goal = st.text_area("Reason/Goal", height=100)
    
    with col2:
        status = st.selectbox("Status", ["Planning", "In progress", "Completed", "Paused", "Cancelled"])
        observed_impact = st.text_area("Observed Impact (if any)", height=100)
        next_steps = st.text_area("Next Steps", height=100)
    
    submitted = st.form_submit_button("Add Decision")
    
    if submitted and new_decision:
        st.success(f"✅ Decision '{new_decision}' has been logged to the register.")
        st.info("Note: In a production environment, this would be saved to your database.")

# Decision Analytics
st.subheader("Decision Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Decisions Tracked",
        value="1",
        delta="New tracking system"
    )

with col2:
    st.metric(
        label="In Progress",
        value="1",
        delta="100% of decisions"
    )

with col3:
    st.metric(
        label="Completed This Quarter",
        value="0",
        delta="Tracking started recently"
    )

# Impact Tracking
st.subheader("Impact Summary")

st.markdown("""
<div style="background-color: #fff; border: 1px solid #e3e6f0; border-radius: 10px; padding: 2rem; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">📊 Current Period Impact</h5>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
        <div>
            <h6 style="color: #28a745; margin-bottom: 0.5rem;">✅ Positive Outcomes</h6>
            <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
                <li>Mid-Market CAC reduction: -8%</li>
                <li>Lead volume maintained during reallocation</li>
            </ul>
        </div>
        <div>
            <h6 style="color: #ffc107; margin-bottom: 0.5rem;">⚠️ Areas to Monitor</h6>
            <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
                <li>SMB pipeline impact from budget shift</li>
                <li>Time to see full MM campaign results</li>
            </ul>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Learning and Insights
st.subheader("Key Learnings")

st.markdown("""
<div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; margin: 2rem 0;">
    <h5 style="color: #333; margin-bottom: 1rem;">💡 What We've Learned</h5>
    <ul style="color: #666; line-height: 1.6; margin-left: 1rem;">
        <li><strong>Budget Reallocation Speed:</strong> Mid-Market campaigns show faster efficiency gains than expected</li>
        <li><strong>Lead Quality Impact:</strong> Reducing SMB spend improved overall lead quality metrics</li>
        <li><strong>Cross-Team Coordination:</strong> Marketing and Sales alignment critical for successful transitions</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Questions section
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 12px; border: 2px solid #FF8C42;">
    <h4 style="color: #333; margin-bottom: 1rem;">Questions? Ask the AI Assistant!</h4>
    <p style="color: #666; margin-bottom: 1.5rem;">
        Need help analyzing decision outcomes or planning next steps? Our AI assistant can help you evaluate the impact of your decisions and recommend adjustments.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Launch AI Assistant", key="launch_ai_decisions"):
    launch_ai_assistant()

st.markdown("</div>", unsafe_allow_html=True) 