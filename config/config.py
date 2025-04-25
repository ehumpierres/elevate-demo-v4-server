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
OPENROUTER_MODEL = "openai/o3"
API_TIMEOUT = 30.0  # seconds

# Memory Settings
OUTPUT_FORMAT = "v1.1"  # Mem0 output format 