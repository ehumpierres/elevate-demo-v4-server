import streamlit as st
import pandas as pd
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.vanna_scripts.vanna_snowflake import VannaSnowflake

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Vanna instance
@st.cache_resource
def get_vanna_instance():
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OpenAI API key is not set. Please set it in your .env file.")
    
    vanna = VannaSnowflake(openai_api_key=openai_api_key)
    vanna.train()
    return vanna

# Generate SQL from a question
@st.cache_data
def generate_sql_cached(question):
    try:
        vanna = get_vanna_instance()
        sql = vanna.generate_sql(question)
        return sql
    except Exception as e:
        st.error(f"Error generating SQL: {str(e)}")
        return None

# Run the SQL query and return results
@st.cache_data
def run_sql_cached(sql):
    try:
        vanna = get_vanna_instance()
        results = vanna.execute_sql(sql)
        
        if isinstance(results, list) and len(results) > 0:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(results)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error executing SQL: {str(e)}")
        return None

# Check if SQL is valid
@st.cache_data
def is_sql_valid_cached(sql):
    if not sql or len(sql) < 5:
        return False
    return True 