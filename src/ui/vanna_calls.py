import streamlit as st
import pandas as pd
import json
import sys
import os
import time
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.vanna_scripts.vanna_snowflake import VannaSnowflake

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded from .env file")

# Initialize Vanna instance with proper cleanup
@st.cache_resource(ttl=1800)  # Cache for 30 minutes to ensure more frequent reconnection
def get_vanna_instance():
    try:
        logger.info("Initializing Vanna instance")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OpenAI API key is not set. Please set it in your .env file.")
            raise ValueError("OpenAI API key is not set. Please set it in your .env file.")
        
        # Check for Snowflake environment variables
        required_vars = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", 
                        "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            missing_list = ", ".join(missing_vars)
            logger.error(f"Missing required Snowflake environment variables: {missing_list}")
            raise ValueError(f"Missing required Snowflake environment variables: {missing_list}")
        
        # Check authentication method
        has_auth = False
        if os.environ.get("SNOWFLAKE_PRIVATE_KEY_BASE64"):
            has_auth = True
            auth_method = "base64 private key"
            logger.info("Using base64 encoded private key for Snowflake authentication")
        elif os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH") and os.path.exists(os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")):
            has_auth = True
            auth_method = "private key file"
            logger.info(f"Using private key file for Snowflake authentication: {os.environ.get('SNOWFLAKE_PRIVATE_KEY_PATH')}")
        elif os.environ.get("SNOWFLAKE_PASSWORD"):
            has_auth = True
            auth_method = "password"
            logger.info("Using password authentication for Snowflake")
        
        if not has_auth:
            logger.error("No Snowflake authentication method available")
            raise ValueError("No Snowflake authentication method available. Please set SNOWFLAKE_PRIVATE_KEY_BASE64, SNOWFLAKE_PRIVATE_KEY_PATH, or SNOWFLAKE_PASSWORD")
        
        logger.info(f"Creating VannaSnowflake instance with {auth_method} authentication")
        vanna = VannaSnowflake(openai_api_key=openai_api_key)
        
        # Test database connection before training
        try:
            logger.info("Testing Snowflake connection with simple query")
            test_result = vanna.test_connection()
            if test_result:
                logger.info("Snowflake connection test successful")
            else:
                logger.error("Snowflake connection test failed")
                st.error("Failed to connect to Snowflake database. Please check your credentials.")
        except Exception as e:
            logger.error(f"Snowflake connection test failed with error: {str(e)}")
            st.error(f"Failed to connect to Snowflake: {str(e)}")
            raise
        
        # Execute training
        logger.info("Beginning Vanna training process")
        try:
            vanna.train()
            logger.info("Vanna training completed successfully")
        except Exception as e:
            logger.error(f"Vanna training failed: {str(e)}")
            logger.debug(f"Training error details: {traceback.format_exc()}")
            st.error(f"Error during Vanna training: {str(e)}")
            raise
        
        # Register a resource cleanup function
        def cleanup():
            if vanna:
                logger.info("Cleaning up Vanna instance and closing connections")
                try:
                    vanna.close()
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")
        
        # Register the cleanup function to be called when the resource is garbage collected
        try:
            st._cache_resource_garbage_collection_callbacks.append(cleanup)
            logger.debug("Registered cleanup callback for Vanna instance")
        except Exception as e:
            logger.warning(f"Unable to register cleanup callback: {str(e)}")
        
        return vanna
    
    except Exception as e:
        logger.error(f"Failed to initialize Vanna instance: {str(e)}")
        logger.debug(f"Initialization error details: {traceback.format_exc()}")
        st.error(f"Failed to initialize data connection: {str(e)}")
        raise

# Generate SQL from a question
@st.cache_data(ttl=600)  # Cache for 10 minutes
def generate_sql_cached(question):
    try:
        logger.info(f"Generating SQL for question: {question}")
        vanna = get_vanna_instance()
        
        start_time = time.time()
        sql = vanna.generate_sql(question)
        execution_time = time.time() - start_time
        
        if sql:
            logger.info(f"SQL generated successfully in {execution_time:.2f} seconds")
            logger.debug(f"Generated SQL: {sql}")
            return sql
        else:
            logger.warning("Empty SQL generated")
            return None
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        logger.debug(f"SQL generation error details: {traceback.format_exc()}")
        # Re-raise so it can be handled by the UI
        raise

# Run the SQL query and return results
@st.cache_data(ttl=300)  # Cache for 5 minutes
def run_sql_cached(sql):
    try:
        if not sql:
            logger.error("Attempted to run empty SQL query")
            raise ValueError("Cannot execute empty SQL query")
            
        logger.info(f"Executing SQL query: {sql[:100]}...")
        vanna = get_vanna_instance()
        
        start_time = time.time()
        results = vanna.execute_sql(sql)
        execution_time = time.time() - start_time
        
        if isinstance(results, list) and len(results) > 0:
            logger.info(f"Query executed successfully in {execution_time:.2f} seconds, returned {len(results)} rows")
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(results)
            return df
        else:
            logger.warning(f"Query executed in {execution_time:.2f} seconds but returned no results")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        logger.debug(f"SQL execution error details: {traceback.format_exc()}")
        # Re-raise so it can be handled by the UI
        raise

# Check if SQL is valid
@st.cache_data
def is_sql_valid_cached(sql):
    if not sql or len(sql) < 5:
        logger.warning(f"SQL validation failed - too short: {sql}")
        return False
    
    # Basic check for SELECT statement
    sql_lower = sql.lower().strip()
    if not sql_lower.startswith("select"):
        logger.warning(f"SQL validation failed - not a SELECT query: {sql[:50]}...")
        return False
    
    logger.debug(f"SQL validation passed for query: {sql[:50]}...")
    return True

# Function to clear all caches - useful to reset connections
def clear_all_caches():
    """Clear all Streamlit caches to force reconnection to Snowflake"""
    logger.info("Clearing all data caches")
    st.cache_data.clear()
    
    logger.info("Forcing resource cache clear to reinitialize connections")
    st.cache_resource.clear()
    
    logger.info("All caches cleared, connections will be reestablished")
    
# Function to verify Snowflake connection is working
def test_snowflake_connection():
    """Test the Snowflake connection and return detailed results"""
    try:
        logger.info("Testing Snowflake connection")
        vanna = get_vanna_instance()
        result = vanna.test_connection(detailed=True)
        logger.info(f"Connection test result: {result}")
        return result
    except Exception as e:
        logger.error(f"Connection test failed with error: {str(e)}")
        logger.debug(f"Connection test error details: {traceback.format_exc()}")
        return {"success": False, "error": str(e), "details": traceback.format_exc()} 