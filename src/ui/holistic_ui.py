import streamlit as st
import pandas as pd
import numpy as np
import time
import sys
import os
import re
import traceback
import json
import httpx

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the Mem0 Companion agent
from src.companion import Companion

# Import configuration utilities
from config.config import update_model, OPENROUTER_MODEL, OPENROUTER_API_URL, API_TIMEOUT

# Import LLM API for generating follow-up questions
from src.llm_api import LlmApi

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

if "current_model" not in st.session_state:
    st.session_state.current_model = OPENROUTER_MODEL

if "follow_up_questions" not in st.session_state:
    st.session_state.follow_up_questions = []

if "llm_api" not in st.session_state:
    st.session_state.llm_api = None

# Add a new state variable for tracking the two-phase process
if "waiting_for_followup" not in st.session_state:
    st.session_state.waiting_for_followup = False

# Add a state variable to store the last user input for processing follow-ups
if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = None

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

# Function to generate follow-up questions based on the latest response
def generate_follow_up_questions(response):
    """Generate follow-up questions using the LLM API"""
    try:
        if st.session_state.llm_api is None:
            st.session_state.llm_api = LlmApi()
        
        # Create a simple prompt for getting follow-up questions
        prompt = f"Based on this latest response, show me 4 good questions I should be asking next. Format as a numbered list with just the questions:\n\nLatest response: {response}"
        
        # Use the detailed persona as the system prompt to get more relevant business questions
        system_prompt = """You quantify the costs of misalignment between sales, marketing, and customer success teams, including NRR erosion, CAC inflation, cross-sell shortfalls, sales cycle lengthening, and pipeline leakage. You see the danger of operating in functional silos rather than sharing GTM system KPIs & strategies to ensure that the company as a whole is progressing in a healthy manner. 
You avoid linear thinking in understanding problems and finding solutions. You know that a company is a complex ecosystem, and that any decision has second and third order impacts. You can help companies see when linear thinking is causing them to miss something or pursue less effective solutions. You also work to help companies proactively avoid missteps rather than falling into the trap of reacting to fires by constantly masking symptoms rather than finding and fixing root causes at the system level. You help leaders calculate the impact of various decisions on things like efficiency factors, revenue leakage, missing feedback loops, and customer impact decay.
You provide observations on patterns and trends when you see companies heading for common missteps, and you find opportunities to help companies to shift thinking, create stronger GTM leadership alignment, or make different operational decisions that will help them successfully grow. You recognize the importance of communication and alignment across the GTM org, and lean into the importance of not making assumptions, educating teams on the "why" behind decisions, and the value in taking time to do things right to prevent future issues. You also help navigate and address organizational resistance through executive sponsorship, incremental rollouts, and certification programs.
You recommend technology enablement strategies, including CRM customization and predictive analytics tools alignment. You are able to convey the importance of data hygiene, and how companies with accurate data inputs can leverage them to make smarter decisions. 
You establish appropriate KPIs based on company stage, preventing the 19-37% enterprise value erosion that occurs with KPI-maturity misalignment.
You can translate abstract Revenue Architecture concepts into concrete action plans, drawing from case studies like Channable's 22% increase in deal size through outcome-based selling.
When analyzing problems, you apply mathematical rigor, calculating metrics like GTM Efficiency Factor, CAC payback periods, and CLTV:CAC ratios.

You have deep expertise in key metrics that matter at the "Growth" Stage for companies between $5M and $20M ARR and can provide specific benchmarks for SaaS companies:
- Customer Retention Rate: You know that median SaaS companies achieve 80-85% retention, while top quartile companies exceed 90%. This metric reveals product value and customer satisfaction.
- Gross Revenue Retention: You advise that healthy SaaS companies maintain 85-90% (median) to 95%+ (top quartile) GRR, indicating product/service stickiness.
- Net Revenue Retention: You emphasize that successful companies achieve 100-110% (median) to 120%+ (top quartile) NRR, demonstrating customer success effectiveness.
- Customer Acquisition Cost by GTM Channel: You help companies optimize their channel mix, targeting a minimum 1:3 CAC:LTV ratio, with top performers achieving 1:5+.
- Win Rate: You benchmark sales effectiveness at 20-30% (median) to 40%+ (top quartile) win rates, reflecting competitive positioning.
- Expansion Revenue %: You guide companies to target 20-30% of new ARR from existing customers (median), with top performers exceeding 40%.
- LTV:CAC ratio: You emphasize that sustainable business models maintain a company ratio greater than 3:1.
- Sales Velocity: You help companies measure and improve their revenue generation capacity through the formula: Opportunities × win rate × deal size ÷ sales cycle, targeting month-over-month increases.

You understand that shifting from 'grow at all costs' to engineered growth is crucial in the post-2022 economic landscape where investors demand profitability alongside expansion. And you know that many of today's executives built successful careers on the growth at all costs model, and/or by using outdated methodologies & frameworks, so it's important to use data and hard facts to show why a new approach is needed to create viable, healthy companies.

Based on the above expertise, suggest follow-up questions that dive deeper into revenue architecture, metrics alignment, and GTM optimization."""
        
        # Call the API directly with the detailed system prompt
        payload = {
            "model": st.session_state.current_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300
        }
        
        # Use the existing headers from the LlmApi class
        response = httpx.post(
            OPENROUTER_API_URL,
            headers=st.session_state.llm_api.headers,
            json=payload,
            timeout=API_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            suggestions_text = result["choices"][0]["message"]["content"]
            
            # Extract questions from the numbered list
            questions = []
            for line in suggestions_text.split('\n'):
                # Look for numbered lines (1. Question) or bulleted lines (• Question)
                match = re.search(r'(?:\d+\.|\*|\•)\s*(.*?)(?:\?|$)', line)
                if match:
                    question = match.group(1).strip()
                    if not question.endswith('?'):
                        question += '?'
                    questions.append(question)
            
            # Ensure we have exactly 4 questions
            return questions[:4] if len(questions) >= 4 else questions
        else:
            print("WARNING: Unexpected response structure for follow-up questions")
            return []
    except Exception as e:
        print(f"Error generating follow-up questions: {str(e)}")
        traceback.print_exc()
        return []

# Function to handle clicking a follow-up question
def handle_follow_up_click(question):
    """Process the selected follow-up question"""
    # This function is called when a follow-up question is clicked
    process_input(question)
    # Force a rerun to update the UI
    st.rerun()

# Apply our exception handler to the run_sql_cached function to handle errors gracefully
@handle_exception
def safe_run_sql(sql_query, question):
    """A wrapper around run_sql_cached that handles exceptions gracefully"""
    return run_sql_cached(sql=sql_query)

# Function to process user input with data analysis if enabled
def process_input(user_input):
    # Phase 1: Generate and display the response
    # Phase 2: Generate follow-up questions
    
    # If we're in phase 2 (waiting for follow-up generation after displaying response)
    if st.session_state.waiting_for_followup:
        with st.spinner("Generating follow-up questions..."):
            # Get the latest response from the conversation history
            latest_response = st.session_state.messages[-1]["content"]
            follow_up_questions = generate_follow_up_questions(latest_response)
            st.session_state.follow_up_questions = follow_up_questions
            
            # Reset the waiting flag
            st.session_state.waiting_for_followup = False
            st.session_state.loading = False
        return
        
    # Otherwise, we're in phase 1: process the input and generate a response
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
    
    # Set flag to indicate we need to generate follow-up questions after rendering
    st.session_state.waiting_for_followup = True
    
    # We need to rerun to render the response before generating follow-up questions
    st.rerun()

# Sidebar for user identification and settings
with st.sidebar:
    st.title("Elevate AI Companion")
    
    # User identification
    if st.session_state.user_id is None:
        user_id = st.text_input("Enter your username:")
        if st.button("Start Session") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id)
            st.session_state.llm_api = LlmApi()  # Initialize LLM API for follow-up questions
            st.rerun()
    else:
        st.write(f"Active User: **{st.session_state.user_id}**")
        
        # Model selector
        st.subheader("Model Settings")
        model_options = ["openai/o3", "openai/gpt-4o-2024-11-20"]
        selected_model = st.selectbox(
            "Select LLM Model:",
            options=model_options,
            index=model_options.index(st.session_state.current_model),
            key="model_selector"
        )
        
        # Update model if changed
        if selected_model != st.session_state.current_model:
            with st.spinner(f"Switching to {selected_model}..."):
                update_model(selected_model)
                st.session_state.current_model = selected_model
                st.success(f"Model switched to {selected_model}")
        
        st.divider()
        
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
    
    # Check if we need to process follow-up questions after displaying the response
    if st.session_state.waiting_for_followup:
        process_input(None)  # Call process_input again with None to generate follow-up questions
    
    # Display follow-up question bubbles if available
    if st.session_state.follow_up_questions:
        st.write("**Suggested Follow-up Questions:**")
        cols = st.columns(len(st.session_state.follow_up_questions))
        for i, question in enumerate(st.session_state.follow_up_questions):
            # Create a clickable button for each question
            if cols[i].button(question, key=f"follow_up_{i}", use_container_width=True):
                handle_follow_up_click(question)
    
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
            disabled=st.session_state.loading or not st.session_state.user_id or st.session_state.waiting_for_followup
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