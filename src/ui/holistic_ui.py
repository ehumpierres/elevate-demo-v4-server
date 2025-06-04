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

# Import persona modules for analyst selection
from config.persona import get_system_prompt as get_arabella_prompt
from config.motions_analyst import get_system_prompt as get_motions_analyst_prompt

# Import Vanna functionality for data analysis (now integrated into Companion)
from src.ui.vanna_calls import (
    clear_all_caches,
    test_snowflake_connection
)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "companion" not in st.session_state:
    st.session_state.companion = None

if "loading" not in st.session_state:
    st.session_state.loading = False

if "current_model" not in st.session_state:
    st.session_state.current_model = OPENROUTER_MODEL

if "follow_up_questions" not in st.session_state:
    st.session_state.follow_up_questions = []

if "llm_api" not in st.session_state:
    st.session_state.llm_api = None

# Add a new state variable for the warm start trigger
if "trigger_warm_start" not in st.session_state:
    st.session_state.trigger_warm_start = False

# Add a new state variable for tracking the two-phase process
if "waiting_for_followup" not in st.session_state:
    st.session_state.waiting_for_followup = False

# Add a state variable to store the last user input for processing follow-ups
if "last_user_input" not in st.session_state:
    st.session_state.last_user_input = None

# Add a new state variable for selected follow-up question
if "selected_follow_up" not in st.session_state:
    st.session_state.selected_follow_up = None

# Add session state for analyst selection
if "selected_analyst" not in st.session_state:
    st.session_state.selected_analyst = "Sales Motion Strategy Agent"

# Add session state for streaming support
if "streaming_enabled" not in st.session_state:
    st.session_state.streaming_enabled = True

# Add a new state variable for tracking streaming status
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False

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

# Function to clean markdown formatting from LLM responses
def clean_markdown_formatting(text):
    """Remove markdown formatting that doesn't render well in Streamlit"""
    if not text:
        return text
    
    # Remove bold formatting (**text** -> text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove italic formatting (*text* -> text) - but be careful not to remove bullet points
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'\1', text)
    
    # Clean up any remaining single asterisks that might be left over
    # but preserve bullet points (lines starting with *)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Don't clean asterisks at the beginning of lines (bullet points)
        if line.strip().startswith('*'):
            cleaned_lines.append(line)
        else:
            # Remove stray asterisks in the middle of sentences
            cleaned_line = re.sub(r'(?<!\s)\*(?!\s)', '', line)
            cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)

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
        
        # Add streaming support if enabled (though for follow-up questions we'll keep it simple)
        if st.session_state.streaming_enabled:
            payload["stream"] = False  # Keep follow-up generation non-streaming for simplicity
        
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
    # Save the selected question for display
    st.session_state.selected_follow_up = question
    # Clear the follow-up questions list
    st.session_state.follow_up_questions = []
    # Process the question
    process_input(question)
    # Force a rerun to update the UI
    st.rerun()

