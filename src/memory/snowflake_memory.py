"""
Short-term memory implementation using Snowflake.
"""
import json
from collections import deque
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.config import SHORT_TERM_MEMORY_SIZE
from src.vanna_scripts.snowflake_connector import SnowflakeConnector

class SnowflakeShortTermMemory:
    """Manages the short-term conversation memory using Snowflake."""
    
    def __init__(self, user_id):
        """
        Initialize the short-term memory for a specific user.
        
        Args:
            user_id: The ID of the user
        """
        self.user_id = user_id
        self.full_history = []  # Store all messages
        self.recent_history = deque(maxlen=SHORT_TERM_MEMORY_SIZE)  # Only recent messages for context
        self.snowflake = SnowflakeConnector()
        self._load_conversation()
    
    def _load_conversation(self):
        """Load the conversation history from Snowflake."""
        try:
            # Connect to Snowflake
            conn = self.snowflake.connect()
            cursor = conn.cursor()
            
            # Query to get the user's conversation history
            query = """
                SELECT conversation_history 
                FROM user_conversations 
                WHERE user_id = :user_id
            """
            
            cursor.execute(query, {"user_id": self.user_id})
            result = cursor.fetchone()
            
            if result and result[0]:
                # Parse the conversation history from the VARIANT column
                data = result[0]
                
                # Load the full history
                self.full_history = data
                
                # Load the most recent messages into the deque for context
                recent_messages = self.full_history[-SHORT_TERM_MEMORY_SIZE:] if len(self.full_history) > SHORT_TERM_MEMORY_SIZE else self.full_history
                self.recent_history = deque(recent_messages, maxlen=SHORT_TERM_MEMORY_SIZE)
            
            cursor.close()
        except Exception as e:
            print(f"Error loading conversation from Snowflake: {e}")
            # Initialize with empty history if there's an error
            self.full_history = []
            self.recent_history = deque(maxlen=SHORT_TERM_MEMORY_SIZE)
    
    def save_conversation(self):
        """Save the current conversation history to Snowflake."""
        try:
            # Connect to Snowflake
            conn = self.snowflake.connect()
            cursor = conn.cursor()
            
            # MERGE statement (UPSERT) to insert or update the conversation
            query = """
                MERGE INTO user_conversations AS target
                USING (SELECT :user_id AS user_id, 
                              :last_updated AS last_updated, 
                              PARSE_JSON(:history_json) AS conversation_history) AS source
                ON target.user_id = source.user_id
                WHEN MATCHED THEN
                    UPDATE SET 
                        last_updated = source.last_updated,
                        conversation_history = source.conversation_history
                WHEN NOT MATCHED THEN
                    INSERT (user_id, last_updated, conversation_history)
                    VALUES (source.user_id, source.last_updated, source.conversation_history)
            """
            
            # Convert the full_history to a JSON string
            history_json = json.dumps(self.full_history)
            
            # Execute the query with parameters
            cursor.execute(
                query, 
                {
                    "user_id": self.user_id, 
                    "last_updated": datetime.now().isoformat(), 
                    "history_json": history_json
                }
            )
            
            # Commit the transaction
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Error saving conversation to Snowflake: {e}")
    
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
    
    def get_api_history(self, limit=30):
        """
        Get the most recent conversation history for API calls, limited to the specified number.
        
        Args:
            limit: Maximum number of recent messages to return
            
        Returns:
            List of the most recent message dictionaries, limited to the specified count
        """
        return self.full_history[-limit:] if len(self.full_history) > limit else self.full_history 