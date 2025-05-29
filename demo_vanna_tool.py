"""
Demonstration script for VannaToolWrapper

This script shows how to use the VannaToolWrapper for:
1. Direct usage (without LLM integration)
2. Getting function schemas for different platforms
3. Example integration patterns with OpenAI and Anthropic

Run this script to test the wrapper functionality.
"""

import json
from src.vanna_scripts import VannaToolWrapper, create_vanna_tools

def demo_direct_usage():
    """Demonstrate direct usage of VannaToolWrapper"""
    print("=" * 60)
    print("DEMO 1: Direct Usage of VannaToolWrapper")
    print("=" * 60)
    
    try:
        # Create wrapper instance
        wrapper = VannaToolWrapper()
        print("✓ VannaToolWrapper initialized successfully")
        
        # Test connection first
        print("\n1. Testing Snowflake connection...")
        connection_result = wrapper.test_connection(detailed=True)
        print(f"Connection test result: {json.dumps(connection_result, indent=2)}")
        
        if connection_result.get("success"):
            print("✓ Snowflake connection successful")
            
            # Test a simple query (SQL generation only)
            print("\n2. Testing SQL generation (without execution)...")
            result = wrapper.snowflake_query(
                question="Show me the top 5 customers by sales",
                execute_query=False
            )
            print(f"SQL Generation result: {json.dumps(result, indent=2)}")
            
            # Test a simple query with execution (if connection works)
            print("\n3. Testing full query with execution...")
            result = wrapper.snowflake_query(
                question="SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = CURRENT_SCHEMA()",
                execute_query=True,
                max_results=10
            )
            print(f"Query execution result: {json.dumps(result, indent=2)}")
        else:
            print("⚠ Snowflake connection failed, skipping query tests")
            
        # Close connections
        wrapper.close()
        print("\n✓ VannaToolWrapper closed successfully")
        
    except Exception as e:
        print(f"❌ Error in direct usage demo: {str(e)}")

def demo_function_schemas():
    """Demonstrate getting function schemas for different platforms"""
    print("\n" + "=" * 60)
    print("DEMO 2: Function Schemas for LLM Platforms")
    print("=" * 60)
    
    try:
        schemas = VannaToolWrapper.get_function_schemas()
        
        print("\n1. OpenAI Function Calling Format:")
        print(json.dumps(schemas["openai"], indent=2))
        
        print("\n2. Anthropic Tool Use Format:")
        print(json.dumps(schemas["anthropic"], indent=2))
        
        print("\n3. Generic Format:")
        print(json.dumps(schemas["generic"], indent=2))
        
    except Exception as e:
        print(f"❌ Error getting function schemas: {str(e)}")

def demo_openai_integration():
    """Show example OpenAI integration pattern (pseudocode)"""
    print("\n" + "=" * 60)
    print("DEMO 3: OpenAI Integration Pattern (Pseudocode)")
    print("=" * 60)
    
    print("""
# Example OpenAI integration:
import openai
from src.vanna_scripts import VannaToolWrapper

# Initialize wrapper
wrapper = VannaToolWrapper()

# Get function schemas
tools = VannaToolWrapper.get_function_schemas()["openai"]

# Use with OpenAI
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "What are our top selling products this quarter?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle function calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "snowflake_query":
            args = json.loads(tool_call.function.arguments)
            result = wrapper.snowflake_query(**args)
            print(f"Query result: {result}")
            
        elif tool_call.function.name == "test_connection":
            args = json.loads(tool_call.function.arguments)
            result = wrapper.test_connection(**args)
            print(f"Connection test: {result}")
""")

def demo_anthropic_integration():
    """Show example Anthropic integration pattern (pseudocode)"""
    print("\n" + "=" * 60)
    print("DEMO 4: Anthropic Integration Pattern (Pseudocode)")
    print("=" * 60)
    
    print("""
# Example Anthropic integration:
import anthropic
from src.vanna_scripts import VannaToolWrapper

# Initialize wrapper
wrapper = VannaToolWrapper()

# Get function schemas
tools = VannaToolWrapper.get_function_schemas()["anthropic"]

# Use with Anthropic
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
        print(f"Query result: {result}")
""")

def demo_error_handling():
    """Demonstrate error handling capabilities"""
    print("\n" + "=" * 60)
    print("DEMO 5: Error Handling")
    print("=" * 60)
    
    try:
        wrapper = VannaToolWrapper()
        
        # Test invalid question
        print("1. Testing invalid question (empty string):")
        result = wrapper.snowflake_query("")
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Test invalid max_results
        print("\n2. Testing invalid max_results:")
        result = wrapper.snowflake_query(
            question="SELECT 1", 
            max_results=2000  # Over limit
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        
        wrapper.close()
        
    except Exception as e:
        print(f"❌ Error in error handling demo: {str(e)}")

if __name__ == "__main__":
    print("VannaToolWrapper Demonstration")
    print("This demo shows how to use the VannaToolWrapper for LLM integration")
    
    # Run all demos
    demo_direct_usage()
    demo_function_schemas()
    demo_openai_integration()
    demo_anthropic_integration()
    demo_error_handling()
    
    print("\n" + "=" * 60)
    print("Demo completed! Check the output above for results.")
    print("Note: Some demos require proper Snowflake configuration to work fully.")
    print("=" * 60) 