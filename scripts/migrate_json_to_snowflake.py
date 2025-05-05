#!/usr/bin/env python
"""
Script to migrate user conversation data from local JSON files to Snowflake.
"""
import os
import json
import sys
import glob
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vanna_scripts.snowflake_connector import SnowflakeConnector
from config.config import DATA_DIRECTORY, JSON_FILE_EXTENSION

def migrate_data():
    """Migrate all user data from JSON files to Snowflake."""
    print("Starting migration of JSON files to Snowflake...")
    
    # Initialize Snowflake connector
    snowflake = SnowflakeConnector()
    conn = snowflake.connect()
    cursor = conn.cursor()
    
    # Get all JSON files in the data directory
    json_pattern = os.path.join(DATA_DIRECTORY, f"*{JSON_FILE_EXTENSION}")
    json_files = glob.glob(json_pattern)
    
    print(f"Found {len(json_files)} JSON files to migrate.")
    
    success_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            # Extract user ID from filename
            user_id = os.path.basename(json_file).replace(JSON_FILE_EXTENSION, "")
            
            print(f"Migrating data for user: {user_id}")
            
            # Read JSON file
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract history and last updated timestamp
            history = data.get('history', [])
            last_updated = data.get('last_updated', datetime.now().isoformat())
            
            # Convert history to JSON string
            history_json = json.dumps(history)
            
            # Insert into Snowflake
            query = """
                MERGE INTO USER_CONVERSATIONS AS target
                USING (SELECT :user_id AS USER_ID, 
                              :last_updated AS LAST_UPDATED, 
                              PARSE_JSON(:history_json) AS CONVERSATION_HISTORY) AS source
                ON target.USER_ID = source.USER_ID
                WHEN MATCHED THEN
                    UPDATE SET 
                        LAST_UPDATED = source.LAST_UPDATED,
                        CONVERSATION_HISTORY = source.CONVERSATION_HISTORY
                WHEN NOT MATCHED THEN
                    INSERT (USER_ID, LAST_UPDATED, CONVERSATION_HISTORY)
                    VALUES (source.USER_ID, source.LAST_UPDATED, source.CONVERSATION_HISTORY)
            """
            
            cursor.execute(
                query, 
                {
                    "user_id": user_id, 
                    "last_updated": last_updated, 
                    "history_json": history_json
                }
            )
            
            success_count += 1
            print(f"Successfully migrated data for user: {user_id}")
            
        except Exception as e:
            error_count += 1
            print(f"Error migrating data for {os.path.basename(json_file)}: {e}")
    
    # Commit all changes
    conn.commit()
    cursor.close()
    
    print(f"Migration completed. Successfully migrated {success_count} files. Encountered {error_count} errors.")

if __name__ == "__main__":
    migrate_data() 