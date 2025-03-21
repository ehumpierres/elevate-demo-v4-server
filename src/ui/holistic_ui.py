import streamlit as st
import pandas as pd
import numpy as np
import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the Mem0 Companion agent
from src.companion import Companion

# Import Vanna functionality for data analysis
from src.ui.vanna_calls import (
    generate_sql_cached,
    run_sql_cached,
    is_sql_valid_cached
)

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
    page_title="Mem0 AI Companion",
    page_icon="🧠",
    layout="wide"
)

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

# Function to process user input with data analysis if enabled
def process_input(user_input):
    st.session_state.loading = True
    
    # Step 1: Check if data analysis is enabled
    data_result = None
    sql_query = None
    
    if st.session_state.data_analyst_enabled:
        with st.spinner("Data Analyst Agent is analyzing..."):
            # Generate SQL from the user's question
            sql_query = generate_sql_cached(question=user_input)
            
            # Execute the SQL if valid
            if sql_query and is_sql_valid_cached(sql=sql_query):
                try:
                    # Run the SQL query
                    data_result = run_sql_cached(sql=sql_query)
                    
                    # Format the DataFrame if results were returned
                    if data_result is not None and not data_result.empty:
                        # Set row indices to start from 1
                        data_result.index = np.arange(1, len(data_result) + 1)
                except Exception as e:
                    st.error(f"Error executing SQL: {str(e)}")
    
    # Step 2: Process the user input through the Mem0 agent
    with st.spinner("Mem0 Agent is thinking..."):
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
    
    # Add the messages to the conversation history
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # If we have data results, store them in the message for display
    if data_result is not None:
        st.session_state.messages[-1]["data"] = data_result
        st.session_state.messages[-1]["sql"] = sql_query
    
    st.session_state.loading = False

# Sidebar for user identification and settings
with st.sidebar:
    st.title("Mem0 AI Companion")
    
    # User identification
    if st.session_state.user_id is None:
        user_id = st.text_input("Enter your username:")
        if st.button("Start Session") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id)
            st.rerun()
    else:
        st.write(f"Active User: **{st.session_state.user_id}**")
        
        # Clear cache button
        if st.button("Clear Cache"):
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Main content area - only show if user is identified
if st.session_state.user_id:
    # Display chat header
    st.title("Mem0 AI Companion")
    st.caption("An intelligent assistant with memory and data analysis capabilities")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
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
    st.title("Welcome to Mem0 AI Companion")
    st.write("Please enter your username in the sidebar to get started.") 