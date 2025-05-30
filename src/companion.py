"""
Main companion application that coordinates all components.
"""
import os
import sys
import threading
import json

# Add the parent directory to the Python path when running directly
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.memory_manager import MemoryManager
from src.llm_api import LlmApi
from src.vanna_scripts import VannaToolWrapper
from config.config import (
    COMPANION_MAX_COMPLETION_TOKENS,
    API_CONVERSATION_HISTORY_LIMIT
)

class Companion:
    """
    AI companion with short-term and long-term memory and data analysis capabilities.
    
    This class coordinates between the memory systems, LLM API, and VannaToolWrapper
    to create a coherent conversation experience with database querying capabilities.
    """
    
    def __init__(self, user_id):
        """
        Initialize the companion.
        
        Args:
            user_id: The ID of the user
        """
        self.user_id = user_id
        self.memory_manager = MemoryManager(user_id)
        self.llm_api = LlmApi()
        self.vanna_wrapper = None  # Initialize lazily when needed
        self.data_analysis_enabled = True  # Enable data analysis by default
    
    def _get_vanna_wrapper(self):
        """Get or create VannaToolWrapper instance (lazy initialization)."""
        if self.vanna_wrapper is None:
            try:
                print("🔄 Companion: Initializing VannaToolWrapper...")
                self.vanna_wrapper = VannaToolWrapper()
                print("✅ Companion: VannaToolWrapper initialized successfully")
            except Exception as e:
                print(f"❌ Companion: Failed to initialize VannaToolWrapper: {e}")
                import traceback
                print(f"Full error: {traceback.format_exc()}")
                return None
        return self.vanna_wrapper
    
    def _store_conversation_async(self, user_message, assistant_response):
        """
        Store a conversation in long-term memory asynchronously.
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response
        """
        self.memory_manager.store_conversation(user_message, assistant_response)
    
    def _should_use_data_analysis(self, user_message):
        """
        Determine if the user message requires data analysis.
        
        Args:
            user_message: The user's message
            
        Returns:
            Boolean indicating if data analysis should be used
        """
        if not self.data_analysis_enabled:
            return False
        
        # Keywords that suggest data analysis is needed
        data_keywords = [
            'show me', 'how many', 'what is the', 'total', 'count', 'sum', 'average',
            'revenue', 'sales', 'customers', 'products', 'orders', 'data', 'report',
            'analysis', 'trend', 'performance', 'metrics', 'kpi', 'dashboard',
            'query', 'table', 'database', 'last quarter', 'this month', 'year'
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in data_keywords)
    
    def _analyze_data(self, user_message):
        """
        Analyze data using VannaToolWrapper.
        
        Args:
            user_message: The user's data question
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        print(f"🔍 Companion: Starting data analysis for: {user_message[:100]}...")
        
        wrapper = self._get_vanna_wrapper()
        if not wrapper:
            print("❌ Companion: VannaToolWrapper not available")
            return None
        
        try:
            print(f"🚀 Companion: Calling wrapper.snowflake_query()...")
            result = wrapper.snowflake_query(
                question=user_message,
                execute_query=True,
                max_results=100
            )
            
            print(f"✅ Companion: wrapper.snowflake_query() completed")
            print(f"📊 Companion: Result type: {type(result)}")
            
            if isinstance(result, dict):
                if result.get("success"):
                    print(f"✅ Companion: Data analysis successful: {result.get('row_count', 0)} rows returned")
                    print(f"📊 Companion: SQL length: {len(result.get('sql', '')) if result.get('sql') else 0}")
                    return result
                else:
                    print(f"❌ Companion: Data analysis failed: {result.get('error', 'Unknown error')}")
                    print(f"Full result: {result}")
                    return None
            else:
                print(f"❌ Companion: Unexpected result type: {type(result)}")
                print(f"Result: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Companion: Error in data analysis: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            return None
    
    def process_message(self, user_message):
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The message from the user
            
        Returns:
            The companion's response, optionally with data analysis results
        """
        # Add the user message to short-term memory
        self.memory_manager.add_user_message(user_message)
        
        # Check if this message requires data analysis
        data_result = None
        if self._should_use_data_analysis(user_message):
            print("🤖 Data analysis detected - querying database...")
            data_result = self._analyze_data(user_message)
        
        # Get relevant memories and conversation context
        memories = self.memory_manager.get_relevant_memories(user_message)
        
        # Use the limited API conversation history
        api_history = self.memory_manager.get_api_conversation_history(API_CONVERSATION_HISTORY_LIMIT)
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in api_history])
        
        # Debug print statements
        print("\n=== Conversation Context Debug Info ===")
        print(f"API conversation history limit: {API_CONVERSATION_HISTORY_LIMIT} messages")
        print(f"API conversation history actual length: {len(api_history)} messages")
        print(f"API conversation context tokens (estimated): {len(conversation_context) // 4} tokens")
        print(f"Full memory history length: {len(self.memory_manager.get_full_conversation_history())} messages")
        if data_result:
            print(f"Data analysis results: {data_result.get('row_count', 0)} rows")
        print("========================================\n")
        
        # Print long-term memories for debugging
        print("\n=== Retrieved Long-term Memories ===")
        print("User memories:", memories["user_memories"] if memories["user_memories"] else "None")
        print("Companion memories:", memories["companion_memories"] if memories["companion_memories"] else "None")
        print("===================================\n")
        
        # Prepare the message for the LLM
        enhanced_message = user_message
        
        # If we have data results, include them in the context
        if data_result and data_result.get("success"):
            data_context = f"""

DATA ANALYSIS RESULTS:
Question: {data_result.get('question', '')}
SQL Query: {data_result.get('sql', '')}
Results: {json.dumps(data_result.get('results', []), indent=2)}
Row Count: {data_result.get('row_count', 0)}
Execution Time: {data_result.get('execution_time_ms', 0)}ms

Please analyze these results and provide insights in your response. Reference the specific data points and explain what they mean for the business."""
            
            enhanced_message = user_message + data_context
        
        # Generate the response with a limit on completion tokens
        assistant_response = self.llm_api.generate_response(
            enhanced_message, 
            memories["user_memories"], 
            memories["companion_memories"], 
            conversation_context,
            max_tokens=COMPANION_MAX_COMPLETION_TOKENS
        )
        
        # Add the assistant response to short-term memory
        self.memory_manager.add_assistant_message(assistant_response)
        
        # Store the conversation in long-term memory asynchronously
        memory_thread = threading.Thread(
            target=self._store_conversation_async,
            args=(user_message, assistant_response)
        )
        memory_thread.daemon = True
        memory_thread.start()
        
        # Return response with optional data results
        response_data = {
            "response": assistant_response,
            "data_analysis": data_result if data_result and data_result.get("success") else None
        }
        
        return response_data
    
    def set_data_analysis_enabled(self, enabled):
        """Enable or disable data analysis capabilities."""
        self.data_analysis_enabled = enabled
        print(f"📊 Data analysis {'enabled' if enabled else 'disabled'}")
    
    def test_data_connection(self):
        """Test the data analysis connection."""
        wrapper = self._get_vanna_wrapper()
        if not wrapper:
            return {"success": False, "error": "VannaToolWrapper not available"}
        
        try:
            return wrapper.test_connection(detailed=True)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close(self):
        """Close all connections."""
        if self.vanna_wrapper:
            try:
                self.vanna_wrapper.close()
                print("🔗 VannaToolWrapper connections closed")
            except Exception as e:
                print(f"⚠️ Error closing VannaToolWrapper: {e}")

