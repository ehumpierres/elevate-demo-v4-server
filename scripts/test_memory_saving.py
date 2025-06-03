#!/usr/bin/env python3
"""
Test script to verify memory saving functionality with Mem0.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.long_term import LongTermMemory
from src.memory.memory_manager import MemoryManager
from config.config import COMPANION_ID

def test_mem0_direct():
    """Test direct Mem0 functionality."""
    print("🔍 Testing direct Mem0 functionality...")
    
    try:
        long_term_memory = LongTermMemory()
        print("✅ LongTermMemory initialized successfully")
        
        # Test storing a simple memory
        test_content = [
            {"role": "user", "content": "What is our current revenue?"},
            {"role": "assistant", "content": "Based on the latest data, our Q4 revenue was $2.3M, showing 15% growth YoY."}
        ]
        
        test_user_id = "test_memory_user"
        
        print(f"\n🔄 Testing memory storage for user: {test_user_id}")
        user_result = long_term_memory.store_memory(test_content, test_user_id, is_agent=False)
        print(f"User memory storage result: {user_result}")
        
        print(f"\n🔄 Testing memory storage for companion: {COMPANION_ID}")
        companion_result = long_term_memory.store_memory(test_content, COMPANION_ID, is_agent=True)
        print(f"Companion memory storage result: {companion_result}")
        
        if user_result and companion_result:
            print("✅ Direct Mem0 memory storage test passed!")
            
            # Test memory retrieval
            print(f"\n🔍 Testing memory retrieval...")
            query = "revenue growth"
            
            user_memories = long_term_memory.search_memories(query, test_user_id, is_agent=False)
            print(f"Retrieved user memories: {user_memories}")
            
            companion_memories = long_term_memory.search_memories(query, COMPANION_ID, is_agent=True)
            print(f"Retrieved companion memories: {companion_memories}")
            
            return True
        else:
            print("❌ Direct Mem0 memory storage test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct Mem0 test: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_memory_manager():
    """Test memory manager functionality."""
    print("\n🔍 Testing MemoryManager functionality...")
    
    try:
        test_user_id = "test_memory_manager_user"
        memory_manager = MemoryManager(test_user_id)
        print("✅ MemoryManager initialized successfully")
        
        # Test storing a conversation
        user_message = "Show me our customer acquisition metrics for Q4"
        assistant_message = "Our Q4 customer acquisition metrics show: CAC of $450, 120 new customers acquired, with a 25% conversion rate from trial to paid."
        
        print(f"\n🔄 Testing conversation storage...")
        result = memory_manager.store_conversation(user_message, assistant_message)
        print(f"Conversation storage result: {result}")
        
        if result["overall_success"]:
            print("✅ MemoryManager conversation storage test passed!")
            
            # Test memory retrieval through memory manager
            print(f"\n🔍 Testing memory retrieval through MemoryManager...")
            query = "customer acquisition"
            memories = memory_manager.get_relevant_memories(query)
            print(f"Retrieved memories: {memories}")
            
            return True
        else:
            print("❌ MemoryManager conversation storage test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error in MemoryManager test: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def main():
    """Run all memory tests."""
    print("🧠 Memory Saving Test Suite")
    print("=" * 50)
    
    # Test 1: Direct Mem0 functionality
    mem0_success = test_mem0_direct()
    
    # Test 2: Memory Manager functionality
    manager_success = test_memory_manager()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    print(f"  Direct Mem0 test: {'✅ PASSED' if mem0_success else '❌ FAILED'}")
    print(f"  MemoryManager test: {'✅ PASSED' if manager_success else '❌ FAILED'}")
    
    if mem0_success and manager_success:
        print("\n🎉 All memory tests passed! Memory saving should be working correctly.")
    else:
        print("\n⚠️ Some memory tests failed. Check the error messages above for details.")
        print("\nCommon issues to check:")
        print("  1. Verify MEM0_API_KEY, MEM0_ORG_ID, and MEM0_PROJECT_ID are set in your .env file")
        print("  2. Check your internet connection")
        print("  3. Verify Mem0 API service is accessible")
        print("  4. Check if there are any API rate limits or quota issues")

if __name__ == "__main__":
    main() 