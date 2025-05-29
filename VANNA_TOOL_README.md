# VannaToolWrapper: LLM-Callable Text-to-SQL Tool

The `VannaToolWrapper` transforms your existing VannaSnowflake text-to-SQL system into an LLM-callable tool through standardized function calling interfaces. This enables AI assistants to seamlessly query your Snowflake data warehouse using natural language.

## Features

- 🔧 **Simple Integration**: Lightweight wrapper around existing VannaSnowflake
- 🌐 **Multi-Platform Support**: Works with OpenAI, Anthropic, and other LLM platforms
- 🛡️ **Security**: Input validation and query safety controls
- ⚡ **Performance**: <100ms wrapper overhead, leverages existing optimizations
- 📊 **Comprehensive**: Full question → SQL → results workflow

## Quick Start

### Basic Usage

```python
from src.vanna_scripts import VannaToolWrapper

# Initialize the wrapper
wrapper = VannaToolWrapper()

# Test connection
connection_status = wrapper.test_connection()
print(f"Connection: {'✓' if connection_status['success'] else '❌'}")

# Ask a question
result = wrapper.snowflake_query(
    question="Show me the top 10 products by sales this quarter",
    execute_query=True,
    max_results=10
)

print(f"SQL: {result['sql']}")
print(f"Results: {result['results']}")

# Close connections
wrapper.close()
```

### Get Function Schemas

```python
# Get schemas for different platforms
schemas = VannaToolWrapper.get_function_schemas()

openai_tools = schemas["openai"]        # OpenAI Function Calling format
anthropic_tools = schemas["anthropic"]  # Anthropic Tool Use format
generic_tools = schemas["generic"]      # Generic format
```

## Integration with LLM Platforms

### OpenAI Function Calling

```python
import openai
from src.vanna_scripts import VannaToolWrapper

# Initialize
wrapper = VannaToolWrapper()
tools = VannaToolWrapper.get_function_schemas()["openai"]

# Create chat completion with tools
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What are our top selling products this quarter?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "snowflake_query":
            args = json.loads(tool_call.function.arguments)
            result = wrapper.snowflake_query(**args)
            
            # Send result back to conversation
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

wrapper.close()
```

### Anthropic Tool Use

```python
import anthropic
from src.vanna_scripts import VannaToolWrapper

# Initialize
wrapper = VannaToolWrapper()
tools = VannaToolWrapper.get_function_schemas()["anthropic"]

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    tools=tools,
    messages=[
        {"role": "user", "content": "Show me our revenue trends by month"}
    ]
)

# Handle tool use
if response.content[0].type == "tool_use":
    tool_use = response.content[0]
    if tool_use.name == "snowflake_query":
        result = wrapper.snowflake_query(**tool_use.input)
        
        # Continue conversation with result
        follow_up = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": "Show me our revenue trends by month"},
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": f"Tool result: {json.dumps(result)}"}
            ]
        )

wrapper.close()
```

## API Reference

### VannaToolWrapper Class

#### `__init__(openai_api_key: Optional[str] = None)`
Initialize the wrapper with optional OpenAI API key.

#### `snowflake_query(question: str, execute_query: bool = True, max_results: int = 100) -> Dict[str, Any]`
Primary tool function for natural language queries.

**Parameters:**
- `question` (str): Natural language question about the data
- `execute_query` (bool): Whether to execute the generated SQL and return results
- `max_results` (int): Maximum number of rows to return (1-1000)

**Returns:**
```python
{
    "success": bool,           # Whether operation succeeded
    "question": str,           # Original question
    "sql": str,               # Generated SQL query
    "results": list,          # Query results (if executed)
    "row_count": int,         # Number of rows returned
    "execution_time_ms": int, # Query execution time
    "error": str,             # Error message (if failed)
    "metadata": {
        "query_type": str,         # Type of SQL operation
        "tables_used": list,       # Tables referenced in query
        "has_more_results": bool,  # Whether results were truncated
        "total_rows_available": int
    }
}
```

#### `test_connection(detailed: bool = False) -> Dict[str, Any]`
Test Snowflake connectivity.

**Parameters:**
- `detailed` (bool): Return detailed connection information

