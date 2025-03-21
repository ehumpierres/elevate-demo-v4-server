"""
Short-term memory implementation using JSON files.
"""
import json
import os
from collections import deque
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import DATA_DIRECTORY, SHORT_TERM_MEMORY_SIZE, JSON_FILE_EXTENSION

class ShortTermMemory:
    """Manages the short-term conversation memory using JSON files."""
    
    def __init__(self, user_id):
        """
        Initialize the short-term memory for a specific user.
        
        Args:
            user_id: The ID of the user
        """
        self.user_id = user_id
        self.file_path = self._get_file_path()
        self.full_history = []  # Store all messages
        self.recent_history = deque(maxlen=SHORT_TERM_MEMORY_SIZE)  # Only recent messages for context
        self._load_conversation()
    
    def _get_file_path(self):
        """Get the file path for the user's conversation history."""
        if not os.path.exists(DATA_DIRECTORY):
            os.makedirs(DATA_DIRECTORY)
        return os.path.join(DATA_DIRECTORY, f"{self.user_id}{JSON_FILE_EXTENSION}")
    
    def _load_conversation(self):
        """Load the conversation history from the JSON file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                
                # Load the full history
                self.full_history = data.get('history', [])
                
                # Load the most recent messages into the deque for context
                recent_messages = self.full_history[-SHORT_TERM_MEMORY_SIZE:] if len(self.full_history) > SHORT_TERM_MEMORY_SIZE else self.full_history
                self.recent_history = deque(recent_messages, maxlen=SHORT_TERM_MEMORY_SIZE)
    
    def save_conversation(self):
        """Save the current conversation history to the JSON file."""
        data = {
            'user_id': self.user_id,
            'last_updated': datetime.now().isoformat(),
            'history': self.full_history  # Save the full history
        }
        
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_message(self, role, content):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role of the message sender (user or assistant)
            content: The content of the message
        """
        message = {"role": role, "content": content}
        
        # Add to both full history and recent history
        self.full_history.append(message)
        self.recent_history.append(message)
        
        # Save the updated conversation
        self.save_conversation()
    
    def get_formatted_history(self):
        """
        Get the recent conversation history formatted as a string.
        
        Returns:
            Formatted conversation history (only recent messages)
        """
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.recent_history])
    
    def get_raw_history(self):
        """
        Get the raw recent conversation history as a list of message dictionaries.
        
        Returns:
            List of recent message dictionaries
        """
        return list(self.recent_history)
    
    def get_full_history(self):
        """
        Get the complete conversation history.
        
        Returns:
            List of all message dictionaries
        """
        return self.full_history 