"""
Main companion application that coordinates all components.
"""
import os
import sys
import threading

# Add the parent directory to the Python path when running directly
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.memory_manager import MemoryManager
from src.llm_api import LlmApi
from config.config import (
    COMPANION_MAX_COMPLETION_TOKENS,
    API_CONVERSATION_HISTORY_LIMIT
)

class Companion:
    """
    AI companion with short-term and long-term memory.
    
    This class coordinates between the memory systems and LLM API
    to create a coherent conversation experience.
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
    
    def _store_conversation_async(self, user_message, assistant_response):
        """
        Store a conversation in long-term memory asynchronously.
        
        Args:
            user_message: The user's message
            assistant_response: The assistant's response
        """
        self.memory_manager.store_conversation(user_message, assistant_response)
    
    def process_message(self, user_message):
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The message from the user
            
        Returns:
            The companion's response
        """
        # Add the user message to short-term memory
        self.memory_manager.add_user_message(user_message)
        
        # Get relevant memories and conversation context
        memories = self.memory_manager.get_relevant_memories(user_message)
        
        # Use the limited API conversation history instead of the full context
        # Limit is set in config.py as API_CONVERSATION_HISTORY_LIMIT
        api_history = self.memory_manager.get_api_conversation_history(API_CONVERSATION_HISTORY_LIMIT)
        conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in api_history])
        
        # Debug print statements to show conversation context length
        print("\n=== Conversation Context Debug Info ===")
        print(f"API conversation history limit: {API_CONVERSATION_HISTORY_LIMIT} messages")
        print(f"API conversation history actual length: {len(api_history)} messages")
        print(f"API conversation context tokens (estimated): {len(conversation_context) // 4} tokens")
        print(f"Full memory history length: {len(self.memory_manager.get_full_conversation_history())} messages")
        print("========================================\n")
        
        # Print long-term memories for debugging
        print("\n=== Retrieved Long-term Memories ===")
        print("User memories:", memories["user_memories"] if memories["user_memories"] else "None")
        print("Companion memories:", memories["companion_memories"] if memories["companion_memories"] else "None")
        print("===================================\n")
        
        # Generate the response with a limit on completion tokens
        # Token limit is set in config.py as COMPANION_MAX_COMPLETION_TOKENS
        assistant_response = self.llm_api.generate_response(
            user_message, 
            memories["user_memories"], 
            memories["companion_memories"], 
            conversation_context,
            max_tokens=COMPANION_MAX_COMPLETION_TOKENS
        )
        
        # Add the assistant response to short-term memory
        self.memory_manager.add_assistant_message(assistant_response)
        
        # Store the conversation in long-term memory asynchronously
        # This prevents the slow memory storage from delaying the response to the user
        memory_thread = threading.Thread(
            target=self._store_conversation_async,
            args=(user_message, assistant_response)
        )
        memory_thread.daemon = True  # Make thread exit when main program exits
        memory_thread.start()
        
        return assistant_response

def main():
    """
    Main function to run the AI companion directly
    """
    print("Revenue Architect Companion")
    print("--------------------------------")
    print("Start chatting with your companion about Revenue Architecture!")
    print("Type 'exit' to end the conversation.\n")
    
    user_id = input("Please enter a username to identify you: ")
    companion = Companion(user_id)
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            print("\nCompanion: Goodbye! It was nice chatting with you about Revenue Architecture!")
            break
        
        print("\nCompanion is thinking...")
        response = companion.process_message(user_input)
        print(f"\nCompanion: {response}")

if __name__ == "__main__":
    main() 