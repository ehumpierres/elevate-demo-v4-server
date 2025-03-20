import time
import streamlit as st
from vanna_calls import (
    generate_sql_cached,
    run_sql_cached,
    is_sql_valid_cached
)
import plotly.express as px
import plotly.graph_objects as go
from config.persona_vanna import (
    UI_TITLE, UI_SUBTITLE, UI_ICON, UI_AVATAR, UI_SIDEBAR_TITLE, UI_CHAT_ROLE,
    UI_FIRST_ROWS_TEXT, UI_FOLLOWUP_TEXT, UI_SUGGESTED_QUESTIONS_TEXT
)
import pandas as pd
import tabulate  # For markdown table generation
import numpy as np

# New function to display a dataframe with thousands separators
def display_table_with_formatting(df, max_rows=10):
    """Display a dataframe with proper formatting including thousands separators and add plots"""
    # Create a copy for display and limit rows
    display_df = df.head(max_rows).copy()
    
    # Create styler object
    styler = display_df.style
    
    # Format numeric columns
    numeric_cols = display_df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if display_df[col].dtype in [np.int64, np.int32]:
            styler.format(subset=col, formatter="{:,d}")
        else:
            styler.format(subset=col, formatter="{:,.2f}")
    
    # Create columns for layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Render the table as HTML
        st.write(styler.to_html(), unsafe_allow_html=True)
        
        # Toggle view button
        if st.button("Toggle view", key=f"toggle_{hash(str(df))}"):
            st.dataframe(display_df, use_container_width=True)
    
    with col2:
        # Generate quick plots if numeric columns exist
        if len(numeric_cols) > 0:
            # Check for date column - more robust detection
            date_cols = []
            for col in display_df.columns:
                if (col.upper() == 'MONTH' or 'DATE' in col.upper() or 'TIME' in col.upper() or
                    (display_df[col].dtype == 'object' and '-' in str(display_df[col].iloc[0]) if len(display_df) > 0 else False)):
                    date_cols.append(col)
            
            x_col = date_cols[0] if date_cols else None
            
            # Always create a basic bar chart even without a date column
            value_col = numeric_cols[0]
            fig = px.bar(
                display_df, 
                x=x_col if x_col else None,
                y=value_col, 
                title=f"Values: {value_col}"
            )
            fig.update_layout(yaxis=dict(tickformat=","))
            st.plotly_chart(fig, use_container_width=True)
            
            # If we have a date column, also show line chart
            if x_col:
                fig = px.line(
                    display_df, 
                    x=x_col, 
                    y=value_col, 
                    title=f"Trend: {value_col}"
                )
                fig.update_layout(yaxis=dict(tickformat=","))
                st.plotly_chart(fig, use_container_width=True)

def format_value(x):
    """Format a numeric value with appropriate thousands separators"""
    # Handle scientific notation first
    if isinstance(x, float) and ('e' in str(x).lower() or x > 1000):
        # For integers or values that should be displayed as integers
        if x.is_integer() or abs(x - round(x)) < 1e-10:
            return f"{int(x):,}"
        else:
            return f"{x:,.2f}"
    elif isinstance(x, (int, np.integer)):
        return f"{x:,}"  # Format integers with commas
    elif isinstance(x, (float, np.float64, np.float32)):
        if x.is_integer() or abs(x - round(x)) < 1e-10:
            return f"{int(x):,}"  # Format whole numbers without decimals
        else:
            return f"{x:,.2f}"  # Format floats with 2 decimal places
    else:
        return str(x)

# Helper function to format numeric values with appropriate thousands separators
def format_numeric_values(df):
    """Format numeric values in DataFrame with appropriate thousands separators and decimal places"""
    formatted_df = df.copy()
    
    # Find all numeric columns
    numeric_cols = []
    for col in df.columns:
        if df[col].dtype.kind in 'ifc':  # Integer, Float, Complex
            numeric_cols.append(col)
    
    # Apply formatting based on data type
    for col in numeric_cols:
        # Check if values are integers or have decimal places
        if df[col].dtype == np.int64 or df[col].dtype == np.int32 or (df[col].dropna() % 1 == 0).all():
            # Format as integers with thousand separators
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else x)
        else:
            # Determine optimal decimal places (max 2)
            non_zero_decimals = df[col].dropna().apply(lambda x: x % 1)
            if (non_zero_decimals == 0).all():
                # All values are whole numbers
                formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else x)
            else:
                # Has decimal places, use 2 decimal places with thousand separators
                formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else x)
    
    return formatted_df