# Function to process user input with streaming support
def process_input_stream(user_input):
    """Process user input with streaming response support and progressive UI feedback"""
    # Phase 1: Generate and display the streaming response
    # Phase 2: Generate follow-up questions (simplified, no background threading)
    
    # If we're in phase 2 (waiting for follow-up generation after displaying response)
    if st.session_state.waiting_for_followup:
        # Generate follow-ups directly (no background threading to avoid Streamlit issues)
        with st.spinner("Generating follow-up questions..."):
            try:
                # Get the latest response from the conversation history
                latest_response = st.session_state.messages[-1]["content"]
                follow_up_questions = generate_follow_up_questions(latest_response)
                st.session_state.follow_up_questions = follow_up_questions
                
                # Reset flags
                st.session_state.waiting_for_followup = False
                st.session_state.loading = False
                st.session_state.selected_follow_up = None
                st.session_state.is_streaming = False
                
            except Exception as e:
                print(f"Error generating follow-up questions: {e}")
                # Still reset flags even if follow-up generation fails
                st.session_state.waiting_for_followup = False
                st.session_state.loading = False
                st.session_state.is_streaming = False
        return
        
    # Otherwise, we're in phase 1: process the input and generate a streaming response
    st.session_state.loading = True
    st.session_state.is_streaming = True
    
    # Add the user message to the conversation history first
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display the user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Create the assistant message container with immediate thinking indicator
    with st.chat_message("assistant"):
        # Show immediate thinking feedback
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🧠 *Analyzing your question and preparing response...*")
        
        # Show data analysis detection feedback if applicable
        if st.session_state.companion._should_use_data_analysis(user_input):
            thinking_placeholder.markdown("🧠 *Analyzing your question...*\n\n📊 *Data analysis detected - querying database...*")
        
        try:
            # Show preparation phase
            with st.spinner("🤖 AI Assistant is preparing your response..."):
                # Get both the streaming generator and metadata from companion
                stream_generator, metadata = st.session_state.companion.process_message_stream(user_input)
            
            # Clear thinking indicator and start streaming
            thinking_placeholder.empty()
            
            # Add a streaming-specific loading indicator
            streaming_placeholder = st.empty()
            streaming_placeholder.markdown("🌊 *Waiting for first response chunk...*")
            
            # Use Streamlit's streaming capability with improved handling
            try:
                streamed_text = st.write_stream(stream_generator)
                # Clear the streaming placeholder once content starts appearing
                streaming_placeholder.empty()
            except Exception as stream_error:
                streaming_placeholder.empty()
                st.error(f"Streaming error: {str(stream_error)}")
                raise stream_error
            
            # Fix spacing issues in revenue text formatting
            full_response = fix_revenue_text_spacing(streamed_text)
            
            # Clean markdown formatting that doesn't render well
            full_response = clean_markdown_formatting(full_response)
            
        except Exception as e:
            thinking_placeholder.empty()
            st.error(f"Error during streaming: {str(e)}")
            full_response = f"I encountered an error while generating my response: {str(e)}"
            metadata = {"data_analysis": None}
        
        # Display data analysis results immediately if available
        data_analysis = metadata.get("data_analysis")
        if data_analysis:
            st.subheader("📊 Data Analysis Results")
            
            # Convert list of dictionaries to DataFrame for display
            try:
                df = pd.DataFrame(data_analysis.get("results", []))
                
                if not df.empty:
                    # Set row indices to start from 1
                    df.index = np.arange(1, len(df) + 1)
                    
                    # Format and display the data
                    formatted_df = format_numeric_values(df)
                    st.dataframe(formatted_df, use_container_width=True)
                    
                    # Show query metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows Returned", data_analysis.get("row_count", len(df)))
                    with col2:
                        st.metric("Execution Time", f"{data_analysis.get('execution_time_ms', 0)}ms")
                    with col3:
                        st.metric("Columns", len(df.columns))
                    
                    # Show the SQL query used
                    if data_analysis.get("sql"):
                        with st.expander("SQL Query"):
                            st.code(data_analysis.get("sql"), language="sql")
                    
                    # Create visualization
                    create_visualization(df)
                else:
                    st.info("Query executed successfully but returned no data.")
                    
            except Exception as e:
                st.error(f"Error displaying data: {e}")
                # Show raw data as fallback
                with st.expander("Raw Data"):
                    st.json(data_analysis.get("results", []))
    
    # Add the complete assistant response to the conversation history
    assistant_message = {"role": "assistant", "content": full_response}
    
    # If we have data analysis results, store them in the message for display
    if data_analysis:
        assistant_message["data"] = data_analysis.get("results", [])
        assistant_message["sql"] = data_analysis.get("sql", "")
        assistant_message["row_count"] = data_analysis.get("row_count", 0)
        assistant_message["execution_time"] = data_analysis.get("execution_time_ms", 0)
    
    st.session_state.messages.append(assistant_message)
    
    # Set flag to indicate we need to generate follow-up questions (but don't rerun immediately)
    st.session_state.waiting_for_followup = True
    st.session_state.is_streaming = False
    st.session_state.loading = False
    
    # Trigger rerun to show follow-up questions
    st.rerun()

