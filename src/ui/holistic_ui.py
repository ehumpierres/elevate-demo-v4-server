import streamlit as st
import pandas as pd
import numpy as np
import time
import sys
import os
import re
import traceback
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the Mem0 Companion agent
from src.companion import Companion

# Import Vanna functionality for data analysis
from src.ui.vanna_calls import (
    generate_sql_cached,
    run_sql_cached,
    is_sql_valid_cached,
    clear_all_caches,
    test_snowflake_connection
)

# Custom exception handling to override Streamlit's default error display
def handle_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "sql" in error_msg.lower() or "query" in error_msg.lower():
                # SQL-related error
                if "syntax" in error_msg.lower() or "compilation" in error_msg.lower():
                    st.info("There was an error compiling the SQL. The Data Analyst couldn't answer this question.")
                else:
                    st.info("The Data Analyst couldn't process this query.")
            else:
                # Non-SQL error - still use info box but with general message
                st.info(f"An issue occurred: {error_msg}")
            
            # Optionally log the full traceback for debugging
            traceback.print_exc()
            return None
    return wrapper

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "companion" not in st.session_state:
    st.session_state.companion = None

if "data_analyst_enabled" not in st.session_state:
    st.session_state.data_analyst_enabled = False

if "loading" not in st.session_state:
    st.session_state.loading = False

# Page configuration
st.set_page_config(
    page_title="Elevate AI Companion",
    page_icon="🧠",
    layout="wide"
)

# Function to format revenue text to ensure proper spacing
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

# Function to format numeric values in DataFrames
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

# Function to create a simple visualization of data
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

# Apply our exception handler to the run_sql_cached function to handle errors gracefully
@handle_exception
def safe_run_sql(sql_query, question):
    """A wrapper around run_sql_cached that handles exceptions gracefully"""
    return run_sql_cached(sql=sql_query)

# Function to process user input with data analysis if enabled
def process_input(user_input):
    st.session_state.loading = True
    
    # Step 1: Check if data analysis is enabled
    data_result = None
    sql_query = None
    sql_error = None
    
    if st.session_state.data_analyst_enabled:
        with st.spinner("Data Analyst Agent is analyzing..."):
            try:
                # Generate SQL from the user's question
                sql_query = generate_sql_cached(question=user_input)
                
                # Execute the SQL if valid
                if sql_query and is_sql_valid_cached(sql=sql_query):
                    try:
                        # Run the SQL query with our safe wrapper
                        data_result = safe_run_sql(sql_query, user_input)
                        
                        # Format the DataFrame if results were returned
                        if data_result is not None and not data_result.empty:
                            # Set row indices to start from 1
                            data_result.index = np.arange(1, len(data_result) + 1)
                    except Exception as e:
                        # This shouldn't be hit due to our wrapper, but just in case
                        sql_error = "There was an error executing the SQL. The Data Analyst couldn't answer this question."
                else:
                    # SQL not valid or not generated
                    sql_error = "SQL query not applicable for this question"
            except Exception as e:
                # Catch any other errors in the data analysis process
                sql_error = "The Data Analyst couldn't process this query."
    
    # Step 2: Process the user input through the Mem0 agent
    with st.spinner("Business Architecture AI Agent is thinking..."):
        # If we have data results, include them in the context for the companion
        if data_result is not None:
            # For now, we'll convert the DataFrame to markdown to include in the prompt
            # In a real implementation, you might want to add this as a special parameter to the agent
            data_context = f"Data Analysis Results:\n{data_result.to_markdown()}"
            # The actual implementation would depend on how the Companion class accepts additional context
            response = st.session_state.companion.process_message(f"{user_input}\n\nContext: {data_context}")
        else:
            # Process without data context
            response = st.session_state.companion.process_message(user_input)
        
        # Fix spacing issues in revenue text formatting
        response = fix_revenue_text_spacing(response)
    
    # Add the messages to the conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # If we have data results, store them in the message for display
    if data_result is not None:
        st.session_state.messages[-1]["data"] = data_result
        st.session_state.messages[-1]["sql"] = sql_query
    
    # If there was a SQL error, store it in the message for display
    if sql_error:
        st.session_state.messages[-1]["sql_error"] = sql_error
    
    st.session_state.loading = False

