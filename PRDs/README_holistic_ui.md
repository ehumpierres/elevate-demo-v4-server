# Mem0 AI Companion with Data Analysis

This application provides a Streamlit-based user interface for interacting with the Mem0 AI Companion, enhanced with optional data analysis capabilities powered by the Vanna Agent.

## Features

- Interactive chat interface with the Mem0 AI Companion
- Long-term and short-term memory capabilities
- Optional data analysis through the Vanna Agent
- Data visualization using Streamlit's native plotting capabilities
- Clean, modern UI with a sidebar for user management

## How to Run

1. Ensure all dependencies are installed:
   ```
   pip install streamlit pandas numpy
   ```

2. Run the Streamlit application:
   ```
   streamlit run src/ui/holistic_ui.py
   ```

3. Open the provided URL in your web browser (usually http://localhost:8501)

## Using the Application

1. **Start a Session**: Enter your username in the sidebar and click "Start Session"

2. **Chat with Mem0**: Type your messages in the chat input at the bottom of the screen

3. **Enable Data Analysis**: Toggle the "Invite Data Analyst Agent" button next to the chat input to enable data analysis capabilities

4. **View Data Results**:
   - When data analysis is enabled, relevant queries will return data tables
   - Data is displayed with proper formatting (thousands separators, two decimal places)
   - SQL queries are available in expandable sections
   - Visualizations are automatically generated for the data

5. **Clear Cache**: Use the "Clear Cache" button in the sidebar to reset the session state

## Architecture

This application integrates:

- **Mem0 Companion Agent** (`src/companion.py`): Provides the conversational AI with memory capabilities
- **Vanna Agent** (`src/ui/vanna_calls.py` and `src/vanna_scripts/vanna_snowflake.py`): Handles data analysis through SQL generation and execution
- **Streamlit UI** (`src/ui/holistic_ui.py`): Combines both agents in a clean, modern interface

## Features in Detail

### Chat Interface
- Clean, modern design using Streamlit's native chat components
- Message history maintained throughout the session
- Active user displayed in the sidebar

### Data Analysis
- Toggle button to enable/disable the Data Analyst Agent
- SQL generation and execution via Vanna
- Data results formatted with proper thousands separators and decimal places
- Row indices start from 1 (not 0)

### Visualization
- Automatic visualization of data results using Streamlit's native plotting capabilities
- Smart detection of date/time columns for x-axis
- Proper formatting of numeric values in charts

### User Experience
- Loading indicators during processing
- Easy navigation via the sidebar
- Session persistence with clear cache option 