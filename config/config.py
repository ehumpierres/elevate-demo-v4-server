"""
Configuration settings for the AI companion application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Agent Settings
COMPANION_ID = "revenue_architect"
SHORT_TERM_MEMORY_SIZE = 20  # Number of recent messages to keep

# Storage Settings
DATA_DIRECTORY = "data"
JSON_FILE_EXTENSION = ".json"

# API Settings
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-4o-2024-11-20"
API_TIMEOUT = 30.0  # seconds

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