def main():
    """
    Main function to run the AI companion directly
    """
    print("Revenue Architect Companion with Data Analysis")
    print("----------------------------------------------")
    print("Start chatting with your companion about Revenue Architecture!")
    print("Ask data questions and I'll query the database for you.")
    print("Type 'exit' to end the conversation.\n")
    
    user_id = input("Please enter a username to identify you: ")
    companion = Companion(user_id)
    
    # Test data connection
    print("\n🔍 Testing data connection...")
    conn_result = companion.test_data_connection()
    if conn_result.get("success"):
        print("✅ Data connection successful!")
    else:
        print(f"⚠️ Data connection failed: {conn_result.get('error')}")
        print("You can still chat, but data analysis won't be available.")
    
    try:
        while True:
            user_input = input("\nYou: ")
            
            if user_input.lower() == 'exit':
                print("\nCompanion: Goodbye! It was nice chatting with you about Revenue Architecture!")
                break
            
            print("\nCompanion is thinking...")
            result = companion.process_message(user_input)
            
            # Handle the new response format
            if isinstance(result, dict) and "response" in result:
                print(f"\nCompanion: {result['response']}")
                
                # Show data analysis results if available
                if result.get("data_analysis"):
                    data = result["data_analysis"]
                    print(f"\n📊 Data Analysis Results:")
                    print(f"Query: {data.get('sql', 'N/A')}")
                    print(f"Rows: {data.get('row_count', 0)}")
                    if data.get('results'):
                        print("Sample results:")
                        for i, row in enumerate(data['results'][:3]):  # Show first 3 rows
                            print(f"  {i+1}: {row}")
            else:
                # Fallback for simple string response
                print(f"\nCompanion: {result}")
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    finally:
        companion.close()

if __name__ == "__main__":
    main() 