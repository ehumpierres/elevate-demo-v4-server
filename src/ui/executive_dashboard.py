import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Executive Brief",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .trend-up {
        color: #28a745;
    }
    .trend-down {
        color: #dc3545;
    }
    .header-container {
        padding: 1.5rem;
        background-color: #f1f3f6;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .confidence-high {
        color: #28a745;
        font-weight: bold;
    }
    .confidence-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .confidence-low {
        color: #dc3545;
        font-weight: bold;
    }
    .card {
        border-radius: 5px;
        padding: 1.5rem;
        background-color: white;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1.5rem;
    }
    .table-container {
        overflow-x: auto;
        margin-bottom: 1.5rem;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #f1f3f6;
        padding: 12px;
        text-align: left;
    }
    td {
        padding: 12px;
        border-bottom: 1px solid #e3e6f0;
    }
    h3 {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    h4 {
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    /* Fix for plotly charts */
    .js-plotly-plot .plotly .main-svg {
        overflow: visible !important;
    }
    /* Add spacing between sections */
    .section-spacer {
        margin-top: 2rem;
    }
    /* Improve sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }
    /* Fix for stacked content */
    .stPlotlyChart {
        margin-top: 2rem;
        margin-bottom: 2rem;
        position: relative;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def format_trend(trend_value):
    """Format trend with arrow and color"""
    if trend_value > 0:
        return f'<span class="trend-up">▲ {abs(trend_value)}</span>'
    elif trend_value < 0:
        return f'<span class="trend-down">▼ {abs(trend_value)}</span>'
    else:
        return f'<span>→ {trend_value}</span>'

def format_confidence(confidence):
    """Format confidence with color"""
    if confidence == "High":
        return f'<span class="confidence-high">● High</span>'
    elif confidence == "Medium":
        return f'<span class="confidence-medium">● Medium</span>'
    else:
        return f'<span class="confidence-low">● Low</span>'

# Data for the dashboard (normally this would come from a database)
component_data = {
    "Component": ["Revenue Health", "Sales Execution", "Marketing Effectiveness", "Customer Success", "Revenue Operations"],
    "Score": [72, 58, 61, 81, 64],
    "Trend": [4, 7, -2, 3, 3],
    "Confidence": ["High", "Medium", "Medium", "High", "Low"]
}

metrics_data = {
    "Key Metric": ["Monthly Growth Rate", "Net Revenue Retention", "CAC (Overall)", "Win Rate", "Sales Cycle", "Pipeline Coverage", "Gross Revenue Retention"],
    "Current": ["6.2%", "112%", "$31K", "26%", "72 days", "2.8x", "92%"],
    "vs Benchmark": ["5-8%", "100-110%", "$25K-$35K", "20-30%", "60-90 days", "3-4x", "85-90%"],
    "Trend": [-0.3, 3, 4, 3, -8, -0.3, 1],
    "Confidence": ["High", "High", "Medium", "Medium", "High", "Medium", "High"]
}

# Convert to DataFrames
df_components = pd.DataFrame(component_data)
df_metrics = pd.DataFrame(metrics_data)

# Create recommendations data
recommendations = [
    {
        "title": "Improve Sales Process Documentation",
        "details": [
            "Standardize opportunity stage definitions to address inconsistent CRM data",
            "Implement validation rules to improve data quality",
            "Create sales process playbook for key customer segments",
            "Owner: VP Sales & Revenue Operations",
            "Expected Impact: More reliable forecasting, improved pipeline quality",
            "Success Metrics: >90% opportunity data compliance within 60 days, improved forecast accuracy"
        ]
    },
    {
        "title": "Evaluate Marketing Channel Effectiveness",
        "details": [
            "Analyze performance of current marketing channels",
            "Shift resources from underperforming to high-performing channels",
            "Develop more targeted messaging for core segments",
            "Owner: VP Marketing",
            "Expected Impact: Lower CAC, improved lead quality",
            "Success Metrics: 10% reduction in overall CAC within 90 days, higher MQL-to-SQL conversion"
        ]
    }
]

# Create insights data
insights = [
    {
        "title": "Overall CAC Increasing",
        "status": "warning",
        "details": [
            "Customer acquisition cost increased 15% QoQ to $31K per customer",
            "Current payback: 12.8 months (benchmark: 12-18 months)",
            "Confidence: Medium - Based on aggregated sales and marketing spend allocation",
            "Initial data suggests higher costs in enterprise segment, but further data needed"
        ]
    },
    {
        "title": "Retention Strength",
        "status": "success",
        "details": [
            "Net Revenue Retention at 112% (benchmark: 100-110%)",
            "Gross Revenue Retention at 92% (benchmark: 85-90%)",
            "Confidence: High - Based on 18 months of consistent renewal data",
            "Strong indicator of product value and customer satisfaction"
        ]
    },
    {
        "title": "Pipeline Coverage Gap",
        "status": "warning",
        "details": [
            "Current pipeline coverage ratio: 2.8x (benchmark: 3-4x)",
            "Declined for third consecutive month (from 3.4x)",
            "Confidence: Medium - Based on CRM opportunity data with inconsistent stage definitions",
            "Creates risk for achieving Q3 targets"
        ]
    }
]

# Data confidence data
confidence_data = {
    "High": [
        "Revenue metrics from financial systems",
        "Customer retention data",
        "Sales cycle length"
    ],
    "Medium": [
        "Marketing attribution data",
        "Opportunity pipeline data",
        "Win/loss categorization"
    ],
    "Low": [
        "Customer segmentation data",
        "Sales activity tracking",
        "Customer usage patterns"
    ]
}

# BEGIN DASHBOARD UI
st.markdown('<div class="header-container">', unsafe_allow_html=True)
st.title("Executive Brief")
st.markdown("### Revenue Performance & Growth Analysis")
st.markdown("</div>", unsafe_allow_html=True)

# Dashboard tabs
tab1, tab2, tab3 = st.tabs(["Component Performance", "Key Metrics", "Recommendations"])

with tab1:
    # Left column: Component overview table
    st.markdown("<h3>Performance Components</h3>", unsafe_allow_html=True)
    
    # Create component performance table
    table_html = "<div class='table-container'><table>"
    table_html += "<tr><th>Component</th><th>Score</th><th>Trend</th><th>Confidence</th></tr>"
    
    for _, row in df_components.iterrows():
        table_html += f"<tr><td>{row['Component']}</td><td>{row['Score']}/100</td><td>{format_trend(row['Trend'])}</td><td>{format_confidence(row['Confidence'])}</td></tr>"
    
    table_html += "</table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Component score chart
    fig = px.bar(
        df_components, 
        x="Component", 
        y="Score",
        color="Score",
        color_continuous_scale=["#dc3545", "#ffc107", "#28a745"],
        range_color=[0, 100],
        labels={"Score": "Score (0-100)"},
        height=300
    )
    fig.update_layout(margin=dict(t=20, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Critical Insights section
    st.markdown("<h3>Critical Insights</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    for i, insight in enumerate(insights):
        with col1 if i % 2 == 0 else col2:
            status_color = "#28a745" if insight["status"] == "success" else "#ffc107"
            st.markdown(f"""
            <div class="card">
                <h4><span style="color:{status_color}">●</span> {insight["title"]}</h4>
                <ul>
                    {"".join([f"<li>{detail}</li>" for detail in insight["details"]])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown("<h3>Core Metrics Summary</h3>", unsafe_allow_html=True)
    
    # Core metrics table
    table_html = "<div class='table-container'><table>"
    table_html += "<tr><th>Key Metric</th><th>Current</th><th>vs Benchmark</th><th>Trend</th><th>Confidence</th></tr>"
    
    for _, row in df_metrics.iterrows():
        table_html += f"<tr><td>{row['Key Metric']}</td><td>{row['Current']}</td><td>{row['vs Benchmark']}</td><td>{format_trend(row['Trend'])}</td><td>{format_confidence(row['Confidence'])}</td></tr>"
    
    table_html += "</table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Create a subplot with 2 metrics per row
    st.markdown("<h3>Key Metrics Visualization</h3>", unsafe_allow_html=True)
    
    # Extract numeric values for plotting
    current_values = []
    for val in df_metrics["Current"]:
        # Extract numeric part from string
        if isinstance(val, str):
            if "%" in val:
                current_values.append(float(val.replace("%", "")))
            elif "$" in val:
                current_values.append(float(val.replace("$", "").replace("K", "")))
            elif "days" in val:
                current_values.append(float(val.replace(" days", "")))
            elif "x" in val:
                current_values.append(float(val.replace("x", "")))
            else:
                current_values.append(float(val))
        else:
            current_values.append(float(val))
    
    df_metrics["NumericValue"] = current_values
    
    # Create a 2x2 subplot for key metrics visualization
    metrics_to_show = ["Monthly Growth Rate", "Net Revenue Retention", "CAC (Overall)", "Pipeline Coverage"]
    filtered_df = df_metrics[df_metrics["Key Metric"].isin(metrics_to_show)]
    
    # Add spacer
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    
    # Use separate indicators instead of subplots to avoid text overlap
    col1, col2 = st.columns(2)
    
    # First row
    with col1:
        # Monthly Growth Rate
        row = filtered_df[filtered_df["Key Metric"] == "Monthly Growth Rate"].iloc[0]
        color = "#dc3545" if row["Trend"] < 0 else "#28a745"
        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=row["NumericValue"],
            delta={"reference": row["NumericValue"] - row["Trend"], "relative": False, "valueformat": ".1f"},
            number={"suffix": "%", "font": {"size": 40}},
            title={"text": "Monthly Growth Rate", "font": {"size": 16}},
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Net Revenue Retention
        row = filtered_df[filtered_df["Key Metric"] == "Net Revenue Retention"].iloc[0]
        color = "#28a745" if row["Trend"] > 0 else "#dc3545"
        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=row["NumericValue"],
            delta={"reference": row["NumericValue"] - row["Trend"], "relative": False, "valueformat": ".1f"},
            number={"suffix": "%", "font": {"size": 40}},
            title={"text": "Net Revenue Retention", "font": {"size": 16}},
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    # Second row
    with col1:
        # CAC (Overall)
        row = filtered_df[filtered_df["Key Metric"] == "CAC (Overall)"].iloc[0]
        color = "#dc3545" if row["Trend"] > 0 else "#28a745"
        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=row["NumericValue"],
            delta={"reference": row["NumericValue"] - row["Trend"], "relative": False, "valueformat": ".1f"},
            number={"prefix": "$", "suffix": "K", "font": {"size": 40}},
            title={"text": "CAC (Overall)", "font": {"size": 16}},
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pipeline Coverage
        row = filtered_df[filtered_df["Key Metric"] == "Pipeline Coverage"].iloc[0]
        color = "#28a745" if row["Trend"] > 0 else "#dc3545"
        fig = go.Figure(go.Indicator(
            mode="number+delta",
            value=row["NumericValue"],
            delta={"reference": row["NumericValue"] - row["Trend"], "relative": False, "valueformat": ".1f"},
            number={"suffix": "x", "font": {"size": 40}},
            title={"text": "Pipeline Coverage", "font": {"size": 16}},
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
    
    # Data confidence assessment
    st.markdown("<h3>Data Confidence Assessment</h3>", unsafe_allow_html=True)
    
    conf_col1, conf_col2, conf_col3 = st.columns(3)
    
    with conf_col1:
        st.markdown(f"""
        <div class="card">
            <h4 class="confidence-high">High Confidence Areas</h4>
            <ul>
                {"".join([f"<li>{item}</li>" for item in confidence_data["High"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with conf_col2:
        st.markdown(f"""
        <div class="card">
            <h4 class="confidence-medium">Medium Confidence Areas</h4>
            <ul>
                {"".join([f"<li>{item}</li>" for item in confidence_data["Medium"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with conf_col3:
        st.markdown(f"""
        <div class="card">
            <h4 class="confidence-low">Low Confidence Areas</h4>
            <ul>
                {"".join([f"<li>{item}</li>" for item in confidence_data["Low"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("<h3>Key Recommendations</h3>", unsafe_allow_html=True)
    
    for i, rec in enumerate(recommendations):
        st.markdown(f"""
        <div class="card">
            <h4>{i+1}. {rec["title"]}</h4>
            <ul>
                {"".join([f"<li>{detail}</li>" for detail in rec["details"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Improvement focus
    st.markdown(f"""
    <div class="card">
        <h4>Improvement Focus</h4>
        <p>Priority on improving CRM data quality and consistency to enable more accurate segmentation and pipeline analysis in future reports</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## Dashboard Controls")
    st.markdown("### Time Period")
    time_period = st.selectbox("Select Time Period", ["Q2 2023", "Q1 2023", "Q4 2022", "Q3 2022"])
    
    st.markdown("### Filters")
    segment_filter = st.multiselect("Customer Segment", ["Enterprise", "Mid-Market", "SMB"], default=["Enterprise", "Mid-Market", "SMB"])
    product_filter = st.multiselect("Product Line", ["Core Platform", "Advanced Analytics", "Enterprise Services"], default=["Core Platform", "Advanced Analytics", "Enterprise Services"])
    
    st.markdown("### Export Options")
    export_format = st.selectbox("Export Format", ["PDF", "Excel", "CSV"])
    if st.button("Export Dashboard"):
        st.info("Export functionality would be implemented here")
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Executive Brief Dashboard v1.0")
    st.markdown("Last updated: July 15, 2023")

# Run the app with: streamlit run src/ui/executive_dashboard.py 