# Determine if we should generate a chart
@st.cache_data
def should_generate_chart(question, sql, df):
    """Determine if we should generate a chart for this query."""
    if df is None or df.empty:
        return False
    
    # Check if the question explicitly asks for a chart/plot/visualization
    plot_keywords = ["plot", "chart", "graph", "visualize", "visualization", "show"]
    if any(keyword in question.lower() for keyword in plot_keywords):
        # If explicitly asked for visualization, check if we have data to visualize
        num_cols = df.select_dtypes(include=['number']).columns
        if len(num_cols) == 0:
            return False
        return True
    
    # Check if we have date/time/month data that should be plotted
    # First look for columns that look like dates
    date_pattern = r'^\d{4}-\d{2}-\d{2}$' 
    month_pattern = r'^\d{4}-\d{2}$'
    
    potential_date_cols = []
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if column values match date patterns
            if df[col].astype(str).str.match(date_pattern).any() or df[col].astype(str).str.match(month_pattern).any():
                potential_date_cols.append(col)
    
    # If we have date columns and numeric columns, we should probably visualize
    if len(potential_date_cols) > 0 and len(df.select_dtypes(include=['number']).columns) > 0:
        return True
    
    # Check if we have numerical columns that could be visualized
    num_cols = df.select_dtypes(include=['number']).columns
    if len(num_cols) > 0 and df.shape[0] > 1 and df.shape[0] <= 50:
        return True
    
    return False

# Generate Plotly code for visualization
@st.cache_data
def generate_plotly_code(question, sql, df):
    if df is None or df.empty:
        return ""
    
    try:
        # Get column types
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Check for string columns that look like dates
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        month_pattern = r'^\d{4}-\d{2}$'
        
        string_date_cols = []
        for col in categorical_cols:
            if df[col].astype(str).str.match(date_pattern).any() or df[col].astype(str).str.match(month_pattern).any():
                string_date_cols.append(col)
                
        # Combine all date-like columns
        all_date_cols = date_cols + string_date_cols
        
        # If we have date columns and numeric columns, create a line or bar chart for time series
        if len(all_date_cols) >= 1 and len(numeric_cols) >= 1:
            date_col = all_date_cols[0]
            value_col = numeric_cols[0]
            
            # Check if we're plotting monthly data
            is_monthly_data = "month" in question.lower() or any("month" in col.lower() for col in df.columns)
            
            # Force bar chart for monthly data, otherwise decide based on number of data points
            if is_monthly_data or df[date_col].nunique() <= 12:
                return f"""
import plotly.express as px
fig = px.bar(df, x='{date_col}', y='{value_col}', title='{question}')
fig.update_layout(xaxis_title='{date_col}', yaxis_title='{value_col}')
fig
"""
            else:
                return f"""
import plotly.express as px
fig = px.line(df, x='{date_col}', y='{value_col}', title='{question}')
fig.update_layout(xaxis_title='{date_col}', yaxis_title='{value_col}')
fig
"""
        # Determine chart type based on data and question
        elif len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            # Bar chart code for categorical vs numeric
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            return f"""
import plotly.express as px
fig = px.bar(df, x='{x_col}', y='{y_col}', title='{question}')
fig.update_layout(xaxis_title='{x_col}', yaxis_title='{y_col}')
fig
"""
        elif len(numeric_cols) >= 2:
            # Scatter plot for two numeric columns
            return f"""
import plotly.express as px
fig = px.scatter(df, x='{numeric_cols[0]}', y='{numeric_cols[1]}', title='{question}')
fig.update_layout(xaxis_title='{numeric_cols[0]}', yaxis_title='{numeric_cols[1]}')
fig
"""
        elif len(numeric_cols) == 1 and len(df) > 1:
            # Simple bar chart with index
            return f"""
import plotly.express as px
fig = px.bar(df, y='{numeric_cols[0]}', title='{question}')
fig.update_layout(yaxis_title='{numeric_cols[0]}')
fig
"""
        else:
            return ""
    except Exception as e:
        st.error(f"Error generating Plotly code: {str(e)}")
        return ""

