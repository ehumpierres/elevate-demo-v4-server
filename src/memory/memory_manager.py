"""
Memory manager to coordinate between short-term and long-term memory systems.
"""
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import COMPANION_ID

class MemoryManager:
    """
    Manages both short-term and long-term memory systems.
    
    This class coordinates between the JSON-based short-term memory
    and the Mem0-based long-term memory.
    """
    
    def __init__(self, user_id):
        """
        Initialize the memory manager.
        
        Args:
            user_id: The ID of the user
        """
        self.user_id = user_id
        self.short_term = ShortTermMemory(user_id)
        self.long_term = LongTermMemory()
    
    def add_user_message(self, content):
        """
        Add a user message to both short-term and long-term memory.
        
        Args:
            content: The content of the user message
        """
        # Add to short-term memory
        self.short_term.add_message("user", content)
    
    def add_assistant_message(self, content):
        """
        Add an assistant message to both short-term and long-term memory.
        
        Args:
            content: The content of the assistant message
        """
        # Add to short-term memory
        self.short_term.add_message("assistant", content)
    
    def store_conversation(self, user_message, assistant_message):
        """
        Store a complete conversation exchange in long-term memory.
        
        Args:
            user_message: The user's message
            assistant_message: The assistant's response
        """
        conversation_content = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        # Store in long-term memory for both user and companion
        self.long_term.store_memory(conversation_content, self.user_id)
        self.long_term.store_memory(conversation_content, COMPANION_ID, is_agent=True)
    
    def get_relevant_memories(self, query):
        """
        Retrieve relevant memories for the given query.
        
        Args:
            query: The query to search for memories
            
        Returns:
            Dict containing user memories and companion memories
        """
        print(f"\n[DEBUG] MemoryManager searching with query: {query}")
        user_memories = self.long_term.search_memories(query, self.user_id)
        companion_memories = self.long_term.search_memories(query, COMPANION_ID, is_agent=True)
        
        return {
            "user_memories": user_memories,
            "companion_memories": companion_memories
        }
    
    def get_conversation_context(self):
        """
        Get the recent conversation history for context.
        
        Returns:
            Formatted conversation history of recent messages
        """
        return self.short_term.get_formatted_history()
    
    def get_raw_history(self):
        """
        Get the raw recent conversation history.
        
        Returns:
            List of recent conversation message dictionaries
        """
        return self.short_term.get_raw_history()
    
    def get_full_conversation_history(self):
        """
        Get the complete conversation history.
        
        Returns:
            List of all conversation message dictionaries
        """
        return self.short_term.get_full_history() 