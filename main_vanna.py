"""
Main entry point for Vanna.ai Snowflake Explorer
"""
import os
import sys
import streamlit.web.cli as stcli
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the Streamlit app"""
    sys.argv = ["streamlit", "run", os.path.join("src", "ui", "streamlit_app.py")]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 