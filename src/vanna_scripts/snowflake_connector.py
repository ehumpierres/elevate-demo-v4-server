import os
import base64
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_USER,
    SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_ROLE,
    SNOWFLAKE_ORG,
    SNOWFLAKE_PRIVATE_KEY_PATH,
    SNOWFLAKE_PRIVATE_KEY_BASE64,
    SNOWFLAKE_MEMORY_DATABASE,
    SNOWFLAKE_MEMORY_SCHEMA
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SnowflakeConnector:
    """Handles connections to Snowflake database."""
    
    def __init__(
        self,
        snowflake_account: str = None,
        snowflake_user: str = None,
        snowflake_warehouse: str = None,
        snowflake_role: str = None,
        snowflake_org: str = None,
        snowflake_private_key_path: str = None,
        snowflake_private_key_base64: str = None,
        memory_database: str = None,
        memory_schema: str = None
    ):
        self.snowflake_account = snowflake_account or SNOWFLAKE_ACCOUNT
        self.snowflake_user = snowflake_user or SNOWFLAKE_USER
        self.snowflake_warehouse = snowflake_warehouse or SNOWFLAKE_WAREHOUSE
        self.snowflake_role = snowflake_role or SNOWFLAKE_ROLE
        self.snowflake_org = snowflake_org or SNOWFLAKE_ORG
        self.snowflake_private_key_path = snowflake_private_key_path or SNOWFLAKE_PRIVATE_KEY_PATH
        self.snowflake_private_key_base64 = snowflake_private_key_base64 or SNOWFLAKE_PRIVATE_KEY_BASE64
        self.memory_database = memory_database or SNOWFLAKE_MEMORY_DATABASE
        self.memory_schema = memory_schema or SNOWFLAKE_MEMORY_SCHEMA
        self.conn = None
        self.p_key = None  # Will hold the loaded private key
        
    def connect(self):
        """Establishes connection to Snowflake."""
        try:
            # Load the private key first
            self._load_private_key()
            
            if self.p_key:
                # Format account name as orgname-accountname if org is provided
                account = f"{self.snowflake_org}-{self.snowflake_account}" if self.snowflake_org else self.snowflake_account
                logger.info(f"Using Snowflake account identifier: {account}")
                
                # Connect to Snowflake using private key
                self.conn = snowflake.connector.connect(
                    user=self.snowflake_user,
                    private_key=self.p_key,
                    account=account,
                    warehouse=self.snowflake_warehouse,
                    role=self.snowflake_role,
                    database=self.memory_database,
                    schema=self.memory_schema
                )
                
                logger.info(f"Connected to Snowflake: {self.memory_database}.{self.memory_schema}")
                return self.conn
            else:
                # Using password authentication as fallback (not recommended for production)
                password = os.environ.get("SNOWFLAKE_PASSWORD")
                if not password:
                    raise ValueError("No authentication method available. Private key could not be loaded and SNOWFLAKE_PASSWORD environment variable is not set.")
                
                # Format account name as orgname-accountname if org is provided
                account = f"{self.snowflake_org}-{self.snowflake_account}" if self.snowflake_org else self.snowflake_account
                
                self.conn = snowflake.connector.connect(
                    user=self.snowflake_user,
                    password=password,
                    account=account,
                    warehouse=self.snowflake_warehouse,
                    role=self.snowflake_role,
                    database=self.memory_database,
                    schema=self.memory_schema
                )
                
                logger.info(f"Connected to Snowflake using password: {self.memory_database}.{self.memory_schema}")
                return self.conn
        except Exception as e:
            logger.error(f"Error connecting to Snowflake: {e}")
            raise
    
    def _load_private_key(self):
        """Load private key from file or base64 string."""
        try:
            # First try to load from base64 string
            if self.snowflake_private_key_base64:
                logger.info("Loading private key from base64 string")
                try:
                    private_key_data = base64.b64decode(self.snowflake_private_key_base64)
                    self.p_key = serialization.load_pem_private_key(
                        private_key_data,
                        password=None,
                        backend=default_backend()
                    )
                    
                    # Get key in correct format for Snowflake
                    self.p_key = self.p_key.private_bytes(
                        encoding=serialization.Encoding.DER,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
                    
                    logger.info("Successfully loaded private key from base64")
                    return self.p_key
                except Exception as e:
                    logger.error(f"Error loading private key from base64: {e}")
            
            # Fall back to loading from file if base64 failed
            if self.snowflake_private_key_path and os.path.exists(self.snowflake_private_key_path):
                logger.info(f"Loading private key from file: {self.snowflake_private_key_path}")
                with open(self.snowflake_private_key_path, "rb") as key_file:
                    self.p_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                
                # Get key in correct format for Snowflake
                self.p_key = self.p_key.private_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                logger.info("Successfully loaded private key from file")
                return self.p_key
            else:
                logger.warning("No valid private key source found")
                self.p_key = None
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            self.p_key = None
        
        return None