# Generate the plotly figure
@st.cache_data
def generate_plot(code, df):
    try:
        # Create a local environment
        local_vars = {"df": df, "px": px, "go": go}
        
        # Execute the code in the local environment
        exec(code, globals(), local_vars)
        
        # Return the figure
        if "fig" in local_vars:
            # Update the figure to include comma formatting in y-axis
            if hasattr(local_vars["fig"], "update_layout"):
                local_vars["fig"].update_layout(
                    yaxis=dict(tickformat=",")  # Add comma separator to y-axis
                )
            return local_vars["fig"]
        return None
    except Exception as e:
        st.error(f"Error generating plot: {str(e)}")
        # Return a simple fallback plot instead of None
        try:
            # Create a simple fallback plot with the first numeric column
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                fig = px.bar(df, y=numeric_cols[0], title="Data Visualization")
                fig.update_layout(yaxis=dict(tickformat=","))  # Add comma separator
                return fig
        except:
            pass
        return None

# Set page configuration
st.set_page_config(
    page_title=UI_TITLE,
    page_icon=UI_ICON,
    layout="wide"
)

# Custom avatar URL
avatar_url = UI_AVATAR

# Initialize session state
if "my_question" not in st.session_state:
    st.session_state["my_question"] = None

if "df" not in st.session_state:
    st.session_state["df"] = None

# Sidebar configuration
st.sidebar.title(UI_SIDEBAR_TITLE)
st.sidebar.checkbox("Show SQL", value=True, key="show_sql")
st.sidebar.checkbox("Show Table", value=True, key="show_table")
st.sidebar.checkbox("Show Plotly Code", value=False, key="show_plotly_code")
st.sidebar.checkbox("Show Chart", value=True, key="show_chart")

