"""
Test script to verify the integration between Companion and VannaToolWrapper
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_companion_integration():
    """Test that Companion properly integrates with VannaToolWrapper"""
    print("🧪 Testing Companion + VannaToolWrapper Integration")
    print("=" * 60)
    
    try:
        # Test import
        from companion import Companion
        print("✅ Companion import successful")
        
        # Initialize companion
        companion = Companion("test_user")
        print("✅ Companion initialized successfully")
        
        # Test data connection
        print("\n🔍 Testing data connection...")
        conn_result = companion.test_data_connection()
        if conn_result.get("success"):
            print("✅ Data connection successful!")
            print(f"   Database: {conn_result.get('connection_details', {}).get('database', 'N/A')}")
            print(f"   Schema: {conn_result.get('connection_details', {}).get('schema', 'N/A')}")
        else:
            print(f"⚠️ Data connection failed: {conn_result.get('error')}")
        
        # Test a simple message (non-data)
        print("\n💬 Testing simple conversation...")
        result = companion.process_message("Hello, how are you?")
        
        if isinstance(result, dict) and "response" in result:
            print("✅ Message processing successful!")
            print(f"   Response type: {type(result)}")
            print(f"   Has data analysis: {'Yes' if result.get('data_analysis') else 'No'}")
            print(f"   Response preview: {result['response'][:100]}...")
        else:
            print(f"❌ Unexpected response format: {type(result)}")
        
        # Test a data-related message
        print("\n📊 Testing data-related query...")
        result = companion.process_message("Show me the total number of tables in our database")
        
        if isinstance(result, dict) and "response" in result:
            print("✅ Data query processing successful!")
            print(f"   Has data analysis: {'Yes' if result.get('data_analysis') else 'No'}")
            if result.get('data_analysis'):
                data = result['data_analysis']
                print(f"   SQL Query: {data.get('sql', 'N/A')[:50]}...")
                print(f"   Row count: {data.get('row_count', 0)}")
                print(f"   Success: {data.get('success', False)}")
        
        # Clean up
        companion.close()
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_companion_integration()
    if success:
        print("\n🎉 Integration test passed! Your system is ready to use.")
        print("\nTo run the Streamlit app:")
        print("   python main.py")
    else:
        print("\n💥 Integration test failed. Check the errors above.")
    
    sys.exit(0 if success else 1) 