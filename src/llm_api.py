"""
Module to handle interactions with the LLM API (OpenRouter).
"""
import httpx
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    OPENROUTER_API_KEY, 
    OPENROUTER_API_URL, 
    OPENROUTER_MODEL, 
    API_TIMEOUT,
    DEFAULT_MAX_COMPLETION_TOKENS  # Import the new config variable
)
from config.persona import get_system_prompt as get_arabella_prompt
from config.motions_analyst import get_system_prompt as get_motions_analyst_prompt

class LlmApi:
    """Handles interactions with the LLM API."""
    
    def __init__(self, analyst_type="Arabella (Business Architect)"):
        """
        Initialize the API connection.
        
        Args:
            analyst_type: The type of analyst to use for generating responses
        """
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        self.analyst_type = analyst_type
        
        # Set the appropriate system prompt function based on analyst type
        if analyst_type == "Sales Motion Strategy Agent":
            self.get_system_prompt = get_motions_analyst_prompt
        else:  # Default to Arabella
            self.get_system_prompt = get_arabella_prompt
    
    def generate_response(self, user_message, user_memories, companion_memories, recent_conversation, max_tokens=DEFAULT_MAX_COMPLETION_TOKENS):
        """
        Generate a response from the LLM.
        
        Args:
            user_message: The user's message
            user_memories: Memories related to the user
            companion_memories: Memories from the companion
            recent_conversation: Recent conversation history
            max_tokens: Maximum number of tokens to generate in the response (default from config)
            
        Returns:
            The generated response from the LLM
        """
        # Create the system prompt with all context
        system_prompt = self.get_system_prompt(user_memories, companion_memories, recent_conversation)
        
        # Prepare the payload
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": max_tokens  # Add max_tokens parameter to limit completion length
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
        print(f"Max tokens setting: {max_tokens}")
        print(json.dumps(result, indent=2))
        
        # Check for token usage and potential truncation
        if "usage" in result:
            completion_tokens = result["usage"].get("completion_tokens", 0)
            print(f"Completion tokens used: {completion_tokens}/{max_tokens}")
            if completion_tokens >= max_tokens * 0.95:  # 95% of limit
                print("⚠️ WARNING: Response may be truncated - approaching token limit!")
        
        print("=======================================\n")
        
        # Check if the response has the expected structure
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            print("WARNING: Unexpected response structure. Full response:", result)
            # Return a fallback message
            return "I apologize, but I encountered an issue with my response. Please try again or contact support." 