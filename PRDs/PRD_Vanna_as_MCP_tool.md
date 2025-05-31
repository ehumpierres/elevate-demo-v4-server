# Product Requirements Document: VannaSnowflake LLM Tool Integration

## Executive Summary

Create a simple wrapper around our existing VannaSnowflake text-to-SQL system to make it LLM-callable through standardized function calling interfaces. This lightweight integration will expose our proven Vanna.AI + Snowflake + ChromaDB solution as callable functions that AI assistants can invoke to answer natural language database questions.

## Product Overview

### Current State
We have a fully functional text-to-SQL system (`VannaSnowflake`) that:
- Uses Vanna.AI for natural language to SQL conversion
- Connects to Snowflake data warehouse
- Leverages ChromaDB for vector storage and semantic search
- Includes training capabilities with DDL, documentation, and example queries
- Provides end-to-end question → SQL → results workflow

### Problem Statement
Our powerful text-to-SQL system is only accessible through direct Python integration. AI assistants and LLMs cannot easily invoke our existing capabilities through standardized function calling interfaces.

### Solution
Create a lightweight tool wrapper class around our existing `VannaSnowflake` that formats its functionality for LLM function calling. This wrapper will provide standardized function schemas and response formats without requiring a separate server or complex infrastructure.

### Success Metrics
- Tool integration accuracy >95% (leveraging existing Vanna accuracy)
- Response time <5 seconds (including Snowflake query execution)
- Zero security vulnerabilities in tool wrapper
- Successful integration with 3+ AI assistant platforms

## Requirements

### Functional Requirements

#### Tool Wrapper Development
**REQ-001: Function Schema Definition**
- Create standardized function calling schemas for our existing methods
- Support primary workflow: `ask()` method (question → SQL → results)
- Include secondary functions: `generate_sql()`, `test_connection()`
- Handle complex return types (query results, metadata, errors)

**REQ-002: Input Validation and Sanitization**
- Validate natural language inputs for safety
- Prevent prompt injection attacks
- Limit query complexity and execution time
- Implement parameter validation

**REQ-003: Response Formatting**
- Structure responses for AI assistant consumption
- Include SQL query, results, and explanatory metadata
- Handle large result sets with pagination
- Provide error messages in user-friendly format

#### Platform Integration
**REQ-004: Multi-Platform Function Calling Support**
- Support OpenAI Function Calling format
- Support Anthropic Tool Use format
- Support other major AI platforms (Claude, GPT, etc.)
- Provide standardized JSON schemas for each platform

**REQ-005: Direct Integration Capability**
- Allow direct import and usage in Python applications
- No server dependency - runs in-process
- Simple instantiation and method calling
- Compatible with existing VannaSnowflake configuration

#### Safety and Security
**REQ-006: Query Safety Controls**
- Leverage existing Snowflake security model
- Implement query result size limits
- Add query timeout controls
- Sanitize returned data for sensitive information

**REQ-007: Connection Security**
- Secure Snowflake credential management
- Connection pooling and lifecycle management
- Audit logging for all tool invocations
- Parameter validation and sanitization

### Non-Functional Requirements

#### Performance
**REQ-008: Response Time**
- Tool wrapper overhead: <100ms
- Total response time: <5 seconds (including Snowflake execution)
- Leverage existing VannaSnowflake caching where available

#### Reliability
**REQ-009: Error Handling**
- Graceful handling of Snowflake connection issues
- Fallback behaviors for Vanna.AI timeouts
- Comprehensive error logging and recovery
- Consistent error response format

#### Simplicity
**REQ-010: Ease of Integration**
- Single Python class for all tool functionality
- Minimal dependencies beyond existing VannaSnowflake
- Clear documentation and examples
- Plug-and-play integration

## Technical Specifications

### System Architecture

#### Simple Wrapper Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Assistant  │────│ VannaToolWrapper │────│ VannaSnowflake  │
│ (with function  │    │   (New - Simple) │    │ (Existing)      │
│    calling)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        │
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Function Schema │    │ Vanna.AI +      │
                       │  Definitions     │    │ ChromaDB +      │
                       └──────────────────┘    │ Snowflake       │
                                              └─────────────────┘
