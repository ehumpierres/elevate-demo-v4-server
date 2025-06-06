"""
Main companion application that coordinates all components with optimized performance.
"""
import os
import sys
import threading
import json
import re
import time
import asyncio
from functools import lru_cache
from datetime import date, datetime

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

# Custom JSON encoder to handle date objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

class DataAnalysisDetector:
    """Fast cached data analysis detection with optimized patterns."""
    
    def __init__(self):
        self.cache = {}
        self.cache_max_size = 1000
        self.common_patterns = self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for faster matching."""
        data_keywords = [
            r'\bshow\s+me\b', r'\bhow\s+many\b', r'\bwhat\s+is\s+the\b', 
            r'\btotal\b', r'\bcount\b', r'\bsum\b', r'\baverage\b', r'\bmean\b',
            r'\brevenue\b', r'\bsales\b', r'\bcustomers?\b', r'\bproducts?\b', 
            r'\borders?\b', r'\bdata\b', r'\breports?\b', r'\banalysis\b', 
            r'\btrends?\b', r'\bperformance\b', r'\bmetrics?\b', r'\bkpis?\b', 
            r'\bdashboard\b', r'\bquery\b', r'\btables?\b', r'\bdatabase\b',
            r'\blast\s+quarter\b', r'\bthis\s+month\b', r'\byears?\b',
            r'\btop\s+\d+\b', r'\bbottom\s+\d+\b', r'\bcompare\b', r'\bfilter\b'
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in data_keywords]
    
    def should_analyze(self, message):
        """
        Fast detection with caching for data analysis needs.
        
        Args:
            message: The user's message
            
        Returns:
            Boolean indicating if data analysis should be used
        """
        # Create cache key
        msg_normalized = message.lower().strip()
        msg_hash = hash(msg_normalized)
        
        # Check cache first
        if msg_hash in self.cache:
            return self.cache[msg_hash]
        
        # Fast regex pattern matching
        result = any(pattern.search(msg_normalized) for pattern in self.common_patterns)
        
        # Cache the result (with LRU-style cleanup)
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest 20% of cache entries
            old_keys = list(self.cache.keys())[:len(self.cache) // 5]
            for key in old_keys:
                del self.cache[key]
        
        self.cache[msg_hash] = result
        return result

class Companion:
    """
    AI companion with short-term and long-term memory and data analysis capabilities.
    
    This class coordinates between the memory systems, LLM API, and VannaToolWrapper
    to create a coherent conversation experience with database querying capabilities.
    """
    
    def __init__(self, user_id, analyst_type="GTM Leadership Strategist", strict_memory=False):
        """
        Initialize the companion.
        
        Args:
            user_id: The ID of the user
            analyst_type: The type of analyst to use (default: "GTM Leadership Strategist")
            strict_memory: If True, fail if Mem0 is unavailable instead of using mock (default: False)
        """
        self.user_id = user_id
        self.analyst_type = analyst_type
        self.memory_manager = MemoryManager(user_id, strict_memory=strict_memory)
        self.llm_api = LlmApi(analyst_type=analyst_type)
        self.vanna_wrapper = None  # Initialize lazily when needed
        self.data_analysis_enabled = True  # Enable data analysis by default
        
        # Performance optimizations
        self.data_detector = DataAnalysisDetector()
        self._session_active = True
        
        # Check memory status on initialization
        memory_status = self.memory_manager.get_memory_status()
        if self.memory_manager.is_memory_degraded():
            print("⚠️ WARNING: Companion initialized with degraded memory capabilities")
            print(f"   Long-term memory: {memory_status['long_term']['message']}")
        else:
            print("✅ Companion initialized with full memory capabilities")
    
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
        try:
            print(f"\n[DEBUG] Companion: Starting async memory storage...")
            result = self.memory_manager.store_conversation(user_message, assistant_response)
            
            if result["overall_success"]:
                print(f"✅ Companion: Long-term memory storage completed successfully")
            else:
                print(f"⚠️ Companion: Memory storage partially failed:")
                print(f"   User memory: {'✅' if result['user_memory_saved'] else '❌'}")
                print(f"   Companion memory: {'✅' if result['companion_memory_saved'] else '❌'}")
                
        except Exception as e:
            print(f"❌ Companion: Error in async memory storage: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")
    
    def _should_use_data_analysis(self, user_message):
        """
        Determine if the user message requires data analysis (optimized with caching).
        
        Args:
            user_message: The user's message
            
        Returns:
            Boolean indicating if data analysis should be used
        """
        if not self.data_analysis_enabled:
            return False
        
        start_time = time.time()
        result = self.data_detector.should_analyze(user_message)
        detection_time = (time.time() - start_time) * 1000
        
        print(f"🚀 Data analysis detection: {result} (took {detection_time:.1f}ms)")
        return result
    
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
    
    async def _analyze_data_async(self, user_message):
        """
        Asynchronously analyze data using VannaToolWrapper.
        
        Args:
            user_message: The user's data question
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        print(f"🔍 Companion: Starting async data analysis for: {user_message[:100]}...")
        
        wrapper = self._get_vanna_wrapper()
        if not wrapper:
            print("❌ Companion: VannaToolWrapper not available")
            return None
        
        try:
            print(f"🚀 Companion: Calling async wrapper.snowflake_query()...")
            
            # Run the data analysis in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: wrapper.snowflake_query(
                    question=user_message,
                    execute_query=True,
                    max_results=100
                )
            )
            
            print(f"✅ Companion: async wrapper.snowflake_query() completed")
            print(f"📊 Companion: Result type: {type(result)}")
            
            if isinstance(result, dict):
                if result.get("success"):
                    print(f"✅ Companion: Async data analysis successful: {result.get('row_count', 0)} rows returned")
                    print(f"📊 Companion: SQL length: {len(result.get('sql', '')) if result.get('sql') else 0}")
                    return result
                else:
                    print(f"❌ Companion: Async data analysis failed: {result.get('error', 'Unknown error')}")
                    print(f"Full result: {result}")
                    return None
            else:
                print(f"❌ Companion: Unexpected async result type: {type(result)}")
                print(f"Result: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Companion: Error in async data analysis: {e}")
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            # Fallback to sync method
            print("🔄 Falling back to synchronous data analysis...")
            return self._analyze_data(user_message)
    
    async def _store_conversation_async_new(self, user_message, assistant_response):
        """
        Store a conversation in long-term memory asynchronously using the new async methods.
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response
        """
        try:
            print(f"\n[DEBUG] Companion: Starting new async memory storage...")
            result = await self.memory_manager.store_conversation_async(user_message, assistant_response)
            
            if result["overall_success"]:
                print(f"✅ Companion: New async long-term memory storage completed successfully")
            else:
                print(f"⚠️ Companion: New async memory storage partially failed:")
                print(f"   User memory: {'✅' if result['user_memory_saved'] else '❌'}")
                print(f"   Companion memory: {'✅' if result['companion_memory_saved'] else '❌'}")
                
        except Exception as e:
            print(f"❌ Companion: Error in new async memory storage: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")
    
    async def process_message_async(self, user_message):
        """
        Process a user message asynchronously with parallel memory retrieval and data analysis.
        
        Args:
            user_message: The message from the user
            
        Returns:
            The companion's response, optionally with data analysis results
        """
        # Add the user message to short-term memory
        self.memory_manager.add_user_message(user_message)
        
        # Start parallel operations
        start_time = time.time()
        
        # Check if this message requires data analysis
        needs_data_analysis = self._should_use_data_analysis(user_message)
        
        # Create tasks for parallel execution
        memory_task = asyncio.create_task(
            self.memory_manager.get_relevant_memories_async(user_message)
        )
        
        data_task = None
        if needs_data_analysis:
            print("🤖 Data analysis detected - querying database in parallel...")
            data_task = asyncio.create_task(self._analyze_data_async(user_message))
        
        # Get conversation context (this is fast, so we can do it synchronously)
        api_history = self.memory_manager.get_api_conversation_history(API_CONVERSATION_HISTORY_LIMIT)
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in api_history])
        
        # Wait for parallel operations to complete
        if data_task:
            memories, data_result = await asyncio.gather(
                memory_task, data_task, return_exceptions=True
            )
        else:
            memories = await memory_task
            data_result = None
        
        # Handle exceptions from parallel operations
        if isinstance(memories, Exception):
            print(f"⚠️ Memory retrieval failed: {memories}")
            memories = {"user_memories": "", "companion_memories": ""}
        
        if isinstance(data_result, Exception):
            print(f"⚠️ Data analysis failed: {data_result}")
            data_result = None
        
        parallel_time = (time.time() - start_time) * 1000
        print(f"🚀 Parallel operations completed in {parallel_time:.1f}ms")
        
        # Debug print statements
        print("\n=== Async Conversation Context Debug Info ===")
        print(f"API conversation history limit: {API_CONVERSATION_HISTORY_LIMIT} messages")
        print(f"API conversation history actual length: {len(api_history)} messages")
        print(f"API conversation context tokens (estimated): {len(conversation_context) // 4} tokens")
        print(f"Full memory history length: {len(self.memory_manager.get_full_conversation_history())} messages")
        if data_result:
            print(f"Data analysis results: {data_result.get('row_count', 0)} rows")
        print("============================================\n")
        
        # Print long-term memories for debugging
        print("\n=== Retrieved Long-term Memories (Async) ===")
        print("User memories:", memories["user_memories"] if memories["user_memories"] else "None")
        print("Companion memories:", memories["companion_memories"] if memories["companion_memories"] else "None")
        print("==========================================\n")
        
        # Prepare the message for the LLM
        enhanced_message = user_message
        
        # If we have data results, include them in the context
        if data_result and data_result.get("success"):
            data_context = f"""

DATA ANALYSIS RESULTS:
Question: {data_result.get('question', '')}
SQL Query: {data_result.get('sql', '')}
Results: {json.dumps(data_result.get('results', []), indent=2, cls=CustomJSONEncoder)}
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
        
        # Store the conversation in long-term memory asynchronously using the new async method
        print(f"\n[DEBUG] Companion: Initiating new async memory storage...")
        asyncio.create_task(self._store_conversation_async_new(user_message, assistant_response))
        print(f"[DEBUG] Companion: New async memory storage task started")
        
        # Return response with optional data results
        response_data = {
            "response": assistant_response,
            "data_analysis": data_result if data_result and data_result.get("success") else None
        }
        
        return response_data

    def process_message(self, user_message):
        """
        Process a user message and generate a response using async optimization when possible.
        
        Args:
            user_message: The message from the user
            
        Returns:
            The companion's response, optionally with data analysis results
        """
        # Try to use async version if we can get or create an event loop
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task for async processing
                print("🚀 Using async parallel processing...")
                return asyncio.run_coroutine_threadsafe(
                    self.process_message_async(user_message), loop
                ).result()
            else:
                # Run async version with asyncio.run
                print("🚀 Using async parallel processing...")
                return asyncio.run(self.process_message_async(user_message))
        except (RuntimeError, AttributeError):
            # If we can't use async (no event loop), fall back to sync version
            print("ℹ️ Falling back to synchronous processing...")
            
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
Results: {json.dumps(data_result.get('results', []), indent=2, cls=CustomJSONEncoder)}
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
            print(f"\n[DEBUG] Companion: Initiating async memory storage thread...")
            memory_thread = threading.Thread(
                target=self._store_conversation_async,
                args=(user_message, assistant_response)
            )
            memory_thread.daemon = True
            memory_thread.start()
            print(f"[DEBUG] Companion: Memory storage thread started")
            
            # Return response with optional data results
            response_data = {
                "response": assistant_response,
                "data_analysis": data_result if data_result and data_result.get("success") else None
            }
            
            return response_data
    
    async def process_message_stream_async(self, user_message):
        """
        Process a user message asynchronously and generate a streaming response with parallel operations.
        
        Args:
            user_message: The message from the user
            
        Returns:
            A tuple containing:
            - Generator that yields chunks of the response
            - Dictionary with metadata (data_analysis, etc.)
        """
        # Add the user message to short-term memory
        self.memory_manager.add_user_message(user_message)
        
        # Start parallel operations
        start_time = time.time()
        
        # Check if this message requires data analysis
        needs_data_analysis = self._should_use_data_analysis(user_message)
        
        # Create tasks for parallel execution
        memory_task = asyncio.create_task(
            self.memory_manager.get_relevant_memories_async(user_message)
        )
        
        data_task = None
        if needs_data_analysis:
            print("🤖 Data analysis detected - querying database in parallel...")
            data_task = asyncio.create_task(self._analyze_data_async(user_message))
        
        # Get conversation context (this is fast, so we can do it synchronously)
        api_history = self.memory_manager.get_api_conversation_history(API_CONVERSATION_HISTORY_LIMIT)
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in api_history])
        
        # Wait for parallel operations to complete
        if data_task:
            memories, data_result = await asyncio.gather(
                memory_task, data_task, return_exceptions=True
            )
        else:
            memories = await memory_task
            data_result = None
        
        # Handle exceptions from parallel operations
        if isinstance(memories, Exception):
            print(f"⚠️ Memory retrieval failed: {memories}")
            memories = {"user_memories": "", "companion_memories": ""}
        
        if isinstance(data_result, Exception):
            print(f"⚠️ Data analysis failed: {data_result}")
            data_result = None
        
        parallel_time = (time.time() - start_time) * 1000
        print(f"🚀 Async streaming parallel operations completed in {parallel_time:.1f}ms")
        
        # Debug print statements
        print("\n=== Async Streaming Conversation Context Debug Info ===")
        print(f"API conversation history limit: {API_CONVERSATION_HISTORY_LIMIT} messages")
        print(f"API conversation history actual length: {len(api_history)} messages")
        print(f"API conversation context tokens (estimated): {len(conversation_context) // 4} tokens")
        print(f"Full memory history length: {len(self.memory_manager.get_full_conversation_history())} messages")
        if data_result:
            print(f"Data analysis results: {data_result.get('row_count', 0)} rows")
        print("======================================================\n")
        
        # Print long-term memories for debugging
        print("\n=== Retrieved Long-term Memories (Async Stream) ===")
        print("User memories:", memories["user_memories"] if memories["user_memories"] else "None")
        print("Companion memories:", memories["companion_memories"] if memories["companion_memories"] else "None")
        print("=================================================\n")
        
        # Prepare the message for the LLM
        enhanced_message = user_message
        
        # If we have data results, include them in the context
        if data_result and data_result.get("success"):
            data_context = f"""

