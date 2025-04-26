import os
import subprocess
import sys
import os
import subprocess
import sys
# Add this new line to import streamlit
import streamlit as st

def main():
    """
    Main entry point for the Elevate AI Companion application.
    This script helps run the Streamlit app located at src/ui/holistic_ui.py.
    """
    # Print welcome message
    print("=" * 80)
    print("Welcome to Elevate AI Companion")
    print("=" * 80)
    
    # Get the directory of the current script
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the path to the Streamlit app
    app_path = os.path.join(root_dir, "src", "ui", "holistic_ui.py")
    
    # Check if the app file exists
    if not os.path.exists(app_path):
        print(f"Error: Could not find the Streamlit app at {app_path}")
        return 1
    
    # Construct the command to run the Streamlit app
    port = os.environ.get('PORT', '8501')  # Get PORT from environment or default to 8501
    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        app_path, 
        f"--server.port={port}", 
        "--server.headless=true"
    ]
    
    print(f"Starting Streamlit app...")
    print(f"App path: {app_path}")
    print("=" * 80)
    print("Press Ctrl+C to stop the application")
    print("=" * 80)
    
    try:
        # Run the Streamlit app
        process = subprocess.run(cmd)
        return process.returncode
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        return 0
    except Exception as e:
        print(f"Error running the application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 