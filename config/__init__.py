"""
Configuration module for Vanna.ai Snowflake Explorer
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Snowflake Configuration
SNOWFLAKE_ACCOUNT = os.environ.get("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.environ.get("SNOWFLAKE_USER", "")
SNOWFLAKE_ORG = os.environ.get("SNOWFLAKE_ORG", "")
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "")
SNOWFLAKE_ROLE = os.environ.get("SNOWFLAKE_ROLE", "")
SNOWFLAKE_DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "")
SNOWFLAKE_SCHEMA = os.environ.get("SNOWFLAKE_SCHEMA", "")
SNOWFLAKE_PRIVATE_KEY_PATH = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "snowflake_keys/rsa_key.p8")

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# ChromaDB Configuration
CHROMA_PERSISTENCE_DIRECTORY = os.environ.get("CHROMA_PERSISTENCE_DIRECTORY", "data/chroma_db")
CHROMA_COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION_NAME", "vanna_snowflake")

# Vanna.AI Configuration
VANNA_MODEL_NAME = os.environ.get("VANNA_MODEL_NAME", "gpt-4o")  # Default to GPT-4 for Vanna
VANNA_DIALECT = os.environ.get("VANNA_DIALECT", "snowflake") 