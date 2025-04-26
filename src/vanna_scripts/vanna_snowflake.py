import os
#import vanna
import chromadb
import logging
from typing import List, Dict, Any, Optional
from config import *
import json
from pathlib import Path
from src.vanna_scripts.snowflake_connection_manager import SnowflakeConnectionManager, auto_reconnect
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VannaSnowflake:
    """
    A class to integrate Vanna.AI with Snowflake and ChromaDB for text-to-SQL generation.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the VannaSnowflake class.
        
        Args:
            openai_api_key: The OpenAI API key to use. If None, it will be read from config.
        """
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
        self.snowflake_connection = None
        self.vanna_ai = None
        self.chroma_client = None
        self.chroma_collection = None
        
        # Initialize components
        self._init_snowflake()
        self._init_chromadb()
        self._init_vanna()
        
    def _init_snowflake(self):
        """Initialize the Snowflake connection."""
        try:
            # Log key environment variables (without sensitive values)
            logger.debug(f"Initializing Snowflake connection with: Account={SNOWFLAKE_ACCOUNT}, " +
                        f"User={SNOWFLAKE_USER}, Database={SNOWFLAKE_DATABASE}, Schema={SNOWFLAKE_SCHEMA}")
            
            # Use the Connection Manager instead of direct connection
            self.snowflake_connection = SnowflakeConnectionManager(
                snowflake_account=SNOWFLAKE_ACCOUNT,
                snowflake_user=SNOWFLAKE_USER,
                snowflake_org=SNOWFLAKE_ORG,
                snowflake_warehouse=SNOWFLAKE_WAREHOUSE,
                snowflake_role=SNOWFLAKE_ROLE,
                database=SNOWFLAKE_DATABASE,
                schema=SNOWFLAKE_SCHEMA,
                snowflake_private_key_path=SNOWFLAKE_PRIVATE_KEY_PATH,
                snowflake_private_key_base64=os.environ.get("SNOWFLAKE_PRIVATE_KEY_BASE64")
            )
            
            logger.info(f"Connected to Snowflake: {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}")
        except Exception as e:
            logger.error(f"Error connecting to Snowflake: {e}")
            logger.debug(f"Connection error details: {traceback.format_exc()}")
            raise
            
    def _init_chromadb(self):
        """Initialize ChromaDB for vector storage."""
        try:
            self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSISTENCE_DIRECTORY)
            
            # Create or get the collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME
            )
            
            logger.info(f"Initialized ChromaDB collection: {CHROMA_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
            
    def _init_vanna(self):
        """Initialize Vanna.AI with ChromaDB and OpenAI."""
        try:
            # Import the correct classes from vanna
            from vanna.openai.openai_chat import OpenAI_Chat
            from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
            
            # Create a custom Vanna class that combines ChromaDB and OpenAI
            class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    ChromaDB_VectorStore.__init__(self, config=config)
                    OpenAI_Chat.__init__(self, config=config)
            
            # Initialize Vanna with ChromaDB and OpenAI
            self.vanna_ai = MyVanna(config={
                'api_key': self.openai_api_key,
                'model': VANNA_MODEL_NAME,
                'collection_name': CHROMA_COLLECTION_NAME,
                'persist_directory': CHROMA_PERSISTENCE_DIRECTORY
            })
            
            logger.info(f"Initialized Vanna.AI with model: {VANNA_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Error initializing Vanna.AI: {e}")
            raise
    
    @auto_reconnect(max_retries=3)
    def get_ddl(self) -> List[str]:
        """
        Extract DDL statements from Snowflake for Vanna training.
        
        Returns:
            List of DDL statements
        """
        try:
            # Use the connection manager instead of direct cursor
            conn = self.snowflake_connection.get_connection()
            cursor = conn.cursor()
            
            # Get all tables in the current schema
            cursor.execute(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{SNOWFLAKE_SCHEMA}'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            ddl_statements = []
            
            for table in tables:
                # Get DDL for each table
                cursor.execute(f"SELECT GET_DDL('TABLE', '{SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}.{table}')")
                ddl = cursor.fetchone()[0]
                ddl_statements.append(ddl)
                
            cursor.close()
            return ddl_statements
        except Exception as e:
            logger.error(f"Error getting DDL from Snowflake: {e}")
            raise
    
    def train(self):
        """Train Vanna.AI on the Snowflake schema."""
        try:
            # Get DDL statements
            ddl_statements = self.get_ddl()
            
            # Train Vanna on the DDL
            for ddl in ddl_statements:
                self.vanna_ai.train(ddl=ddl)
                
            logger.info(f"Trained Vanna.AI on {len(ddl_statements)} DDL statements")
            
            # Training sources paths
            training_root = Path("data/training_sources")
            docs_path = training_root / "documentation"
            queries_path = training_root / "example_queries"
            qa_pairs_path = training_root / "qa_pairs"
            
            # Train documentation
            logger.info("Training documentation...")
            for doc_file in docs_path.glob("*.md"):
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            self.vanna_ai.train(documentation=content)
                            logger.info(f"Trained documentation from {doc_file.name}")
                        except Exception as e:
                            logger.error(f"Error training documentation from {doc_file.name}: {e}")
            
            # Train example queries
            logger.info("Training example queries...")
            for sql_file in queries_path.glob("*.sql"):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            self.vanna_ai.train(sql=content)
                            logger.info(f"Trained query from {sql_file.name}")
                        except Exception as e:
                            logger.error(f"Error training query from {sql_file.name}: {e}")
            
            # Train QA pairs
            logger.info("Training Q&A pairs...")
            for json_file in qa_pairs_path.glob("*.json"):
                with open(json_file, 'r', encoding='utf-8') as f:
                    qa_pairs = json.load(f)
                    for pair in qa_pairs:
                        try:
                            self.vanna_ai.train(
                                question=json.dumps(pair["question"]), 
                                sql=json.dumps(pair["sql"])
                            )
                            logger.info(f"Trained Q&A pair from {json_file.name}: {pair['question'][:50]}...")
                        except Exception as e:
                            logger.error(f"Error training Q&A pair from {json_file.name}: {e}")
            
            logger.info("Training process completed!")
            return True
        except Exception as e:
            logger.error(f"Error training Vanna.AI: {e}")
            raise
    
    def generate_sql(self, question: str) -> str:
        """
        Generate SQL from a natural language question.
        
        Args:
            question: The natural language question to convert to SQL
            
        Returns:
            Generated SQL query
        """
        try:
            sql = self.vanna_ai.generate_sql(question=question)
            return sql
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise
    
    @auto_reconnect(max_retries=3)
    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query on Snowflake and return results.
        
        Args:
            sql: The SQL query to execute
            
        Returns:
            Results as a list of dictionaries
        """
        try:
            # Use the execute_query method from our connection manager
            return self.snowflake_connection.execute_query(sql)
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            raise
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question in natural language and get the SQL and results.
        
        Args:
            question: The natural language question
            
        Returns:
            Dictionary with SQL query and results
        """
        try:
            # Generate SQL from question
            sql = self.generate_sql(question=question)
            
            # Execute the SQL
            results = self.execute_sql(sql)
            
            return {
                "question": question,
                "sql": sql,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                "question": question,
                "error": str(e)
            }
            
    def close(self):
        """Close all connections."""
        if self.snowflake_connection:
            self.snowflake_connection.close()

    def test_connection(self, detailed=False):
        """
        Test the Snowflake connection by running a simple query.
        
        Args:
            detailed: If True, return detailed connection information
            
        Returns:
            Boolean success status or dict with detailed information
        """
        try:
            if not self.snowflake_connection:
                logger.error("No Snowflake connection available to test")
                if detailed:
                    return {
                        "success": False,
                        "error": "No Snowflake connection available",
                        "connection_initialized": False
                    }
                return False
            
            # Get a connection
            conn = self.snowflake_connection.get_connection()
            
            # Run test query to get connection details
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CURRENT_USER() as user,
                    CURRENT_ROLE() as role,
                    CURRENT_WAREHOUSE() as warehouse,
                    CURRENT_DATABASE() as database,
                    CURRENT_SCHEMA() as schema,
                    CURRENT_ACCOUNT() as account,
                    CURRENT_REGION() as region,
                    CURRENT_VERSION() as version
            """)
            
            result = cursor.fetchone()
            cursor.close()
            
            # Verify if we have valid data
            if not result:
                logger.error("Connection test query returned no results")
                if detailed:
                    return {
                        "success": False,
                        "error": "Test query returned no results",
                        "connection_initialized": True,
                        "connection_active": True
                    }
                return False
            
            # Check if we can access the schema
            try:
                cursor = conn.cursor()
                cursor.execute(f"SHOW TABLES IN {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}")
                tables = cursor.fetchall()
                table_count = len(tables)
                cursor.close()
                schema_accessible = True
                logger.info(f"Found {table_count} tables in {SNOWFLAKE_DATABASE}.{SNOWFLAKE_SCHEMA}")
            except Exception as e:
                schema_accessible = False
                table_count = 0
                schema_error = str(e)
                logger.error(f"Error accessing schema: {schema_error}")
            
            # Build response
            if detailed:
                connection_details = {
                    "success": True,
                    "connection_initialized": True,
                    "connection_active": True,
                    "user": result[0],
                    "role": result[1],
                    "warehouse": result[2],
                    "database": result[3],
                    "schema": result[4],
                    "account": result[5],
                    "region": result[6],
                    "version": result[7],
                    "schema_accessible": schema_accessible,
                    "table_count": table_count
                }
                
                if not schema_accessible:
                    connection_details["schema_error"] = schema_error
                
                return connection_details
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")
            logger.debug(f"Connection test error details: {traceback.format_exc()}")
            
            if detailed:
                return {
                    "success": False,
                    "error": error_msg,
                    "details": traceback.format_exc(),
                    "connection_initialized": self.snowflake_connection is not None
                }
            
            return False 