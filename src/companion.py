"""
Main companion application that coordinates all components.
"""
import os
import sys

# Add the parent directory to the Python path when running directly
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.memory_manager import MemoryManager
from src.llm_api import LlmApi

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
        conversation_context = self.memory_manager.get_conversation_context()
        
        # Print long-term memories for debugging
        print("\n=== Retrieved Long-term Memories ===")
        print("User memories:", memories["user_memories"] if memories["user_memories"] else "None")
        print("Companion memories:", memories["companion_memories"] if memories["companion_memories"] else "None")
        print("===================================\n")
        
        # Generate the response
        assistant_response = self.llm_api.generate_response(
            user_message, 
            memories["user_memories"], 
            memories["companion_memories"], 
            conversation_context
        )
        
        # Add the assistant response to short-term memory
        self.memory_manager.add_assistant_message(assistant_response)
        
        # Store the conversation in long-term memory
        self.memory_manager.store_conversation(user_message, assistant_response)
        
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