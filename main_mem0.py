"""
Main entry point for running the AI companion.
"""
import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """
    Main function to run the AI companion.
    
    This launches the Streamlit interface for a more interactive experience.
    If you prefer the command-line interface, you can run src/companion.py directly.
    """
    print("Revenue Architect Companion")
    print("--------------------------------")
    print("Launching Streamlit interface...")
    
    # Get the path to the Streamlit app
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "ui", "app.py")
    
    try:
        # Launch Streamlit
        subprocess.run(["streamlit", "run", app_path], check=True)
    except FileNotFoundError:
        print("\nError: Streamlit not found. Please install it with:")
        print("pip install streamlit")
        print("\nOr run the command-line interface directly with:")
        print("python src/companion.py")
    except subprocess.CalledProcessError:
        print("\nError launching Streamlit. Please check your installation.")
    except KeyboardInterrupt:
        print("\nStreamlit interface closed.")

if __name__ == "__main__":
    main() 