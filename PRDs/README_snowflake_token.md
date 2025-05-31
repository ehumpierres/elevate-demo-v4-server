# Snowflake Token Management System

This system provides automatic handling of Snowflake authentication token expiration, which is particularly useful when deploying to services like Render where applications may run for extended periods.

## Overview

The token management system includes:

1. **SnowflakeConnectionManager**: A robust wrapper around Snowflake connections that handles token expiration and automatic reconnection.
2. **Auto-reconnect Decorator**: A decorator (`@auto_reconnect`) that can be applied to functions that interact with Snowflake.
3. **TTL-based Caching**: Streamlit caching with time-to-live parameters to ensure periodic reconnection.
4. **Manual Reconnection**: A UI button to manually reconnect if needed.

## Key Features

- **Automatic Token Renewal**: Detects "Authentication token has expired" errors and automatically reconnects.
- **Connection Health Checking**: Validates connections before executing queries.
- **Exponential Backoff**: Implements increasing delays between retry attempts.
- **Graceful Error Handling**: Provides clear error messages and logging.
- **Resource Cleanup**: Ensures proper connection cleanup to prevent resource leaks.
- **Flexible Key Management**: Supports both file-based and base64-encoded private keys.

## Usage

### In Code

To use the connection manager in your code:

```python
from src.vanna_scripts.snowflake_connection_manager import SnowflakeConnectionManager, auto_reconnect

# Create a connection manager
conn_manager = SnowflakeConnectionManager(
    snowflake_account="your_account",
    snowflake_user="your_user",
    # Other parameters...
)

# Execute a query with automatic reconnection
results = conn_manager.execute_query("SELECT * FROM your_table")

# Or use the decorator on functions that interact with Snowflake
@auto_reconnect(max_retries=3)
def your_snowflake_function():
    # Function that interacts with Snowflake
    pass
```

### Environment Variables

The following environment variables should be set in your deployment environment (e.g., Render):

- `SNOWFLAKE_ACCOUNT`: Your Snowflake account identifier
- `SNOWFLAKE_USER`: Your Snowflake username
- `SNOWFLAKE_ORG`: (Optional) Your Snowflake organization
- `SNOWFLAKE_WAREHOUSE`: The warehouse to use
- `SNOWFLAKE_ROLE`: The role to use
- `SNOWFLAKE_DATABASE`: The default database
- `SNOWFLAKE_SCHEMA`: The default schema

Plus one of the following for authentication:

- `SNOWFLAKE_PRIVATE_KEY_BASE64`: Base64-encoded private key (preferred for cloud deployments)
- `SNOWFLAKE_PRIVATE_KEY_PATH`: Path to your private key file (alternative)
- `SNOWFLAKE_PASSWORD`: Password authentication (fallback, not recommended for production)

### Using Base64-encoded Private Key

For cloud deployments like Render, storing the private key as a base64-encoded environment variable is recommended over file-based storage:

1. Convert your private key to base64:
   ```bash
   cat your_private_key.p8 | base64
   ```

2. Add the output to your environment variables in Render as `SNOWFLAKE_PRIVATE_KEY_BASE64`

3. The connection manager will automatically detect and use this key

### Manual Reconnection

If you encounter consistent token expiration issues, you can use the "Reconnect to Snowflake" button in the sidebar to force a reconnection.

## Troubleshooting

If you encounter issues with Snowflake connections:

1. Check the logs for specific error messages
2. Ensure your private key (file or base64) is valid
3. Verify that your Snowflake account settings are correct
4. Try the manual reconnection button
5. Restart the application if necessary

## Implementation Details

- `snowflake_connection_manager.py`: Contains the main connection manager class and decorator
- `vanna_calls.py`: Implements TTL-based caching and connection cleanup
- `vanna_snowflake.py`: Uses the connection manager for Snowflake interactions
- `holistic_ui.py`: Provides the UI for manual reconnection 