"""
Long-term memory implementation using Mem0.
"""
import sys
import os
import asyncio
from mem0 import Memory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import MEM0_API_KEY, MEM0_ORG_ID, MEM0_PROJECT_ID, OUTPUT_FORMAT

class LongTermMemory:
    """Manages the long-term memory using Mem0."""
    
    def __init__(self, fail_on_error=False):
        """
        Initialize the Mem0 client.
        
        Args:
            fail_on_error: If True, raise exception if Mem0 fails. If False, operate without long-term memory.
        """
        # Initialize the Mem0 client
        print(f"[DEBUG] Initializing Mem0 client with:")
        print(f"  API Key: {MEM0_API_KEY[:40] + '...' if MEM0_API_KEY else 'None'}")
        print(f"  Org ID: {MEM0_ORG_ID}")
        print(f"  Project ID: {MEM0_PROJECT_ID}")
        print(f"  Output Format: {OUTPUT_FORMAT}")
        
        self.mem0_client = None  # Will be None if initialization fails
        self.is_operational = False
        
        try:
            # Try the new Memory initialization format first
            config = {
                "provider": "mem0",
                "config": {
                    "api_key": MEM0_API_KEY,
                    "org_id": MEM0_ORG_ID,
                    "project_id": MEM0_PROJECT_ID,
                }
            }
            self.mem0_client = Memory.from_config(config)
            self.is_operational = True
            print("✅ LongTermMemory initialized with Mem0 (new format)")
        except (AttributeError, TypeError) as e:
            print(f"⚠️ New format failed ({e}), trying legacy format...")
            try:
                # Fallback to legacy initialization format
                self.mem0_client = Memory()
                self.is_operational = True
                print("✅ LongTermMemory initialized with Mem0 (legacy format)")
            except Exception as e2:
                print(f"❌ Failed to initialize Mem0 client: {e2}")
                if fail_on_error:
                    print("💥 Failing fast as requested")
                    raise e2
                else:
                    print("🔄 Operating without long-term memory - no fake data will be generated")
                    self.mem0_client = None
                    self.is_operational = False
    
    def _create_mock_client(self):
        """This method is removed - we don't use mock clients anymore."""
        raise NotImplementedError("Mock clients are not used - system operates without memory when Mem0 fails")
    
    def is_degraded(self):
        """Check if the memory system is operating in degraded mode."""
        return not self.is_operational
    
    def get_status(self):
        """Get the current status of the memory system."""
        if not self.is_operational:
            return {
                "status": "unavailable",
                "message": "Mem0 client unavailable - operating without long-term memory",
                "capabilities": {
                    "can_store": False,
                    "can_retrieve": False,
                    "data_persistent": False
                }
            }
        else:
            return {
                "status": "operational", 
                "message": "Mem0 client operational",
                "capabilities": {
                    "can_store": True,
                    "can_retrieve": True,
                    "data_persistent": True
                }
            }
    
    def store_memory(self, content, entity_id, is_agent=False):
        """
        Store a memory for either the user or the companion.
        
        Args:
            content: The conversation content to store
            entity_id: The ID of the entity (user or agent)
            is_agent: Boolean to determine if the entity is the agent or user
            
        Returns:
            Boolean indicating success/failure
        """
        if not self.is_operational:
            print("⚠️ WARNING: Mem0 client unavailable - memory not stored")
            return False
        
        try:
            print(f"\n[DEBUG] Storing memory to Mem0:")
            print(f"  Entity ID: {entity_id}")
            print(f"  Is Agent: {is_agent}")
            print(f"  Agent ID: {entity_id if is_agent else None}")
            print(f"  User ID: {entity_id if not is_agent else None}")
            print(f"  Content type: {type(content)}")
            print(f"  Content length: {len(str(content)) if content else 0}")
            
            result = self.mem0_client.add(
                content,
                agent_id=entity_id if is_agent else None,
                user_id=entity_id if not is_agent else None,
                output_format=OUTPUT_FORMAT
            )
            
            print(f"\n[DEBUG] Mem0 add response:")
            print(f"  {result}")
            
            if result:
                print(f"✅ Memory stored successfully to Mem0")
                return True
            else:
                print(f"⚠️ Mem0 returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Error storing memory to Mem0: {e}")
            import traceback
            print(f"   Full error: {traceback.format_exc()}")
            return False
    
    def search_memories(self, query, entity_id, is_agent=False):
        """
        Retrieve memories based on a query for either the user or the companion.
        
        Args:
            query: The search query
            entity_id: The ID of the entity (user or agent)
            is_agent: Boolean to determine if the entity is the agent or user
            
        Returns:
            String with relevant memories (empty string if Mem0 unavailable)
        """
        if not self.is_operational:
            print("⚠️ WARNING: Mem0 client unavailable - no long-term memories available")
            return ""  # Return empty string instead of fake data
        
        print(f"\n[DEBUG] Searching Mem0 with parameters:")
        print(f"  Query: {query}")
        print(f"  Entity ID: {entity_id}")
        print(f"  Is Agent: {is_agent}")
        print(f"  Agent ID: {entity_id if is_agent else None}")
        print(f"  User ID: {entity_id if not is_agent else None}")
        
        try:
            memories = self.mem0_client.search(
                query,
                agent_id=entity_id if is_agent else None,
                user_id=entity_id if not is_agent else None,
                output_format=OUTPUT_FORMAT
            )
            
            print(f"\n[DEBUG] Raw Mem0 response:")
            print(f"  {memories}")
            
            # Extract memories from the response
            if memories and "results" in memories:
                # Sort memories by score in descending order
                sorted_memories = sorted(memories["results"], key=lambda x: x.get("score", 0), reverse=True)
                # Extract and join the memory strings
                extracted = "\n".join([m["memory"] for m in sorted_memories])
                print(f"\n[DEBUG] Extracted memories:")
                print(f"  {extracted}")
                return extracted
            
            print("\n[DEBUG] No memories extracted from response")
            return ""
        except Exception as e:
            print(f"❌ Error searching memories: {e}")
            return ""  # Return empty instead of fake data
    
    async def search_memories_async(self, query, entity_id, is_agent=False):
        """
        Asynchronously retrieve memories based on a query for either the user or the companion.
        
        Args:
            query: The search query
            entity_id: The ID of the entity (user or agent)
            is_agent: Boolean to determine if the entity is the agent or user
            
        Returns:
            String with relevant memories (empty string if Mem0 unavailable)
        """
        if not self.is_operational:
            print("⚠️ WARNING: Mem0 client unavailable - no long-term memories available")
            return ""  # Return empty string instead of fake data
        
        print(f"\n[DEBUG] Async searching Mem0 with parameters:")
        print(f"  Query: {query}")
        print(f"  Entity ID: {entity_id}")
        print(f"  Is Agent: {is_agent}")
        print(f"  Agent ID: {entity_id if is_agent else None}")
        print(f"  User ID: {entity_id if not is_agent else None}")
        
        try:
            # Run the Mem0 search in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            memories = await loop.run_in_executor(
                None,
                lambda: self.mem0_client.search(
                    query,
                    agent_id=entity_id if is_agent else None,
                    user_id=entity_id if not is_agent else None,
                    output_format=OUTPUT_FORMAT
                )
            )
            
            print(f"\n[DEBUG] Async Mem0 response:")
            print(f"  {memories}")
            
            # Extract memories from the response
            if memories and "results" in memories:
                # Sort memories by score in descending order
                sorted_memories = sorted(memories["results"], key=lambda x: x.get("score", 0), reverse=True)
                # Extract and join the memory strings
                extracted = "\n".join([m["memory"] for m in sorted_memories])
                print(f"\n[DEBUG] Extracted async memories:")
                print(f"  {extracted}")
                return extracted
            
            print("\n[DEBUG] No memories extracted from async response")
            return ""
            
        except Exception as e:
            print(f"❌ Error in async memory search: {e}")
            return ""  # Return empty instead of fake data
    
    async def store_memory_async(self, content, entity_id, is_agent=False):
        """
        Asynchronously store a memory for either the user or the companion.
        
        Args:
            content: The conversation content to store
            entity_id: The ID of the entity (user or agent)
            is_agent: Boolean to determine if the entity is the agent or user
            
        Returns:
            Boolean indicating success/failure
        """
        if not self.is_operational:
            print("⚠️ WARNING: Mem0 client unavailable - memory not stored")
            return False
        
        try:
            print(f"\n[DEBUG] Async storing memory to Mem0:")
            print(f"  Entity ID: {entity_id}")
            print(f"  Is Agent: {is_agent}")
            print(f"  Agent ID: {entity_id if is_agent else None}")
            print(f"  User ID: {entity_id if not is_agent else None}")
            print(f"  Content type: {type(content)}")
            print(f"  Content length: {len(str(content)) if content else 0}")
            
            # Run the Mem0 add operation in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.mem0_client.add(
                    content,
                    agent_id=entity_id if is_agent else None,
                    user_id=entity_id if not is_agent else None,
                    output_format=OUTPUT_FORMAT
                )
            )
            
            print(f"\n[DEBUG] Async Mem0 add response:")
            print(f"  {result}")
            
            if result:
                print(f"✅ Memory stored asynchronously to Mem0")
                return True
            else:
                print(f"⚠️ Async Mem0 returned empty response")
                return False
                
        except Exception as e:
            print(f"❌ Error in async memory storage: {e}")
            return False  # Return False instead of falling back to anything
    
    def get_client(self):
        """Get the Mem0 client (may be None if unavailable)."""
        return self.mem0_client
    
    def set_client(self, client):
        """Set the Mem0 client (useful for testing)."""
        self.mem0_client = client
        self.is_operational = client is not None 