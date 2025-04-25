"""
Module to handle interactions with the LLM API (OpenRouter).
"""
import httpx
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL, API_TIMEOUT
from config.persona import get_system_prompt

class LlmApi:
    """Handles interactions with the LLM API."""
    
    def __init__(self):
        """Initialize the API connection."""
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def generate_response(self, user_message, user_memories, companion_memories, recent_conversation):
        """
        Generate a response from the LLM.
        
        Args:
            user_message: The user's message
            user_memories: Memories related to the user
            companion_memories: Memories from the companion
            recent_conversation: Recent conversation history
            
        Returns:
            The generated response from the LLM
        """
        # Create the system prompt with all context
        system_prompt = get_system_prompt(user_memories, companion_memories, recent_conversation)
        
        # Prepare the payload
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        
        # Make the API call
        response = httpx.post(
            OPENROUTER_API_URL,
            headers=self.headers,
            json=payload,
            timeout=API_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Debug: Print the full response structure
        print("\n=== OpenRouter API Response Structure ===")
        print(f"Model used: {OPENROUTER_MODEL}")
        print(json.dumps(result, indent=2))
        print("=======================================\n")
        
        # Check if the response has the expected structure
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            print("WARNING: Unexpected response structure. Full response:", result)
            # Return a fallback message
            return "I apologize, but I encountered an issue with my response. Please try again or contact support." 