DATA ANALYSIS RESULTS:
Question: {data_result.get('question', '')}
SQL Query: {data_result.get('sql', '')}
Results: {json.dumps(data_result.get('results', []), indent=2, cls=CustomJSONEncoder)}
Row Count: {data_result.get('row_count', 0)}
Execution Time: {data_result.get('execution_time_ms', 0)}ms

Please analyze these results and provide insights in your response. Reference the specific data points and explain what they mean for the business."""
            
            enhanced_message = user_message + data_context
        
        # Create the metadata dict
        metadata = {
            "data_analysis": data_result if data_result and data_result.get("success") else None
        }
        
        # Create the streaming generator
        def stream_generator():
            full_response = ""
            try:
                for chunk in self.llm_api.generate_response_stream(
                    enhanced_message, 
                    memories["user_memories"], 
                    memories["companion_memories"], 
                    conversation_context,
                    max_tokens=COMPANION_MAX_COMPLETION_TOKENS
                ):
                    full_response += chunk
                    yield chunk
                    
            except Exception as e:
                print(f"❌ Error during async streaming: {e}")
                error_message = f"I encountered an error while generating my response: {str(e)}"
                full_response = error_message
                yield error_message
            
            # Store the complete response for memory after streaming
            metadata["full_response"] = full_response
            
            # Add the complete assistant response to short-term memory
            self.memory_manager.add_assistant_message(full_response)
            
            # Store the conversation in long-term memory asynchronously using the new async method
            print(f"\n[DEBUG] Companion: Initiating new async memory storage from stream...")
            asyncio.create_task(self._store_conversation_async_new(user_message, full_response))
            print(f"[DEBUG] Companion: New async memory storage task started from stream")
        
        return stream_generator(), metadata

    def process_message_stream(self, user_message):
        """
        Process a user message and generate a streaming response using async optimization when possible.
        
        Args:
            user_message: The message from the user
            
        Returns:
            A tuple containing:
            - Generator that yields chunks of the response
            - Dictionary with metadata (data_analysis, etc.)
        """
        # Try to use async version if we can get or create an event loop
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this carefully for streaming
                print("🚀 Using async parallel processing for streaming...")
                # Create a future that will be resolved with the async result
                future = asyncio.run_coroutine_threadsafe(
                    self.process_message_stream_async(user_message), loop
                )
                return future.result()
            else:
                # Run async version with asyncio.run
                print("🚀 Using async parallel processing for streaming...")
                return asyncio.run(self.process_message_stream_async(user_message))
        except (RuntimeError, AttributeError):
            # If we can't use async (no event loop), fall back to sync version
            print("ℹ️ Falling back to synchronous streaming processing...")
            
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
            print("\n=== Streaming Conversation Context Debug Info ===")
            print(f"API conversation history limit: {API_CONVERSATION_HISTORY_LIMIT} messages")
            print(f"API conversation history actual length: {len(api_history)} messages")
            print(f"API conversation context tokens (estimated): {len(conversation_context) // 4} tokens")
            print(f"Full memory history length: {len(self.memory_manager.get_full_conversation_history())} messages")
            if data_result:
                print(f"Data analysis results: {data_result.get('row_count', 0)} rows")
            print("===============================================\n")
            
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
Results: {json.dumps(data_result.get('results', []), indent=2, cls=CustomJSONEncoder)}
Row Count: {data_result.get('row_count', 0)}
Execution Time: {data_result.get('execution_time_ms', 0)}ms

Please analyze these results and provide insights in your response. Reference the specific data points and explain what they mean for the business."""
                
                enhanced_message = user_message + data_context
            
            # Create the metadata dict
            metadata = {
                "data_analysis": data_result if data_result and data_result.get("success") else None
            }
            
            # Create the streaming generator
            def stream_generator():
                full_response = ""
                try:
                    for chunk in self.llm_api.generate_response_stream(
                        enhanced_message, 
                        memories["user_memories"], 
                        memories["companion_memories"], 
                        conversation_context,
                        max_tokens=COMPANION_MAX_COMPLETION_TOKENS
                    ):
                        full_response += chunk
                        yield chunk
                        
                except Exception as e:
                    print(f"❌ Error during streaming: {e}")
                    error_message = f"I encountered an error while generating my response: {str(e)}"
                    full_response = error_message
                    yield error_message
                
                # Store the complete response for memory after streaming
                metadata["full_response"] = full_response
                
                # Add the complete assistant response to short-term memory
                self.memory_manager.add_assistant_message(full_response)
                
                # Store the conversation in long-term memory asynchronously
                print(f"\n[DEBUG] Companion: Initiating async memory storage thread...")
                memory_thread = threading.Thread(
                    target=self._store_conversation_async,
                    args=(user_message, full_response)
                )
                memory_thread.daemon = True
                memory_thread.start()
                print(f"[DEBUG] Companion: Memory storage thread started")
            
            return stream_generator(), metadata
    
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
        """Close all connections and flush pending operations."""
        print(f"🔄 Companion: Closing session for user {self.user_id}")
        
        self._session_active = False
        
        # Force write any pending memory operations
        try:
            if hasattr(self.memory_manager.short_term, 'force_write'):
                self.memory_manager.short_term.force_write()
            if hasattr(self.memory_manager.short_term, 'close'):
                self.memory_manager.short_term.close()
            print("✅ Companion: Memory writes flushed")
        except Exception as e:
            print(f"⚠️ Companion: Error flushing memory: {e}")
        
        # Close VannaToolWrapper connections
        if self.vanna_wrapper:
            try:
                self.vanna_wrapper.close()
                print("✅ Companion: VannaToolWrapper connections closed")
            except Exception as e:
                print(f"⚠️ Companion: Error closing VannaToolWrapper: {e}")
        
        print("🔚 Companion: Session closed successfully")

    def get_system_status(self):
        """Get the overall system status including memory and data connections."""
        memory_status = self.memory_manager.get_memory_status()
        
        # Test data connection
        data_status = self.test_data_connection()
        
        return {
            "memory": memory_status,
            "data_analysis": {
                "status": "operational" if data_status.get("success") else "degraded",
                "message": "Snowflake data analysis available" if data_status.get("success") else f"Data analysis unavailable: {data_status.get('error', 'Unknown error')}",
                "capabilities": {
                    "can_query": data_status.get("success", False),
                    "can_analyze": data_status.get("success", False)
                }
            },
            "overall_health": "operational" if not self.memory_manager.is_memory_degraded() and data_status.get("success") else "degraded"
        }

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
    
    # Analyst selection
    print("\nSelect your AI Analyst:")
    print("1. Arabella (Business Architect) - General business strategy expert")
    print("2. Sales Motion Strategy Agent - Specialized in sales motion optimization")
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice == "1":
            analyst_type = "Arabella (Business Architect)"
            break
        elif choice == "2":
            analyst_type = "Sales Motion Strategy Agent"
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    
    print(f"\nInitializing {analyst_type}...")
    companion = Companion(user_id, analyst_type=analyst_type)
    
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