# Clear cache button
if st.sidebar.button("Clear Cache", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Reset button
if st.sidebar.button("Reset", use_container_width=True):
    st.session_state["my_question"] = None
    st.session_state["df"] = None
    st.rerun()

# Main page content
st.title(UI_TITLE)
st.caption(UI_SUBTITLE)

# Function to set the current question
def set_question(question):
    st.session_state["my_question"] = question
    st.rerun()

# Get the current question
my_question = st.session_state.get("my_question", None)

# Question input
user_input = st.chat_input("Ask me a question about your data")
if user_input:
    my_question = user_input
    st.session_state["my_question"] = my_question
    st.rerun()

# Process the question if one exists
if my_question:
    # Display user question
    user_message = st.chat_message("user")
    user_message.write(my_question)
    
    # Check if this is a direct visualization request for existing data
    is_viz_request = any(phrase in my_question.lower() for phrase in ["show me a visualization", "visualize this data", "create a chart", "plot this data"])
    
    if is_viz_request and st.session_state.get("df") is not None:
        # Use existing data for visualization
        df = st.session_state.get("df")
        assistant_message = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
        
        with assistant_message:
            try:
                # Generate a simple visualization based on the data
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    fig = px.bar(df, y=numeric_cols[0], title="Data Visualization")
                    st.plotly_chart(fig)
                else:
                    st.info("I couldn't create a visualization because there are no numeric columns in the data.")
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
    else:
        # Generate SQL
        sql = generate_sql_cached(question=my_question)
        
        if sql:
            # Display SQL if valid and if shown
            if is_sql_valid_cached(sql=sql):
                if st.session_state.get("show_sql", True):
                    assistant_message_sql = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                    assistant_message_sql.code(sql, language="sql", line_numbers=True)
            else:
                assistant_message = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                # Provide more user-friendly message for SQL syntax errors
                if "syntax error" in sql.lower() or "compilation error" in sql.lower():
                    assistant_message.error("I generated SQL with a syntax error. Let me try to fix that for you.")
                else:
                    assistant_message.write(sql)
                st.stop()
            
            # Execute SQL and get results
            try:
                df = run_sql_cached(sql=sql)
                
                if df is not None:
                    st.session_state["df"] = df
                
                if st.session_state.get("df") is not None:
                    df = st.session_state.get("df")
                    
                    # Display table
                    if st.session_state.get("show_table", True):
                        assistant_message_table = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                        with assistant_message_table:
                            if len(df) > 10:
                                st.text(UI_FIRST_ROWS_TEXT)
                            
                            # Use our new function to display the table with formatting
                            display_table_with_formatting(df)
                    
                    # Generate and display chart if appropriate
                    should_generate_chart = should_generate_chart(question=my_question, sql=sql, df=df)
                    
                    # FORCE chart generation for "plot" queries regardless of the cached result
                    if "plot" in my_question.lower() or should_generate_chart:
                        try:
                            assistant_message_chart = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                            with assistant_message_chart:
                                # Identify likely date/month column - make detection more robust
                                date_col = None
                                
                                # Look for MONTH column explicitly first (case-insensitive)
                                for col in df.columns:
                                    if col.upper() == 'MONTH':
                                        date_col = col
                                        break
                                
                                # If still not found, look for other date-like columns
                                if not date_col:
                                    for col in df.columns:
                                        if ('DATE' in col.upper() or 'TIME' in col.upper()):
                                            date_col = col
                                            break
                                
                                # Last resort - check values in each column
                                if not date_col:
                                    for col in df.columns:
                                        if df[col].dtype == 'object' and len(df) > 0:
                                            # Try to find date-like strings
                                            sample = str(df[col].iloc[0])
                                            if '-' in sample and len(sample) >= 7:  # YYYY-MM or YYYY-MM-DD format
                                                date_col = col
                                                break
                                
                                # Define numeric columns
                                numeric_cols = df.select_dtypes(include=['number']).columns
                                
                                # Always create a visualization if we have numeric columns
                                if len(numeric_cols) > 0:
                                    value_col = numeric_cols[0]
                                    
                                    if date_col:
                                        # Format y-axis with commas - time series charts
                                        fig = px.bar(df, x=date_col, y=value_col, title=f"{my_question}")
                                        fig.update_layout(
                                            xaxis_title=date_col,
                                            yaxis_title=value_col,
                                            yaxis=dict(tickformat=",")
                                        )
                                        st.plotly_chart(fig)
                                        
                                        fig2 = px.line(df, x=date_col, y=value_col, title=f"Trend: {my_question}")
                                        fig2.update_layout(
                                            xaxis_title=date_col,
                                            yaxis_title=value_col,
                                            yaxis=dict(tickformat=",")
                                        )
                                        st.plotly_chart(fig2)
                                    else:
                                        # Simple bar chart without date column
                                        fig = px.bar(df, y=value_col, title=f"{my_question}")
                                        fig.update_layout(yaxis=dict(tickformat=","))
                                        st.plotly_chart(fig)
                        except Exception as e:
                            st.error(f"Error creating direct visualization: {str(e)}")
                            
                        # Also try the original code-based approach as fallback
                        try:
                            code = generate_plotly_code(question=my_question, sql=sql, df=df)
                            
                            # Show plotly code if enabled
                            if st.session_state.get("show_plotly_code", False) and code:
                                assistant_message_plotly_code = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                                assistant_message_plotly_code.code(code, language="python", line_numbers=True)
                            
                            # Show chart if enabled
                            if code and st.session_state.get("show_chart", True):
                                assistant_message_chart = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                                with assistant_message_chart:
                                    st.write("Executing visualization code...")  # Debug line
                                    fig = generate_plot(code=code, df=df)
                                    if fig is not None:
                                        st.write("Displaying chart...")  # Debug line
                                        st.plotly_chart(fig)
                                        
                                        # Add button to show data in markdown format
                                        if st.button("Show Chart Data", key=f"chart_data_btn_{hash(str(my_question))}"):
                                            # Use our new function to display the chart data with formatting
                                            display_table_with_formatting(df)
                                    else:
                                        st.info("I couldn't generate a chart for this data. Try a different query or visualization type.")
                        except Exception as e:
                            st.error(f"Error with visualization: {str(e)}")
            
            except Exception as e:
                # Display error message for SQL execution failures
                assistant_message_error = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
                error_msg = str(e)
                
                if "syntax error" in error_msg.lower() or "compilation error" in error_msg.lower():
                    assistant_message_error.error("There's a syntax error in the SQL query. Let me try a different approach.")
                elif "access denied" in error_msg.lower() or "permission" in error_msg.lower():
                    assistant_message_error.error(f"I don't have permission to access one or more tables in this query: {error_msg}")
                elif "no such table" in error_msg.lower() or "table not found" in error_msg.lower():
                    assistant_message_error.error(f"One or more tables in this query don't exist: {error_msg}")
                elif "timeout" in error_msg.lower():
                    assistant_message_error.error(f"The query timed out: {error_msg}")
                else:
                    assistant_message_error.error(f"I couldn't execute this SQL query: {error_msg}")
                
                st.stop()
            
        else:
            # Display error if SQL generation failed
            assistant_message_error = st.chat_message(UI_CHAT_ROLE, avatar=avatar_url)
            assistant_message_error.error("I wasn't able to generate SQL for that question") 