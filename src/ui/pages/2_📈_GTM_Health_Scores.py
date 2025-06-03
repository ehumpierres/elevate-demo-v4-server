import streamlit as st
import sys
import os

# Add the components directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.common import get_common_css, add_navigation_header, launch_ai_assistant

# Page configuration
st.set_page_config(
    page_title="GTM Health Scores",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply common CSS
st.markdown(get_common_css(), unsafe_allow_html=True)

# Add navigation header
add_navigation_header("GTM Health Scores")

# Main content
st.markdown('<div class="content-section">', unsafe_allow_html=True)

st.markdown("""
<div class="gtm-section-description">
    <strong>GTM Health Scores Overview:</strong> This section provides a comprehensive view of your Go-To-Market performance across functions, motions, and internal operations. Scores are calculated based on efficiency metrics, conversion rates, and strategic alignment indicators.
</div>
""", unsafe_allow_html=True)

# GTM Functions Table
st.subheader("GTM Functions Performance")

gtm_functions_html = """
<table class="gtm-functions-table">
    <thead>
        <tr>
            <th>Function</th>
            <th>Health Score</th>
            <th>Trend</th>
            <th>Confidence</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Marketing</td>
            <td>72</td>
            <td>+3</td>
            <td>Medium</td>
            <td>Strong lead volume but quality issues in SMB - 43% don't match ICP</td>
        </tr>
        <tr>
            <td>Sales Development</td>
            <td>65</td>
            <td>-2</td>
            <td>High</td>
            <td>Conversion rates stable but resource allocation needs optimization</td>
        </tr>
        <tr>
            <td>Sales</td>
            <td>58</td>
            <td>-5</td>
            <td>High</td>
            <td>Mid-Market win rate decline (-9 pts) offsetting Enterprise gains</td>
        </tr>
        <tr>
            <td>Customer Success</td>
            <td>74</td>
            <td>+8</td>
            <td>Low</td>
            <td>Strong expansion revenue (+22%) but limited visibility into metrics</td>
        </tr>
        <tr>
            <td>Support</td>
            <td>69</td>
            <td>+1</td>
            <td>Medium</td>
            <td>Consistent performance with slight efficiency improvements</td>
        </tr>
        <tr>
            <td>Onboarding</td>
            <td>81</td>
            <td>+4</td>
            <td>High</td>
            <td>Highest performing function - strong product stickiness signals</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(gtm_functions_html, unsafe_allow_html=True)

# GTM Motions Table
st.subheader("GTM Motions by Segment")

gtm_motions_html = """
<table class="gtm-motions-table">
    <thead>
        <tr>
            <th>Motion</th>
            <th>Health Score</th>
            <th>Trend</th>
            <th>LTV:CAC</th>
            <th>Win Rate</th>
            <th>Pipeline Velocity</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>SMB</td>
            <td>61</td>
            <td>-1</td>
            <td>2.8:1</td>
            <td>18%</td>
            <td>42 days</td>
        </tr>
        <tr>
            <td>Mid-Market</td>
            <td>75</td>
            <td>-4</td>
            <td>5.9:1</td>
            <td>31%</td>
            <td>67 days</td>
        </tr>
        <tr>
            <td>Enterprise</td>
            <td>84</td>
            <td>+7</td>
            <td>8.2:1</td>
            <td>45%</td>
            <td>124 days</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(gtm_motions_html, unsafe_allow_html=True)

# Internal Functions Table
st.subheader("Internal Functions Performance")

internal_functions_html = """
<table class="internal-functions-table">
    <thead>
        <tr>
            <th>Function</th>
            <th>Health Score</th> 
            <th>Trend</th>
            <th>Key Metric</th>
            <th>Performance</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Data & Analytics</td>
            <td>67</td>
            <td>+2</td>
            <td>Report Accuracy</td>
            <td>94%</td>
            <td>Improved data quality but still gaps in CS metrics visibility</td>
        </tr>
        <tr>
            <td>Sales Operations</td>
            <td>71</td>
            <td>+3</td>
            <td>Process Efficiency</td>
            <td>78%</td>
            <td>Pipeline management improvements showing results</td>
        </tr>
        <tr>
            <td>Marketing Operations</td>
            <td>69</td>
            <td>0</td>
            <td>Campaign ROI</td>
            <td>4.2x</td>
            <td>Stable performance, attribution model updates needed</td>
        </tr>
        <tr>
            <td>Revenue Operations</td>
            <td>73</td>
            <td>+5</td>
            <td>Forecast Accuracy</td>
            <td>91%</td>
            <td>Strong cross-functional coordination driving improvements</td>
        </tr>
    </tbody>
</table>
"""

st.markdown(internal_functions_html, unsafe_allow_html=True)

# Questions section
st.markdown("""
<div style="margin-top: 3rem; padding: 2rem; background-color: #f8f9fa; border-radius: 12px; border: 2px solid #FF8C42;">
    <h4 style="color: #333; margin-bottom: 1rem;">Questions? Ask the AI Assistant!</h4>
    <p style="color: #666; margin-bottom: 1.5rem;">
        Want to dive deeper into these health scores? Ask our AI assistant about specific metrics, trends, or get recommendations for improvement.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🤖 Launch AI Assistant", key="launch_ai_gtm"):
    launch_ai_assistant()

st.markdown("</div>", unsafe_allow_html=True) 