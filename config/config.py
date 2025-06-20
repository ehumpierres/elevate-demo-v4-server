"""
Configuration settings for the AI companion application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
MEM0_ORG_ID = os.getenv("MEM0_ORG_ID")
MEM0_PROJECT_ID = os.getenv("MEM0_PROJECT_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Agent Settings
COMPANION_ID = "revenue_architect"
SHORT_TERM_MEMORY_SIZE = 20  # Number of recent messages to keep

# Storage Settings
DATA_DIRECTORY = "data"
JSON_FILE_EXTENSION = ".json"

# Snowflake Settings
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
SNOWFLAKE_ORG = os.getenv("SNOWFLAKE_ORG")
SNOWFLAKE_PRIVATE_KEY_PATH = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
SNOWFLAKE_PRIVATE_KEY_BASE64 = os.getenv("SNOWFLAKE_PRIVATE_KEY_BASE64")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "DEMO_V4")
SNOWFLAKE_MEMORY_SCHEMA = os.getenv("SNOWFLAKE_MEMORY_SCHEMA", "CORRELATED_SCHEMA")

# API Settings
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/o3"
API_TIMEOUT = 45.0  # seconds

# Token and Context Management Settings
# Default max completion tokens for API calls - used in llm_api.py as the default parameter
DEFAULT_MAX_COMPLETION_TOKENS = 3000  # Increased from 1500 to allow longer responses

# Actual completion tokens limit used in Companion - this overrides the default when called from companion.py
COMPANION_MAX_COMPLETION_TOKENS = 2500  # Increased from 1000 to prevent truncation

# Number of recent conversation messages to include in the prompt to reduce token usage
# This determines how many short-term memory messages are passed to the API from companion.py
API_CONVERSATION_HISTORY_LIMIT = 15  # Limiting history to save tokens in prompts

# Memory Settings
OUTPUT_FORMAT = "v1.1"  # Mem0 output format 

# Function to update the model at runtime
def update_model(new_model):
    """
    Updates the OPENROUTER_MODEL at runtime.
    
    Args:
        new_model: The new model to use
    """
    global OPENROUTER_MODEL
    OPENROUTER_MODEL = new_model
    return OPENROUTER_MODEL 