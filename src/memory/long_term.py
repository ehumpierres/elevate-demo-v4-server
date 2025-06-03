"""
Long-term memory implementation using Mem0.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from mem0 import MemoryClient
from config.config import MEM0_API_KEY, MEM0_ORG_ID, MEM0_PROJECT_ID, OUTPUT_FORMAT

class LongTermMemory:
    """Manages the long-term memory using Mem0."""
    
    def __init__(self):
        """Initialize the Mem0 client."""
        # Validate API credentials
        if not MEM0_API_KEY:
            raise ValueError("MEM0_API_KEY environment variable is not set")
        if not MEM0_ORG_ID:
            raise ValueError("MEM0_ORG_ID environment variable is not set")
        if not MEM0_PROJECT_ID:
            raise ValueError("MEM0_PROJECT_ID environment variable is not set")
            
        print(f"[DEBUG] Initializing Mem0 client with:")
        print(f"  API Key: {'*' * (len(MEM0_API_KEY) - 4) + MEM0_API_KEY[-4:] if MEM0_API_KEY else 'None'}")
        print(f"  Org ID: {MEM0_ORG_ID}")
        print(f"  Project ID: {MEM0_PROJECT_ID}")
        print(f"  Output Format: {OUTPUT_FORMAT}")
        
        try:
            self.mem0_client = MemoryClient(
                api_key=MEM0_API_KEY,
                org_id=MEM0_ORG_ID,
                project_id=MEM0_PROJECT_ID
            )
            print(f"✅ Mem0 client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Mem0 client: {e}")
            raise
    
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
            String with relevant memories
        """
        print(f"\n[DEBUG] Searching Mem0 with parameters:")
        print(f"  Query: {query}")
        print(f"  Entity ID: {entity_id}")
        print(f"  Is Agent: {is_agent}")
        print(f"  Agent ID: {entity_id if is_agent else None}")
        print(f"  User ID: {entity_id if not is_agent else None}")
        
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