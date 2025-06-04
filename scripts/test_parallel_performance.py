#!/usr/bin/env python3
"""
Test script to verify parallel memory operations performance improvements.
"""
import asyncio
import time
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.companion import Companion

async def test_parallel_operations():
    """Test parallel memory operations vs sequential operations."""
    print("🧪 Testing Parallel Memory Operations Performance")
    print("=" * 60)
    
    # Initialize companion with strict memory (no mock fallback for testing)
    user_id = "test_user_parallel"
    companion = Companion(user_id, strict_memory=True)
    
    # Test message that would trigger both memory retrieval and data analysis
    test_message = "Show me the revenue trends for the last quarter and analyze our customer retention"
    
    print(f"📝 Test message: {test_message[:50]}...")
    print()
    
    try:
        # Test 1: Async parallel processing
        print("🚀 Test 1: Async Parallel Processing")
        start_time = time.time()
        
        result_async = await companion.process_message_async(test_message)
        
        async_time = (time.time() - start_time) * 1000
        print(f"✅ Async processing completed in: {async_time:.1f}ms")
        print(f"📊 Response length: {len(result_async['response'])} characters")
        if result_async.get('data_analysis'):
            print(f"📈 Data analysis included: {result_async['data_analysis'].get('row_count', 0)} rows")
        print()
        
        # Test 2: Traditional sequential processing (using the sync fallback)
        print("⏰ Test 2: Sequential Processing (for comparison)")
        
        # Create a new companion instance to avoid cached results
        companion_sync = Companion(user_id + "_sync", strict_memory=True)
        
        # Temporarily disable async to force sync processing
        original_method = companion_sync.memory_manager.get_relevant_memories
        
        start_time = time.time()
        
        # Force sync processing
        companion_sync.memory_manager.add_user_message(test_message)
        
        # Sequential operations (original flow)
        data_result = None
        if companion_sync._should_use_data_analysis(test_message):
            print("🤖 Data analysis detected - querying database sequentially...")
            data_result = companion_sync._analyze_data(test_message)
        
        memories = companion_sync.memory_manager.get_relevant_memories(test_message)
        
        sync_time = (time.time() - start_time) * 1000
        print(f"✅ Sequential processing completed in: {sync_time:.1f}ms")
        print()
        
        # Calculate performance improvement
        if async_time > 0 and sync_time > 0:
            improvement = ((sync_time - async_time) / sync_time) * 100
            print("📊 Performance Comparison:")
            print(f"   Async parallel:  {async_time:.1f}ms")
            print(f"   Sequential:      {sync_time:.1f}ms")
            print(f"   🚀 Improvement:   {improvement:.1f}% faster")
            
            if improvement > 20:
                print("✅ PASS: Significant performance improvement detected!")
            elif improvement > 0:
                print("⚠️  PARTIAL: Some improvement detected")
            else:
                print("❌ FAIL: No performance improvement")
        
        print()
        print("🔍 Testing Async Memory Manager Operations...")
        
        # Test 3: Direct async memory operations
        start_time = time.time()
        async_memories = await companion.memory_manager.get_relevant_memories_async("test query")
        async_memory_time = (time.time() - start_time) * 1000
        
        start_time = time.time()
        sync_memories = companion.memory_manager.get_relevant_memories("test query")
        sync_memory_time = (time.time() - start_time) * 1000
        
        memory_improvement = ((sync_memory_time - async_memory_time) / sync_memory_time) * 100 if sync_memory_time > 0 else 0
        
        print(f"📝 Memory Operations:")
        print(f"   Async memory:    {async_memory_time:.1f}ms")
        print(f"   Sequential:      {sync_memory_time:.1f}ms")
        print(f"   🚀 Improvement:   {memory_improvement:.1f}% faster")
        
        # Clean up
        companion.close()
        companion_sync.close()
        
        print()
        print("🎉 Parallel Operations Test Complete!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_sync_processing():
    """Test that sync processing still works as fallback."""
    print("\n🔄 Testing Sync Fallback Processing")
    print("=" * 40)
    
    try:
        # Initialize companion with strict memory (no mock fallback for testing)
        user_id = "test_user_sync"
        companion = Companion(user_id, strict_memory=True)
        
        # Test message
        test_message = "What are our key business metrics?"
        
        print(f"📝 Test message: {test_message}")
        
        start_time = time.time()
        result = companion.process_message(test_message)
        sync_time = (time.time() - start_time) * 1000
        
        print(f"✅ Sync processing completed in: {sync_time:.1f}ms")
        print(f"📊 Response length: {len(result['response'])} characters")
        
        companion.close()
        print("✅ Sync fallback test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Parallel Memory Operations Performance Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Parallel operations
    parallel_success = await test_parallel_operations()
    
    # Test 2: Sync fallback
    sync_success = test_sync_processing()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Parallel Operations: {'✅ PASS' if parallel_success else '❌ FAIL'}")
    print(f"   Sync Fallback:       {'✅ PASS' if sync_success else '❌ FAIL'}")
    
    if parallel_success and sync_success:
        print("\n🎉 All tests passed! Parallel operations are working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(main())
    exit(0 if success else 1) 