```

#### Core Wrapper Class
```python
class VannaToolWrapper:
    """Simple wrapper to make VannaSnowflake LLM-callable"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.vanna = VannaSnowflake(openai_api_key)
    
    def snowflake_query(self, question: str, execute_query: bool = True, max_results: int = 100):
        """Primary tool function for natural language queries"""
        
    def test_connection(self, detailed: bool = False):
        """Secondary tool function for connection testing"""
        
    @staticmethod
    def get_function_schemas():
        """Return function calling schemas for different platforms"""
```

#### Tool Function Specifications

**Primary Tool: `snowflake_query`**
```json
{
  "name": "snowflake_query",
  "description": "Ask questions about data in natural language and get SQL query results from Snowflake",
  "parameters": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "Natural language question about the data (e.g., 'Show me sales by region for last quarter')"
      },
      "execute_query": {
        "type": "boolean",
        "description": "Whether to execute the generated SQL and return results",
        "default": true
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of rows to return",
        "default": 100,
        "maximum": 1000
      }
    },
    "required": ["question"]
  }
}
```

**Response Schema:**
```json
{
  "success": "boolean - Whether operation succeeded",
  "question": "string - Original natural language question",
  "sql": "string - Generated SQL query",
  "results": "array - Query results (if executed)",
  "row_count": "number - Number of rows returned",
  "execution_time_ms": "number - Query execution time",
  "error": "string - Error message if failed",
  "metadata": {
    "tables_used": "array - Tables referenced in query",
    "query_type": "string - Type of SQL operation",
    "has_more_results": "boolean - Whether results were truncated"
  }
}
```

**Secondary Tool: `test_connection`**
```json
{
  "name": "test_connection",
  "description": "Test connectivity to Snowflake and return connection status",
  "parameters": {
    "type": "object",
    "properties": {
      "detailed": {
        "type": "boolean",
        "description": "Return detailed connection information",
        "default": false
      }
    }
  }
}
```

### Technology Stack

#### Existing Components (No Changes Required)
- **Core Engine:** VannaSnowflake class
- **AI/ML:** Vanna.AI with OpenAI integration
- **Vector Store:** ChromaDB with persistent storage
- **Database:** Snowflake data warehouse
- **Connection Management:** SnowflakeConnectionManager

#### New Components (Minimal)
- **Tool Wrapper:** Single Python class `VannaToolWrapper`
- **Function Schemas:** JSON schema definitions for each platform
- **Input Validation:** Parameter validation using existing Python patterns

### Integration Examples

#### Direct Usage
```python
# Initialize the wrapper
tool_wrapper = VannaToolWrapper()

# Use as regular Python class
result = tool_wrapper.snowflake_query("Show me total sales by region")

# Get function schemas for LLM integration
schemas = VannaToolWrapper.get_function_schemas()
```

#### LLM Function Calling Integration
```python
# OpenAI Function Calling
tools = [tool_wrapper.get_function_schemas()['openai']]
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What are our top selling products?"}],
    tools=tools
)

# Anthropic Tool Use
tools = [tool_wrapper.get_function_schemas()['anthropic']]
# Similar pattern for other platforms
```

## Implementation Plan

### Phase 1: Core Wrapper (1 week)
**Days 1-3: Basic Implementation**
- Create `VannaToolWrapper` class
- Implement `snowflake_query()` method wrapping existing `ask()`
- Add input validation and error handling
- Create response formatting

**Days 4-5: Function Schemas**
- Define JSON schemas for OpenAI, Anthropic, and generic formats
- Add `get_function_schemas()` static method
- Create integration examples and documentation

### Phase 2: Testing and Refinement (1 week)
**Days 6-8: Testing**
- Unit tests for wrapper functionality
- Integration tests with actual LLM platforms
- Error handling and edge case testing
- Performance validation

**Days 9-10: Documentation and Examples**
- Complete integration documentation
- Code examples for different platforms
- Usage guidelines and best practices

## Testing Strategy

### Unit Testing
- Tool wrapper functionality around existing VannaSnowflake methods
- Input validation and parameter handling
- Error handling scenarios
- Response formatting accuracy

### Integration Testing
- End-to-end function calling with OpenAI
- End-to-end function calling with Anthropic
- Performance testing with concurrent calls
- Error propagation from underlying VannaSnowflake

### Security Testing
- Input injection attempts through function parameters
- Parameter validation bypass attempts
- Data sanitization in responses

## Risk Assessment

### Low Risk (Simple Wrapper Approach)
**Implementation Complexity**
- *Status:* Simple wrapper around proven VannaSnowflake system
- *Mitigation:* Minimal new code, leveraging existing functionality

**Platform Compatibility**
- *Status:* Function calling is standardized across major LLM platforms
- *Mitigation:* Provide schemas for multiple platforms, simple JSON format

### Medium Risk
**Performance Overhead**
- *Risk:* Wrapper adds latency to existing system
- *Mitigation:* Minimal wrapper logic, direct method calls to VannaSnowflake

**Error Handling Consistency**
- *Risk:* Different error formats between platforms
- *Mitigation:* Standardized error response format, comprehensive testing

### High Risk
**Security Through Function Calling**
- *Risk:* LLMs might construct malicious function calls
- *Mitigation:* Comprehensive input validation, parameter sanitization, existing Snowflake security

## Success Criteria

### MVP Launch Criteria
- ✅ Working `VannaToolWrapper` class with core functionality
- ✅ Function schemas for OpenAI and Anthropic platforms
- ✅ Integration examples and documentation
- ✅ Security validation passing
- ✅ Performance overhead <100ms

### Post-Launch Goals (2 weeks)
- Integration examples with 3+ LLM platforms
- 100+ successful function calls in testing
- Documentation and examples published
- Zero security issues in wrapper layer

## Appendix

### Current VannaSnowflake Capabilities
Our existing system already provides:
- **Training:** Automatic DDL extraction, documentation training, example query training
- **Generation:** Natural language to SQL conversion via Vanna.AI
- **Execution:** Full Snowflake query execution with result formatting
- **Testing:** Connection validation and health checks
- **Logging:** Comprehensive error handling and debugging

### Integration Pattern
```python
# Before: Direct VannaSnowflake usage
vanna = VannaSnowflake()
result = vanna.ask("Show me total sales by region")

# After: LLM-callable wrapper
wrapper = VannaToolWrapper()
result = wrapper.snowflake_query("Show me total sales by region")

# LLM Function Calling
tools = [wrapper.get_function_schemas()['openai']]
# AI assistant can now call the tool automatically
```

### Deployment Strategy
- **Development:** Simple Python package/module
- **Distribution:** Can be imported alongside existing VannaSnowflake
- **No Infrastructure:** Runs in-process, no server required
- **Configuration:** Uses same config as existing VannaSnowflake system