# Sidebar for user identification and settings
with st.sidebar:
    st.title("Elevate AI Companion")
    
    # User identification
    if st.session_state.user_id is None:
        user_id = st.text_input("Enter your username:")
        if st.button("Start Session") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id)
            st.rerun()
    else:
        st.write(f"Active User: **{st.session_state.user_id}**")
        
        # Data connection section
        st.subheader("Data Connection")
        
        # Test Snowflake Connection button
        if st.button("Test Snowflake Connection"):
            with st.spinner("Testing Snowflake connection..."):
                try:
                    result = test_snowflake_connection()
                    if isinstance(result, dict) and result.get("success", False):
                        st.success("✅ Connected to Snowflake successfully!")
                        with st.expander("Connection Details"):
                            # Format the connection details nicely
                            st.write(f"**User:** {result.get('user')}")
                            st.write(f"**Role:** {result.get('role')}")
                            st.write(f"**Warehouse:** {result.get('warehouse')}")
                            st.write(f"**Database:** {result.get('database')}")
                            st.write(f"**Schema:** {result.get('schema')}")
                            st.write(f"**Tables found:** {result.get('table_count', 0)}")
                            
                            # Check schema access
                            if result.get("schema_accessible", False):
                                st.write("✅ Schema is accessible")
                            else:
                                st.error(f"❌ Schema access error: {result.get('schema_error', 'Unknown error')}")
                    else:
                        st.error("❌ Failed to connect to Snowflake")
                        with st.expander("Error Details"):
                            if isinstance(result, dict):
                                st.write(f"**Error:** {result.get('error', 'Unknown error')}")
                                if "details" in result:
                                    st.code(result["details"], language="python")
                            else:
                                st.write("Connection test failed without detailed information.")
                except Exception as e:
                    st.error(f"❌ Error testing connection: {str(e)}")
                    with st.expander("Error Traceback"):
                        st.code(traceback.format_exc(), language="python")
        
        # Add a Reconnect to Snowflake button
        if st.button("Reconnect to Snowflake"):
            with st.spinner("Reconnecting to Snowflake..."):
                try:
                    # Clear caches to force reconnection
                    clear_all_caches()
                    st.success("Reconnected to Snowflake successfully!")
                    
                    # Verify the new connection
                    with st.spinner("Verifying new connection..."):
                        result = test_snowflake_connection()
                        if isinstance(result, dict) and result.get("success", False):
                            st.success(f"✅ Verified connection to {result.get('database')}.{result.get('schema')}")
                        else:
                            st.warning("⚠️ Reconnection may have failed, please check connection details")
                except Exception as e:
                    st.error(f"❌ Error during reconnection: {str(e)}")
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc(), language="python")
        
        # Show current Snowflake environment settings
        with st.expander("Snowflake Configuration"):
            # Get environment variables related to Snowflake (hide sensitive values)
            snowflake_vars = {
                "Account": os.environ.get("SNOWFLAKE_ACCOUNT", "Not set"),
                "User": os.environ.get("SNOWFLAKE_USER", "Not set"),
                "Organization": os.environ.get("SNOWFLAKE_ORG", "Not set"),
                "Warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "Not set"),
                "Role": os.environ.get("SNOWFLAKE_ROLE", "Not set"),
                "Database": os.environ.get("SNOWFLAKE_DATABASE", "Not set"),
                "Schema": os.environ.get("SNOWFLAKE_SCHEMA", "Not set"),
                "Auth Method": "Private Key (base64)" if os.environ.get("SNOWFLAKE_PRIVATE_KEY_BASE64") else 
                              "Private Key File" if os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH") else
                              "Password" if os.environ.get("SNOWFLAKE_PASSWORD") else "None"
            }
            
            for key, value in snowflake_vars.items():
                st.write(f"**{key}:** {value}")
        
        st.divider()
        
        # Clear cache button
        if st.button("Clear Cache"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Main content area - only show if user is identified
if st.session_state.user_id:
    # Display chat header
    st.title("Elevate AI Companion")
    st.caption("An intelligent business strategist with memory and data analysis capabilities")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Apply fix_revenue_text_spacing to all displayed messages to ensure proper formatting
            formatted_content = fix_revenue_text_spacing(message["content"])
            st.write(formatted_content)
            
            # If there was a SQL error, display it as an info message with a friendly message
            if "sql_error" in message:
                # Extract the error type for more specific messages
                error_msg = message["sql_error"]
                
                if "compilation error" in error_msg.lower() or "syntax error" in error_msg.lower():
                    st.info("There was an error compiling the SQL. The Data Analyst couldn't answer this question.")
                elif "execution error" in error_msg.lower():
                    st.info("There was an error executing the SQL. The Data Analyst couldn't answer this question.")
                else:
                    st.info("The Data Analyst couldn't answer this question with SQL.")
            
            # If this message has data attached, display it
            if "data" in message and message["data"] is not None:
                st.subheader("Data Table")
                # Format and display the data
                formatted_df = format_numeric_values(message["data"])
                st.dataframe(formatted_df, use_container_width=True)
                
                # Show the SQL query used
                with st.expander("SQL Query"):
                    st.code(message["sql"], language="sql")
                
                # Create visualization
                create_visualization(message["data"])
    
    # Chat input area with data analyst toggle
    col1, col2 = st.columns([5, 1])
    
    with col2:
        # Toggle button for Data Analyst Agent
        st.session_state.data_analyst_enabled = st.toggle(
            "Invite Data Analyst Agent", 
            value=st.session_state.data_analyst_enabled
        )
    
    with col1:
        # Chat input
        user_input = st.chat_input(
            "Type your message here...",
            disabled=st.session_state.loading or not st.session_state.user_id
        )
        
        # Process input when submitted
        if user_input:
            process_input(user_input)
            st.rerun()
    
    # Loading indicator
    if st.session_state.loading:
        st.markdown("![Loading](https://i.gifer.com/ZKZx.gif)")
else:
    # Welcome message when no user is identified
    st.title("Welcome to Elevate AI Companion")
    st.write("Please enter your username in the sidebar to get started.") 