# Function to process user input with data analysis if enabled
def process_input(user_input):
    """Process user input with progressive UI feedback"""
    # Phase 1: Generate and display the response
    # Phase 2: Generate follow-up questions (simplified, no background threading)
    
    # If we're in phase 2 (waiting for follow-up generation after displaying response)
    if st.session_state.waiting_for_followup:
        # Generate follow-ups directly (no background threading to avoid Streamlit issues)
        with st.spinner("Generating follow-up questions..."):
            try:
                # Get the latest response from the conversation history
                latest_response = st.session_state.messages[-1]["content"]
                follow_up_questions = generate_follow_up_questions(latest_response)
                st.session_state.follow_up_questions = follow_up_questions
                
                # Reset flags
                st.session_state.waiting_for_followup = False
                st.session_state.loading = False
                st.session_state.selected_follow_up = None
                
            except Exception as e:
                print(f"Error generating follow-up questions: {e}")
                # Still reset flags even if follow-up generation fails
                st.session_state.waiting_for_followup = False
                st.session_state.loading = False
        return
        
    # Check if streaming is enabled, if so use streaming process
    if st.session_state.streaming_enabled:
        return process_input_stream(user_input)
        
    # Otherwise, we're in phase 1: process the input and generate a response (non-streaming)
    st.session_state.loading = True
    
    # Add the user message to the conversation history first
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display the user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Create the assistant message container with immediate thinking indicator
    with st.chat_message("assistant"):
        # Show immediate thinking feedback
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("🧠 *Analyzing your question and preparing response...*")
        
        # Show data analysis detection feedback if applicable
        if st.session_state.companion._should_use_data_analysis(user_input):
            thinking_placeholder.markdown("🧠 *Analyzing your question...*\n\n📊 *Data analysis detected - querying database...*")
        
        try:
            # Process the user input through the enhanced Companion (now includes data analysis)
            with st.spinner("🤖 AI Assistant is thinking..."):
                # The Companion now handles data analysis automatically
                result = st.session_state.companion.process_message(user_input)
                
                # Handle the new response format
                if isinstance(result, dict) and "response" in result:
                    response = result["response"]
                    data_analysis = result.get("data_analysis")
                else:
                    # Fallback for simple string response (shouldn't happen with new Companion)
                    response = str(result)
                    data_analysis = None
                
                # Fix spacing issues in revenue text formatting
                response = fix_revenue_text_spacing(response)
                
                # Clean markdown formatting that doesn't render well
                response = clean_markdown_formatting(response)
            
            # Clear thinking indicator and show response
            thinking_placeholder.empty()
            st.write(response)
            
        except Exception as e:
            thinking_placeholder.empty()
            st.error(f"Error during processing: {str(e)}")
            response = f"I encountered an error while generating my response: {str(e)}"
            data_analysis = None
        
        # Display data analysis results immediately if available
        if data_analysis:
            st.subheader("📊 Data Analysis Results")
            
            # Convert list of dictionaries to DataFrame for display
            try:
                df = pd.DataFrame(data_analysis.get("results", []))
                
                if not df.empty:
                    # Set row indices to start from 1
                    df.index = np.arange(1, len(df) + 1)
                    
                    # Format and display the data
                    formatted_df = format_numeric_values(df)
                    st.dataframe(formatted_df, use_container_width=True)
                    
                    # Show query metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows Returned", data_analysis.get("row_count", len(df)))
                    with col2:
                        st.metric("Execution Time", f"{data_analysis.get('execution_time_ms', 0)}ms")
                    with col3:
                        st.metric("Columns", len(df.columns))
                    
                    # Show the SQL query used
                    if data_analysis.get("sql"):
                        with st.expander("SQL Query"):
                            st.code(data_analysis.get("sql"), language="sql")
                    
                    # Create visualization
                    create_visualization(df)
                else:
                    st.info("Query executed successfully but returned no data.")
                    
            except Exception as e:
                st.error(f"Error displaying data: {e}")
                # Show raw data as fallback
                with st.expander("Raw Data"):
                    st.json(data_analysis.get("results", []))
    
    # Add the assistant response to the conversation history
    assistant_message = {"role": "assistant", "content": response}
    
    # If we have data analysis results, store them in the message for display
    if data_analysis:
        assistant_message["data"] = data_analysis.get("results", [])
        assistant_message["sql"] = data_analysis.get("sql", "")
        assistant_message["row_count"] = data_analysis.get("row_count", 0)
        assistant_message["execution_time"] = data_analysis.get("execution_time_ms", 0)
    
    st.session_state.messages.append(assistant_message)
    
    # Set flag to indicate we need to generate follow-up questions (but don't rerun immediately)
    st.session_state.waiting_for_followup = True
    st.session_state.loading = False
    
    # Trigger rerun to show follow-up questions
    st.rerun()

