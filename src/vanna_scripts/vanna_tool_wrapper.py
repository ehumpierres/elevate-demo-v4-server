import time
import logging
from typing import Dict, Any, Optional, List, Union
from .vanna_snowflake import VannaSnowflake

# Configure logging
logger = logging.getLogger(__name__)

class VannaToolWrapper:
    """
    Simple wrapper to make VannaSnowflake LLM-callable through standardized function calling interfaces.
    
    This wrapper provides standardized function schemas and response formats for AI assistants
    to invoke our existing Vanna.AI + Snowflake + ChromaDB text-to-SQL capabilities.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the VannaToolWrapper.
        
        Args:
            openai_api_key: The OpenAI API key to use. If None, it will be read from config.
        """
        logger.info("🔄 Initializing VannaToolWrapper...")
        try:
            logger.info("🚀 Creating VannaSnowflake instance...")
            self.vanna = VannaSnowflake(openai_api_key)
            logger.info("✅ VannaSnowflake instance created successfully")
            
            # Test that the vanna_ai instance is available
            if hasattr(self.vanna, 'vanna_ai') and self.vanna.vanna_ai:
                logger.info("✅ VannaSnowflake.vanna_ai is available")
            else:
                logger.warning("⚠️ VannaSnowflake.vanna_ai is not available!")
                
            logger.info("✅ VannaToolWrapper initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize VannaToolWrapper: {e}")
            logger.debug("VannaToolWrapper initialization exception:", exc_info=True)
            raise
    
    def snowflake_query(
        self, 
        question: str, 
        execute_query: bool = True, 
        max_results: int = 100
    ) -> Dict[str, Any]:
        """
        Primary tool function for natural language queries to Snowflake.
        
        Args:
            question: Natural language question about the data
            execute_query: Whether to execute the generated SQL and return results
            max_results: Maximum number of rows to return (1-1000)
            
        Returns:
            Structured response with SQL, results, and metadata
        """
        start_time = time.time()
        
        try:
            # Input validation
            if not question or not isinstance(question, str):
                logger.error(f"Invalid question input: {type(question)} - {question}")
                return {
                    "success": False,
                    "error": "Question must be a non-empty string",
                    "question": question
                }
            
            if len(question.strip()) == 0:
                logger.error("Question is empty or only whitespace")
                return {
                    "success": False,
                    "error": "Question cannot be empty or only whitespace",
                    "question": question
                }
            
            # Validate max_results
            if not isinstance(max_results, int) or max_results < 1 or max_results > 1000:
                logger.error(f"Invalid max_results: {max_results}")
                return {
                    "success": False,
                    "error": "max_results must be an integer between 1 and 1000",
                    "question": question
                }
            
            logger.info(f"🔍 VannaToolWrapper processing query: {question[:100]}...")
            logger.debug(f"Full question: {question}")
            logger.debug(f"Execute query: {execute_query}, Max results: {max_results}")
            
            # Check if vanna instance is available
            if not self.vanna:
                logger.error("VannaSnowflake instance is None!")
                return {
                    "success": False,
                    "error": "VannaSnowflake instance not available",
                    "question": question
                }
            
            if execute_query:
                # Use the full ask() method that generates SQL and executes it
                logger.info("🚀 Calling vanna.ask() method...")
                try:
                    result = self.vanna.ask(question)
                    logger.info(f"✅ vanna.ask() completed: {type(result)}")
                    logger.debug(f"vanna.ask() result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    if isinstance(result, dict):
                        if "error" in result:
                            logger.error(f"❌ vanna.ask() returned error: {result['error']}")
                            return {
                                "success": False,
                                "question": question,
                                "error": result["error"],
                                "execution_time_ms": int((time.time() - start_time) * 1000)
                            }
                        
                        # Log what we got back
                        sql = result.get("sql", "")
                        results = result.get("results", [])
                        logger.info(f"📊 Generated SQL length: {len(sql)} characters")
                        logger.info(f"📊 Results count: {len(results) if results else 0}")
                        logger.debug(f"Generated SQL: {sql[:500]}...")
                        
                        # Extract and format results
                        # Truncate results if needed
                        truncated_results = results[:max_results] if results else []
                        has_more_results = len(results) > max_results if results else False
                        
                        # Extract metadata
                        metadata = self._extract_query_metadata(sql)
                        
                        logger.info(f"✅ Query processing successful - returning {len(truncated_results)} rows")
                        return {
                            "success": True,
                            "question": question,
                            "sql": sql,
                            "results": truncated_results,
                            "row_count": len(truncated_results),
                            "execution_time_ms": int((time.time() - start_time) * 1000),
                            "metadata": {
                                **metadata,
                                "has_more_results": has_more_results,
                                "total_rows_available": len(results) if results else 0
                            }
                        }
                    else:
                        logger.error(f"❌ vanna.ask() returned unexpected type: {type(result)}")
                        return {
                            "success": False,
                            "question": question,
                            "error": f"Unexpected response type from vanna.ask(): {type(result)}",
                            "execution_time_ms": int((time.time() - start_time) * 1000)
                        }
                        
                except Exception as e:
                    logger.error(f"❌ Exception in vanna.ask(): {str(e)}")
                    logger.debug(f"vanna.ask() exception details:", exc_info=True)
                    return {
                        "success": False,
                        "question": question,
                        "error": f"Error in vanna.ask(): {str(e)}",
                        "execution_time_ms": int((time.time() - start_time) * 1000)
                    }
            else:
                # Only generate SQL without executing
                logger.info("🔧 Calling vanna.generate_sql() method...")
                try:
                    sql = self.vanna.generate_sql(question)
                    logger.info(f"✅ vanna.generate_sql() completed: {len(sql) if sql else 0} characters")
                    logger.debug(f"Generated SQL: {sql}")
                    
                    metadata = self._extract_query_metadata(sql)
                    
                    return {
                        "success": True,
                        "question": question,
                        "sql": sql,
                        "results": None,
                        "row_count": 0,
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "metadata": metadata
                    }
                except Exception as e:
                    logger.error(f"❌ Exception in vanna.generate_sql(): {str(e)}")
                    logger.debug(f"vanna.generate_sql() exception details:", exc_info=True)
                    return {
                        "success": False,
                        "question": question,
                        "error": f"Error in vanna.generate_sql(): {str(e)}",
                        "execution_time_ms": int((time.time() - start_time) * 1000)
                    }
                
        except Exception as e:
            logger.error(f"❌ Unexpected error in snowflake_query: {str(e)}")
            logger.debug(f"snowflake_query exception details:", exc_info=True)
            return {
                "success": False,
                "question": question,
                "error": f"Query processing failed: {str(e)}",
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
    
    def test_connection(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Secondary tool function for testing Snowflake connectivity.
        
        Args:
            detailed: Whether to return detailed connection information
            
        Returns:
            Connection status and optional detailed information
        """
        try:
            logger.info("Testing Snowflake connection...")
            result = self.vanna.test_connection(detailed=detailed)
            
            if detailed and isinstance(result, dict):
                return {
                    "success": result.get("success", False),
                    "connection_details": result
                }
            elif isinstance(result, bool):
                return {
                    "success": result,
                    "message": "Connection successful" if result else "Connection failed"
                }
            else:
                return {
                    "success": False,
                    "error": "Unexpected response from connection test"
                }
                
        except Exception as e:
            logger.error(f"Error in test_connection: {str(e)}")
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}"
            }
    
    def _extract_query_metadata(self, sql: str) -> Dict[str, Any]:
        """
        Extract metadata from SQL query for response formatting.
        
        Args:
            sql: The SQL query string
            
        Returns:
            Dictionary with query metadata
        """
        if not sql:
            return {"query_type": "unknown", "tables_used": []}
        
        sql_upper = sql.upper().strip()
        
        # Determine query type
        if sql_upper.startswith("SELECT"):
            query_type = "SELECT"
        elif sql_upper.startswith("INSERT"):
            query_type = "INSERT"
        elif sql_upper.startswith("UPDATE"):
            query_type = "UPDATE"
        elif sql_upper.startswith("DELETE"):
            query_type = "DELETE"
        elif sql_upper.startswith("CREATE"):
            query_type = "CREATE"
        elif sql_upper.startswith("ALTER"):
            query_type = "ALTER"
        elif sql_upper.startswith("DROP"):
            query_type = "DROP"
        else:
            query_type = "OTHER"
        
        # Extract table names (basic extraction - could be enhanced)
        tables_used = []
        try:
            # Simple pattern matching for table names after FROM and JOIN
            import re
            # Look for patterns like "FROM table_name" or "JOIN table_name"
            pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
            matches = re.findall(pattern, sql_upper)
            tables_used = list(set(matches))  # Remove duplicates
        except Exception:
            # If regex fails, continue with empty tables list
            pass
        
        return {
            "query_type": query_type,
            "tables_used": tables_used
        }
    
    @staticmethod
    def get_function_schemas() -> Dict[str, Dict[str, Any]]:
        """
        Return function calling schemas for different LLM platforms.
        
        Returns:
            Dictionary with schemas for different platforms (openai, anthropic, generic)
        """
        # Base schema for snowflake_query
        snowflake_query_schema = {
            "name": "snowflake_query",
            "description": "Ask questions about data in natural language and get SQL query results from Snowflake data warehouse. This tool can generate SQL from natural language and optionally execute it to return actual data results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the data (e.g., 'Show me sales by region for last quarter', 'What are the top 10 products by revenue?', 'How many customers do we have?')"
                    },
                    "execute_query": {
                        "type": "boolean",
                        "description": "Whether to execute the generated SQL and return actual results. Set to false if you only want to see the generated SQL without running it.",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of rows to return from the query results. Must be between 1 and 1000.",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["question"]
            }
        }
        
        # Base schema for test_connection
        test_connection_schema = {
            "name": "test_connection",
            "description": "Test connectivity to the Snowflake data warehouse and return connection status information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Whether to return detailed connection information including user, role, warehouse, database, and schema details.",
                        "default": False
                    }
                }
            }
        }
        
        return {
            "openai": [
                {
                    "type": "function",
                    "function": snowflake_query_schema
                },
                {
                    "type": "function", 
                    "function": test_connection_schema
                }
            ],
            "anthropic": [
                snowflake_query_schema,
                test_connection_schema
            ],
            "generic": [
                snowflake_query_schema,
                test_connection_schema
            ]
        }
    
    def close(self):
        """Close underlying VannaSnowflake connections."""
        if self.vanna:
            self.vanna.close()
            logger.info("VannaToolWrapper closed successfully")

# Convenience function for easy importing
def create_vanna_tools(openai_api_key: Optional[str] = None) -> VannaToolWrapper:
    """
    Convenience function to create a VannaToolWrapper instance.
    
    Args:
        openai_api_key: Optional OpenAI API key
        
    Returns:
        Configured VannaToolWrapper instance
    """
    return VannaToolWrapper(openai_api_key) 