**Returns:**
```python
{
    "success": bool,
    "message": str,              # Status message (if simple)
    "connection_details": dict   # Detailed info (if detailed=True)
}
```

#### `close()`
Close underlying VannaSnowflake connections.

### Static Methods

#### `get_function_schemas() -> Dict[str, List[Dict]]`
Returns function calling schemas for different platforms.

**Returns:**
- `openai`: OpenAI Function Calling format
- `anthropic`: Anthropic Tool Use format  
- `generic`: Generic format

### Convenience Functions

#### `create_vanna_tools(openai_api_key: Optional[str] = None) -> VannaToolWrapper`
Convenience function to create a VannaToolWrapper instance.

## Configuration

The wrapper uses the same configuration as your existing VannaSnowflake system:

```python
# Environment variables (same as VannaSnowflake)
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
OPENAI_API_KEY=your_openai_key

# Optional: Snowflake private key authentication
SNOWFLAKE_PRIVATE_KEY_BASE64=your_private_key
```

## Error Handling

The wrapper provides comprehensive error handling:

```python
result = wrapper.snowflake_query("invalid question format")

if not result["success"]:
    print(f"Error: {result['error']}")
    # Handle error appropriately
else:
    print(f"Success: {result['results']}")
```

Common error scenarios:
- **Invalid input**: Empty questions, invalid parameters
- **Connection issues**: Snowflake connectivity problems
- **SQL errors**: Invalid generated SQL or execution failures
- **Rate limiting**: Query timeout or resource limits

## Security Considerations

The wrapper implements several security measures:

1. **Input Validation**: All parameters are validated before processing
2. **Result Limiting**: Maximum 1000 rows per query to prevent data dumps
3. **Query Timeout**: Leverages existing VannaSnowflake timeout controls
4. **Snowflake Security**: Inherits existing role-based access controls
5. **Error Sanitization**: Sensitive information filtered from error messages

## Performance

- **Wrapper Overhead**: <100ms for function call processing
- **Total Response Time**: <5 seconds including Snowflake execution
- **Caching**: Leverages existing VannaSnowflake and ChromaDB caching
- **Connection Pooling**: Reuses existing connection management

## Testing

Run the test suite to validate the installation:

```bash
python test_vanna_tool.py
```

Run the demonstration script:

```bash
python demo_vanna_tool.py
```

## Troubleshooting

### Import Errors
```python
# Make sure you're importing from the correct path
from src.vanna_scripts import VannaToolWrapper
```

### Connection Issues
```python
# Test connection first
wrapper = VannaToolWrapper()
status = wrapper.test_connection(detailed=True)
print(status)
```

### Schema Issues
```python
# Verify function schemas are valid
schemas = VannaToolWrapper.get_function_schemas()
print(json.dumps(schemas["openai"], indent=2))
```

## Limitations

1. **Snowflake Only**: Currently supports Snowflake data warehouse only
2. **Read Operations**: Primarily designed for SELECT queries
3. **Result Size**: Limited to 1000 rows per query for performance
4. **Training Required**: Requires existing VannaSnowflake training data

## Migration from Direct VannaSnowflake Usage

**Before:**
```python
from src.vanna_scripts import VannaSnowflake

vanna = VannaSnowflake()
result = vanna.ask("Show me sales by region")
```

**After:**
```python
from src.vanna_scripts import VannaToolWrapper

wrapper = VannaToolWrapper()
result = wrapper.snowflake_query("Show me sales by region")
```

The response format is enhanced but backward compatible.

## Contributing

To extend the wrapper:

1. **Add new platforms**: Extend `get_function_schemas()` method
2. **Enhance validation**: Add validation logic in `snowflake_query()`
3. **Improve metadata**: Enhance `_extract_query_metadata()` method
4. **Add features**: Create new methods following the same pattern

## Support

For issues and questions:

1. Check the existing VannaSnowflake configuration
2. Run the test suite to validate setup
3. Review error messages in wrapper responses
4. Check Snowflake connectivity independently

The wrapper is designed to be a thin layer over your existing VannaSnowflake system, so most issues will be related to the underlying configuration. 