# Sidebar for user identification and settings
with st.sidebar:
    st.title("Elevate AI Companion")
    
    # User identification
    if st.session_state.user_id is None:
        user_id = st.text_input("Enter your username:")
        
        # Create columns for the two buttons
        col1, col2 = st.columns(2)
        
        # Regular start button
        if col1.button("Start Session") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id, analyst_type=st.session_state.selected_analyst)
            st.session_state.llm_api = LlmApi()  # Initialize LLM API for follow-up questions
            st.rerun()
        
        # Warm start button
        if col2.button("Warm Start") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id, analyst_type=st.session_state.selected_analyst)
            st.session_state.llm_api = LlmApi()  # Initialize LLM API for follow-up questions
            # Set a flag to trigger the warm start prompt after rerun
            st.session_state.trigger_warm_start = True
            st.rerun()
    else:
        st.write(f"Active User: **{st.session_state.user_id}**")
        
        # Analyst selector
        st.subheader("AI Assistant")
        analyst_options = ["Arabella (Business Architect)", "Sales Motion Strategy Agent"]
        selected_analyst = st.selectbox(
            "Select AI Assistant:",
            options=analyst_options,
            index=analyst_options.index(st.session_state.selected_analyst),
            key="analyst_selector"
        )
        
        # Update analyst if changed (this will require reinitializing the companion)
        if selected_analyst != st.session_state.selected_analyst:
            # Close the existing companion properly
            if st.session_state.companion:
                try:
                    st.session_state.companion.close()
                    print(f"✅ UI: Closed {st.session_state.selected_analyst} session")
                except Exception as e:
                    print(f"⚠️ UI: Error closing companion during analyst switch: {e}")
            
            st.session_state.selected_analyst = selected_analyst
            # Reinitialize companion with new analyst
            st.session_state.companion = Companion(st.session_state.user_id, analyst_type=selected_analyst)
            st.success(f"🔄 Switched to {selected_analyst} (previous session closed)")
        
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
        
        # Streaming toggle
        st.subheader("Response Settings")
        streaming_enabled = st.toggle(
            "🌊 Streaming Responses",
            value=st.session_state.streaming_enabled,
            help="Enable real-time streaming of AI responses for faster interaction"
        )
        
        # Update streaming setting if changed
        if streaming_enabled != st.session_state.streaming_enabled:
            st.session_state.streaming_enabled = streaming_enabled
            if streaming_enabled:
                st.success("✅ Streaming mode enabled - responses will appear in real-time!")
            else:
                st.info("ℹ️ Streaming mode disabled - responses will appear all at once")
        
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
        
        # Train Vanna.AI button
        if st.button("🎓 Train SQL Model"):
            with st.spinner("Training Vanna.AI model... This may take several minutes."):
                try:
                    # Import and initialize VannaSnowflake for training
                    from src.vanna_scripts.vanna_snowflake import VannaSnowflake
                    
                    # Show progress steps
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔗 Testing Snowflake connection...")
                    progress_bar.progress(10)
                    
                    # Initialize VannaSnowflake
                    vanna = VannaSnowflake()
                    
                    # Test connection first
                    connection_test = vanna.test_connection(detailed=True)
                    
                    if not connection_test.get("success", False):
                        st.error(f"❌ Connection test failed: {connection_test.get('error', 'Unknown error')}")
                        progress_bar.empty()
                        status_text.empty()
                    else:
                        status_text.text(f"✅ Connected to {connection_test['database']}.{connection_test['schema']}")
                        progress_bar.progress(30)
                        
                        status_text.text("🎓 Training AI model on database schema and examples...")
                        progress_bar.progress(50)
                        
                        # Run training
                        training_result = vanna.train()
                        
                        if training_result:
                            progress_bar.progress(90)
                            status_text.text("📊 Getting training statistics...")
                            
                            # Get training statistics
                            try:
                                from src.vanna_scripts.show_training_data import TrainingDataViewer
                                viewer = TrainingDataViewer()
                                stats = viewer.get_stats()
                                
                                progress_bar.progress(100)
                                status_text.text("✅ Training completed successfully!")
                                
                                st.success("🎉 Vanna.AI model training completed successfully!")
                                
                                # Display training statistics
                                st.info(f"""
                                **Training Summary:**
                                - Total entries: {stats['total_entries']}
                                - DDL statements: {stats['ddl_count']}
                                - Documentation entries: {stats['documentation_count']}
                                - SQL examples: {stats['sql_count']}
                                - Q&A pairs: {stats['qa_pairs_count']}
                                """)
                                
                            except Exception as e:
                                st.warning(f"⚠️ Could not get training statistics: {e}")
                                st.success("✅ Training completed successfully!")
                        else:
                            st.error("❌ Training failed!")
                        
                        # Close connections
                        vanna.close()
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                except Exception as e:
                    st.error(f"❌ Training process failed: {str(e)}")
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
            # Properly close companion session before clearing
            if st.session_state.companion:
                try:
                    st.session_state.companion.close()
                    print("✅ UI: Companion session closed properly")
                except Exception as e:
                    print(f"⚠️ UI: Error closing companion: {e}")
            
            # Reset all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("🔄 Cache cleared and session closed!")
            st.rerun()

