import os
import time
import logging
import functools
import base64
import traceback
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Configure logging with more detail
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SnowflakeConnectionManager:
    """
    A connection manager for Snowflake that handles token expiration and reconnection.
    """
    
    # Error code for authentication token expiration
    TOKEN_EXPIRED_ERROR_CODE = "390114"
    
    def __init__(
        self,
        snowflake_account: str = None,
        snowflake_user: str = None,
        snowflake_warehouse: str = None,
        snowflake_role: str = None,
        snowflake_org: str = None,
        snowflake_private_key_path: str = None,
        snowflake_private_key_base64: str = None,
        database: str = None,
        schema: str = None,
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        """
        Initialize the Snowflake Connection Manager.
        
        Args:
            snowflake_account: Snowflake account identifier
            snowflake_user: Snowflake username
            snowflake_warehouse: Snowflake warehouse
            snowflake_role: Snowflake role
            snowflake_org: Snowflake organization (optional)
            snowflake_private_key_path: Path to private key file
            snowflake_private_key_base64: Base64-encoded private key string
            database: Default database to use
            schema: Default schema to use
            max_retries: Maximum number of retry attempts for reconnection
            retry_delay: Base delay between retries in seconds
        """
        self.snowflake_account = snowflake_account or os.environ.get("SNOWFLAKE_ACCOUNT")
        self.snowflake_user = snowflake_user or os.environ.get("SNOWFLAKE_USER")
        self.snowflake_warehouse = snowflake_warehouse or os.environ.get("SNOWFLAKE_WAREHOUSE")
        self.snowflake_role = snowflake_role or os.environ.get("SNOWFLAKE_ROLE")
        self.snowflake_org = snowflake_org or os.environ.get("SNOWFLAKE_ORG")
        
        # Log connection parameters (except sensitive data)
        logger.debug(f"Connection parameters: Account={self.snowflake_account}, User={self.snowflake_user}, " +
                    f"Warehouse={self.snowflake_warehouse}, Role={self.snowflake_role}, Org={self.snowflake_org}")
        
        # Get base64-encoded private key or fallback to file path
        self.snowflake_private_key_base64 = snowflake_private_key_base64 or os.environ.get("SNOWFLAKE_PRIVATE_KEY_BASE64")
        
        # Default private key path if not provided and base64 key not available
        if not self.snowflake_private_key_base64:
            if not snowflake_private_key_path:
                snowflake_private_key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
                if not snowflake_private_key_path:
                    snowflake_private_key_path = os.path.join("snowflake_keys", "rsa_key.p8")
            self.snowflake_private_key_path = snowflake_private_key_path
            logger.debug(f"Using private key file from: {self.snowflake_private_key_path}")
        else:
            self.snowflake_private_key_path = None
            logger.debug("Using base64-encoded private key from environment variable")
        
        self.database = database or os.environ.get("SNOWFLAKE_DATABASE")
        self.schema = schema or os.environ.get("SNOWFLAKE_SCHEMA")
        logger.debug(f"Database target: {self.database}.{self.schema}")
        
        # Retry configuration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Connection state
        self.conn = None
        self.p_key = None
        self.last_connection_time = None
        
        # Check if environment variables are properly set
        self._validate_config()
        
        # Establish initial connection
        self.connect()
    
    def _validate_config(self):
        """Validate that necessary configuration values are available"""
        missing = []
        if not self.snowflake_account:
            missing.append("SNOWFLAKE_ACCOUNT")
        if not self.snowflake_user:
            missing.append("SNOWFLAKE_USER")
        if not self.snowflake_warehouse:
            missing.append("SNOWFLAKE_WAREHOUSE")
        if not self.database:
            missing.append("SNOWFLAKE_DATABASE")
        if not self.schema:
            missing.append("SNOWFLAKE_SCHEMA")
        
        # Check authentication methods
        has_auth = False
        auth_methods = []
        if self.snowflake_private_key_base64:
            has_auth = True
            auth_methods.append("SNOWFLAKE_PRIVATE_KEY_BASE64")
        elif self.snowflake_private_key_path and os.path.exists(self.snowflake_private_key_path):
            has_auth = True
            auth_methods.append("SNOWFLAKE_PRIVATE_KEY_PATH")
        elif os.environ.get("SNOWFLAKE_PASSWORD"):
            has_auth = True
            auth_methods.append("SNOWFLAKE_PASSWORD")
        
        if not has_auth:
            missing.append("Authentication method (Private key or password)")
        
        if missing:
            logger.error(f"Missing required Snowflake configuration: {', '.join(missing)}")
        else:
            logger.debug(f"Config validation passed. Authentication methods available: {', '.join(auth_methods)}")
    
    def connect(self):
        """
        Establish a new connection to Snowflake.
        """
        try:
            # Load the private key
            self._load_private_key()
            
            if self.p_key:
                # Format account name as orgname-accountname if org is provided
                account = f"{self.snowflake_org}-{self.snowflake_account}" if self.snowflake_org else self.snowflake_account
                logger.info(f"Connecting to Snowflake account: {account}")
                
                # Connect to Snowflake using private key
                connect_params = {
                    "user": self.snowflake_user,
                    "private_key": self.p_key,
                    "account": account,
                    "warehouse": self.snowflake_warehouse,
                    "database": self.database,
                    "schema": self.schema
                }
                
                if self.snowflake_role:
                    connect_params["role"] = self.snowflake_role
                
                logger.debug(f"Connection parameters: {', '.join(k + '=' + (v if k != 'private_key' else '[REDACTED]') for k, v in connect_params.items())}")
                
                self.conn = snowflake.connector.connect(**connect_params)
                
                self.last_connection_time = time.time()
                logger.info(f"Connected to Snowflake: {self.database}.{self.schema}")
                
                # Verify connection with test query
                self._test_connection()
                
                return self.conn
            else:
                # Fallback to password authentication
                password = os.environ.get("SNOWFLAKE_PASSWORD")
                if not password:
                    logger.error("No authentication method available. Private key could not be loaded and SNOWFLAKE_PASSWORD environment variable is not set.")
                    raise ValueError("No authentication method available. Private key could not be loaded and SNOWFLAKE_PASSWORD environment variable is not set.")
                
                logger.debug("Using password authentication as fallback")
                account = f"{self.snowflake_org}-{self.snowflake_account}" if self.snowflake_org else self.snowflake_account
                
                connect_params = {
                    "user": self.snowflake_user,
                    "password": "[REDACTED]",  # For logging only
                    "account": account,
                    "warehouse": self.snowflake_warehouse,
                    "database": self.database,
                    "schema": self.schema
                }
                
                if self.snowflake_role:
                    connect_params["role"] = self.snowflake_role
                
                logger.debug(f"Connection parameters: {', '.join(k + '=' + v for k, v in connect_params.items())}")
                
                # Replace redacted password with actual password for connection
                connect_params["password"] = password
                
                self.conn = snowflake.connector.connect(**connect_params)
                
                self.last_connection_time = time.time()
                logger.info(f"Connected to Snowflake using password: {self.database}.{self.schema}")
                
                # Verify connection with test query
                self._test_connection()
                
                return self.conn
        except Exception as e:
            logger.error(f"Error connecting to Snowflake: {str(e)}")
            logger.debug(f"Connection error details: {traceback.format_exc()}")
            raise
    
    def _test_connection(self):
        """Run a simple query to verify the connection works"""
        try:
            cursor = self.conn.cursor()
            
            # Set database and schema context to ensure they're available for queries
            if self.database:
                cursor.execute(f"USE DATABASE {self.database}")
                logger.debug(f"Set database context to: {self.database}")
            
            if self.schema:
                cursor.execute(f"USE SCHEMA {self.schema}")
                logger.debug(f"Set schema context to: {self.schema}")
            
            cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
            result = cursor.fetchone()
            cursor.close()
            logger.debug(f"Connection test succeeded - User: {result[0]}, Role: {result[1]}, Warehouse: {result[2]}, DB: {result[3]}, Schema: {result[4]}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def reconnect(self):
        """
        Close the existing connection and establish a new one.
        """
        logger.info("Reconnecting to Snowflake...")
        
        # Close existing connection if present
        if self.conn:
            try:
                self.conn.close()
            except Exception as e:
                logger.warning(f"Error closing existing connection: {e}")
        
        # Establish a new connection
        return self.connect()
    
    def _load_private_key(self):
        """
        Load private key from base64 string or file.
        """
        try:
            # First try to load from base64 string in environment variable
            if self.snowflake_private_key_base64:
                logger.info("Loading private key from base64 string")
                try:
                    # Check if the base64 string has a reasonable length
                    if len(self.snowflake_private_key_base64) < 100:
                        logger.warning("Base64 private key string appears too short - may be invalid")
                    
                    # Decode the base64 string to bytes
                    try:
                        key_bytes = base64.b64decode(self.snowflake_private_key_base64)
                        logger.debug(f"Successfully decoded base64 key, length: {len(key_bytes)} bytes")
                    except Exception as e:
                        logger.error(f"Failed to decode base64 string: {str(e)}")
                        raise
                    
                    # Load the key
                    try:
                        p_key = serialization.load_pem_private_key(
                            key_bytes,
                            password=None,
                            backend=default_backend()
                        )
                        logger.debug("Successfully parsed PEM key")
                    except Exception as e:
                        logger.error(f"Failed to parse private key from decoded base64: {str(e)}")
                        raise
                    
                    # Get key in correct format for Snowflake
                    self.p_key = p_key.private_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    logger.info("Successfully loaded private key from base64 string")
                    return self.p_key
                except Exception as e:
                    logger.error(f"Error loading private key from base64 string: {e}")
                    logger.debug(f"Base64 key processing error details: {traceback.format_exc()}")
                    # Continue to try loading from file if base64 loading fails
            
            # Fall back to loading from file if base64 string not available or loading failed
            if self.snowflake_private_key_path and os.path.exists(self.snowflake_private_key_path):
                logger.info(f"Loading private key from file: {self.snowflake_private_key_path}")
                try:
                    with open(self.snowflake_private_key_path, "rb") as key_file:
                        file_contents = key_file.read()
                        logger.debug(f"Read {len(file_contents)} bytes from key file")
                        p_key = serialization.load_pem_private_key(
                            file_contents,
                            password=None,
                            backend=default_backend()
                        )
                    
                    # Get key in correct format for Snowflake
                    self.p_key = p_key.private_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    logger.info("Successfully loaded private key from file")
                    return self.p_key
                except Exception as e:
                    logger.error(f"Error loading private key from file: {str(e)}")
                    logger.debug(f"File key processing error details: {traceback.format_exc()}")
            else:
                if not self.snowflake_private_key_base64:
                    logger.error(f"Private key file not found at: {self.snowflake_private_key_path}")
                self.p_key = None
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            logger.debug(f"Key loading error details: {traceback.format_exc()}")
            self.p_key = None
        
        return None
    
    def is_connection_active(self):
        """
        Check if the current connection is active.
        """
        if not self.conn:
            logger.debug("Connection check failed: No connection object exists")
            return False
        
        try:
            # Simple query to test connection
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            logger.debug("Connection check passed")
            return True
        except Exception as e:
            logger.debug(f"Connection check failed: {str(e)}")
            return False
    
    def execute_query(self, sql, params=None, retry_count=0):
        """
        Execute a SQL query with automatic reconnection if token expires.
        
        Args:
            sql: SQL query to execute
            params: Query parameters
            retry_count: Current retry attempt (used internally)
            
        Returns:
            Query results
        """
        if retry_count > self.max_retries:
            logger.error(f"Maximum retry attempts ({self.max_retries}) exceeded")
            raise Exception(f"Failed to execute query after {self.max_retries} attempts")
        
        # Log query for debugging (truncate if too long)
        log_sql = sql if len(sql) < 500 else sql[:500] + "..."
        logger.debug(f"Executing SQL (retry {retry_count}/{self.max_retries}): {log_sql}")
        
        try:
            # Ensure connection is active
            if not self.is_connection_active():
                logger.info("Connection is not active, reconnecting...")
                self.reconnect()
            
            # Execute the query
            cursor = self.conn.cursor()
            start_time = time.time()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            execution_time = time.time() - start_time
            logger.debug(f"SQL execution time: {execution_time:.2f} seconds")
            
            # Get column names
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                logger.debug(f"Query result columns: {', '.join(columns)}")
                
                # Fetch results
                results = []
                row_count = 0
                for row in cursor:
                    results.append(dict(zip(columns, row)))
                    row_count += 1
                
                logger.debug(f"Query returned {row_count} rows")
                cursor.close()
                return results
            else:
                # For non-result queries (like INSERT, UPDATE, etc.)
                affected = cursor.rowcount if hasattr(cursor, 'rowcount') else 'unknown'
                logger.debug(f"Non-query SQL affected {affected} rows")
                cursor.close()
                return []
                
        except snowflake.connector.errors.ProgrammingError as e:
            error_message = str(e)
            
            # Check if token expired error
            if self.TOKEN_EXPIRED_ERROR_CODE in error_message and "Authentication token has expired" in error_message:
                logger.warning("Authentication token has expired, reconnecting...")
                
                # Exponential backoff
                if retry_count > 0:
                    backoff_time = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retry attempt {retry_count+1}, waiting for {backoff_time} seconds...")
                    time.sleep(backoff_time)
                
                # Reconnect and retry
                self.reconnect()
                return self.execute_query(sql, params, retry_count + 1)
            else:
                # Propagate other errors
                logger.error(f"SQL error: {e}")
                logger.debug(f"SQL error details: {traceback.format_exc()}")
                raise
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.debug(f"Query execution error details: {traceback.format_exc()}")
            raise
    
    def get_connection(self):
        """
        Get the current Snowflake connection, reconnecting if necessary.
        
        Returns:
            Active Snowflake connection
        """
        if not self.is_connection_active():
            logger.info("Connection not active in get_connection(), reconnecting...")
            self.reconnect()
        
        # Ensure database and schema context are set
        try:
            cursor = self.conn.cursor()
            if self.database:
                cursor.execute(f"USE DATABASE {self.database}")
                logger.debug(f"Ensured database context: {self.database}")
            
            if self.schema:
                cursor.execute(f"USE SCHEMA {self.schema}")
                logger.debug(f"Ensured schema context: {self.schema}")
            
            cursor.close()
        except Exception as e:
            logger.warning(f"Could not set database/schema context: {e}")
        
        return self.conn
    
    def close(self):
        """
        Close the Snowflake connection.
        """
        if self.conn:
            try:
                self.conn.close()
                logger.info("Snowflake connection closed")
            except Exception as e:
                logger.error(f"Error closing Snowflake connection: {e}")
            finally:
                self.conn = None

# Decorator for auto-reconnect functionality
def auto_reconnect(max_retries=3):
    """
    Decorator to automatically reconnect to Snowflake when token expires.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(self, *args, **kwargs)
                except snowflake.connector.errors.ProgrammingError as e:
                    error_message = str(e)
                    
                    # Check if token expired error
                    if "390114" in error_message and "Authentication token has expired" in error_message:
                        logger.warning("Authentication token has expired, reconnecting...")
                        
                        # Exponential backoff
                        if retries > 0:
                            backoff_time = 1 * (2 ** (retries - 1))
                            logger.info(f"Retry attempt {retries+1}, waiting for {backoff_time} seconds...")
                            time.sleep(backoff_time)
                        
                        # Reconnect
                        if hasattr(self, 'reconnect'):
                            self.reconnect()
                        
                        retries += 1
                    else:
                        # Propagate other errors
                        raise
                except Exception:
                    # Propagate non-Snowflake errors
                    raise
            
            # Max retries exceeded
            raise Exception(f"Failed after {max_retries} reconnection attempts")
        
        return wrapper
    
    return decorator 