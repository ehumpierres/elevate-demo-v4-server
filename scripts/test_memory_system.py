#!/usr/bin/env python
"""
Test script to verify the memory system is working correctly with Snowflake.
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory.snowflake_memory import SnowflakeShortTermMemory
from src.vanna_scripts.snowflake_connector import SnowflakeConnector

def test_snowflake_connection():
    """Test basic Snowflake connection."""
    print("🔄 Testing Snowflake connection...")
    try:
        connector = SnowflakeConnector()
        conn = connector.connect()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
        result = cursor.fetchone()
        print(f"✅ Connected successfully!")
        print(f"   Database: {result[0]}")
        print(f"   Schema: {result[1]}")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_user_conversations_table():
    """Test if USER_CONVERSATIONS table exists and is accessible."""
    print("\n🔄 Testing USER_CONVERSATIONS table...")
    try:
        connector = SnowflakeConnector()
        conn = connector.connect()
        cursor = conn.cursor()
        
        # Check if table exists (try both uppercase and mixed case)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'CORRELATED_SCHEMA' 
            AND TABLE_NAME IN ('USER_CONVERSATIONS', 'user_conversations')
        """)
        
        result = cursor.fetchone()
        if result[0] == 0:
            print("❌ USER_CONVERSATIONS table does not exist!")
            print("   Please run the create_user_conversations_table.sql script first.")
            print("   Available tables in CORRELATED_SCHEMA:")
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'CORRELATED_SCHEMA'
                ORDER BY TABLE_NAME
            """)
            tables = cursor.fetchall()
            for table in tables:
                print(f"     - {table[0]}")
            return False
        
        # Test table structure
        cursor.execute("DESCRIBE TABLE USER_CONVERSATIONS")
        columns = cursor.fetchall()
        print("✅ USER_CONVERSATIONS table exists!")
        print("   Table structure:")
        for col in columns:
            print(f"     {col[0]} - {col[1]}")
        
        # Test permissions by trying to query
        cursor.execute("SELECT COUNT(*) FROM USER_CONVERSATIONS")
        count = cursor.fetchone()[0]
        print(f"   Current record count: {count}")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        import traceback
        print(f"   Full error: {traceback.format_exc()}")
        return False

def test_memory_system():
    """Test the memory system end-to-end."""
    print("\n🔄 Testing memory system...")
    try:
        # Create a test user
        test_user_id = "test_user_123"
        memory = SnowflakeShortTermMemory(test_user_id)
        
        print(f"✅ Memory system initialized for user: {test_user_id}")
        
        # Add a test message
        memory.add_message("user", "Hello, this is a test message")
        print("✅ Test message added successfully")
        
        # Verify it was saved
        history = memory.get_full_history()
        if len(history) > 0:
            print(f"✅ Message saved and retrieved. History length: {len(history)}")
            print(f"   Last message: {history[-1]}")
        else:
            print("❌ No messages found in history")
            return False
        
        # Clean up test data
        connector = SnowflakeConnector()
        conn = connector.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM USER_CONVERSATIONS WHERE USER_ID = %s", (test_user_id,))
        conn.commit()
        cursor.close()
        print("✅ Test data cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback
        print(f"   Full error: {traceback.format_exc()}")
        return False

def main():
    """Run all tests."""
    print("=== Memory System Diagnostics ===")
    
    # Test 1: Basic connection
    conn_success = test_snowflake_connection()
    
    # Test 2: Table existence
    table_success = test_user_conversations_table() if conn_success else False
    
    # Test 3: Memory system
    memory_success = test_memory_system() if table_success else False
    
    print("\n=== Test Summary ===")
    print(f"Snowflake Connection: {'✅ PASS' if conn_success else '❌ FAIL'}")
    print(f"USER_CONVERSATIONS Table: {'✅ PASS' if table_success else '❌ FAIL'}")
    print(f"Memory System: {'✅ PASS' if memory_success else '❌ FAIL'}")
    
    if conn_success and table_success and memory_success:
        print("\n🎉 All tests passed! Your memory system should be working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please address the issues above.")
        if not table_success:
            print("   HINT: Run the create_user_conversations_table.sql script in Snowflake first.")

if __name__ == "__main__":
    main() 