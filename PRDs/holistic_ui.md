# Streamlit Chat Interface for Mem0 Agent with Data Analysis Capabilities

## Overview
Build a new Streamlit-based user interface that provides an interactive chat experience with the Mem0 agent (from companion.py), enhanced with optional data analysis capabilities.

## Core Requirements

### Chat Interface
- Create a clean, modern chat interface using native Streamlit components
- Set up the primary conversation flow between users and the Mem0 Companion agent (the one on companion.py)
- Ensure the Mem0 agent utilizes both short-term and long-term memory capabilities as designed in companion.py

### Data Analysis Agent Integration
-Add a toggle button labeled "Invite Data Analyst Agent" next to the prompt input field
- When enabled, submitted queries will be:
    - Processed by the Vanna Agent for data analysis (see vanna_calls.py and vanna_snowflake.py)
    - The resulting data will be fed to the Mem0 agent along with other context from memory and system prompts

- Pass only processed data tables to Mem0 Companion Agent (not raw SQL) in the format that best supports memory storage (DataFrame, markdown, or JSON). You will have to add the this response variable as an input in the prompt feed to thwe Mem0 Companion Agent

### Response Display
- Show the Mem0 agent's conversational response prominently
- Display the data table produced by the Data Analyst Agent with:
    - Row indices starting from 1 (not 0)
    - Numerical values formatted with thousands separators (commas) and two decimal places

- Include the generated SQL query used by the Data Analyst Agent in its query
- Create a visualization of the data using Streamlit's native plotting capabilities (not Plotly)
- When the system is processing a response add some moving icon or loader icon so users do not get bored waiting

### Sidebar Navigation
- Display the currently active user in the left sidebar
- Include a "Clear Cache" button in the sidebar to reset the session state

### Technical Considerations
- Ensure proper integration with the existing Mem0 agent implementation in companion.py
- Design the UI to gracefully handle both text-only and data-enhanced conversations

### User Experience Goals
- Provide seamless transitions between conversational and analytical modes
- Maintain context across multiple turns of conversation
- Present data in an accessible, easy-to-understand format