# Main content area - only show if user is identified
if st.session_state.user_id:
    # Display chat header with selected analyst
    analyst_name = st.session_state.selected_analyst
    st.title(f"Elevate AI Companion - {analyst_name}")
    st.caption("An intelligent business strategist with integrated data analysis and memory capabilities")
    
    # Check for the trigger_warm_start flag and process the warm start prompt
    if st.session_state.trigger_warm_start:
        initial_prompt = "Give me a status of the most recent financial milestones and business risks, and show me the revenue for the last quarter, be succinct"
        st.session_state.trigger_warm_start = False
        process_input(initial_prompt)
    
    # Display chat messages (skip if currently streaming to avoid duplication)
    if not st.session_state.is_streaming:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # Apply both text formatting functions to all displayed messages to ensure proper formatting
                formatted_content = fix_revenue_text_spacing(message["content"])
                formatted_content = clean_markdown_formatting(formatted_content)
                st.write(formatted_content)
                
                # If this message has data attached, display it
                if "data" in message and message["data"]:
                    st.subheader("Data Analysis Results")
                    
                    # Convert list of dictionaries to DataFrame for display
                    try:
                        df = pd.DataFrame(message["data"])
                        
                        if not df.empty:
                            # Set row indices to start from 1
                            df.index = np.arange(1, len(df) + 1)
                            
                            # Format and display the data
                            formatted_df = format_numeric_values(df)
                            st.dataframe(formatted_df, use_container_width=True)
                            
                            # Show query metadata
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Rows Returned", message.get("row_count", len(df)))
                            with col2:
                                st.metric("Execution Time", f"{message.get('execution_time', 0)}ms")
                            with col3:
                                st.metric("Columns", len(df.columns))
                            
                            # Show the SQL query used
                            if "sql" in message and message["sql"]:
                                with st.expander("SQL Query"):
                                    st.code(message["sql"], language="sql")
                            
                            # Create visualization
                            create_visualization(df)
                        else:
                            st.info("Query executed successfully but returned no data.")
                            
                    except Exception as e:
                        st.error(f"Error displaying data: {e}")
                        # Show raw data as fallback
                        with st.expander("Raw Data"):
                            st.json(message["data"])
    
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
    elif st.session_state.selected_follow_up and st.session_state.loading:
        # Show only the selected question when it's being processed
        st.write("**Processing Question:**")
        st.info(st.session_state.selected_follow_up)
    
    # Chat input area
    # Chat input
    input_placeholder = "Ask me anything about business strategy or your data..."
    if st.session_state.streaming_enabled:
        input_placeholder += " (Streaming mode active 🌊)"
    
    user_input = st.chat_input(
        input_placeholder,
        disabled=st.session_state.loading or not st.session_state.user_id or st.session_state.waiting_for_followup or st.session_state.is_streaming
    )
    
    # Process input when submitted
    if user_input:
        process_input(user_input)
        st.rerun()
    
    # Loading indicator with streaming awareness and optimization status
    if st.session_state.loading or st.session_state.is_streaming:
        if st.session_state.is_streaming:
            st.markdown("🌊 **Streaming response in real-time...**")
        else:
            st.markdown("🧠 **AI Assistant is thinking...**")
        
        # Show optimization status
        if st.session_state.companion:
            try:
                # Show batch write status if available
                if hasattr(st.session_state.companion.memory_manager.short_term, 'write_buffer'):
                    buffer_size = len(st.session_state.companion.memory_manager.short_term.write_buffer)
                    if buffer_size > 0:
                        st.caption(f"📝 Memory optimization: {buffer_size} messages buffered for batch write")
            except:
                pass  # Silently handle any errors in status display
else:
    # Welcome message when no user is identified
    st.title("Welcome to Elevate AI Companion")
    st.write("Please enter your username in the sidebar to get started.") 