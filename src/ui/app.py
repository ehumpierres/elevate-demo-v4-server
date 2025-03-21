"""
Streamlit UI for the Revenue Architect AI companion.
"""
import os
import sys
import streamlit as st

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.companion import Companion

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "companion" not in st.session_state:
        st.session_state.companion = None
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Revenue Architect Companion",
        page_icon="💼",
        layout="wide"
    )
    
    initialize_session_state()
    
    st.title("💼 Revenue Architect Companion")
    st.subheader("Chat with Arabella about Revenue Architecture")
    
    # Sidebar for user information
    with st.sidebar:
        st.header("User Information")
        
        # User ID input
        user_id = st.text_input("Enter your username:", key="user_id_input")
        
        if st.button("Start Session") and user_id:
            st.session_state.user_id = user_id
            st.session_state.companion = Companion(user_id)
            st.session_state.messages = []
            st.success(f"Session started for user: {user_id}")
        
        st.divider()
        st.markdown("### About Arabella")
        st.markdown("""
        Arabella is an expert business analyst and consultant specializing in GTM Systems 
        thinking and Revenue Architecture frameworks for sustainable business growth.
        """)
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.messages = []
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                # For equations and formulas, use code blocks to preserve formatting
                if "\\text" in message["content"] or "\\times" in message["content"]:
                    # Group consecutive equation lines together
                    lines = message["content"].split('\n')
                    i = 0
                    while i < len(lines):
                        # Skip empty lines
                        if not lines[i].strip():
                            i += 1
                            continue
                            
                        # Check if current line is an equation
                        is_equation = "\\text" in lines[i] or "\\times" in lines[i] or lines[i].strip() in ["=", "+", "-", "(", ")", "×"]
                        
                        if is_equation:
                            # Find consecutive equation lines
                            equation_block = [lines[i]]
                            j = i + 1
                            while j < len(lines) and ("\\text" in lines[j] or "\\times" in lines[j] or lines[j].strip() in ["=", "+", "-", "(", ")", "×"]):
                                equation_block.append(lines[j])
                                j += 1
                            
                            # Display the equation block as a single code block
                            st.code('\n'.join(equation_block), language=None)
                            i = j
                        else:
                            # Find consecutive text lines
                            text_block = [lines[i]]
                            j = i + 1
                            while j < len(lines) and not ("\\text" in lines[j] or "\\times" in lines[j] or lines[j].strip() in ["=", "+", "-", "(", ")", "×"]):
                                if lines[j].strip():  # Skip empty lines
                                    text_block.append(lines[j])
                                j += 1
                            
                            # Display the text block
                            st.markdown('\n'.join(text_block))
                            i = j
                else:
                    # Regular message without equations
                    st.markdown(message["content"])
    
    # Chat input
    if st.session_state.companion:
        user_input = st.chat_input("Ask Arabella about Revenue Architecture...")
        
        if user_input:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Get response from companion
            with st.chat_message("assistant"):
                with st.spinner("Arabella is thinking..."):
                    response = st.session_state.companion.process_message(user_input)
                    
                    # For equations and formulas, use code blocks to preserve formatting
                    if "\\text" in response or "\\times" in response:
                        # Group consecutive equation lines together
                        lines = response.split('\n')
                        i = 0
                        while i < len(lines):
                            # Skip empty lines
                            if not lines[i].strip():
                                i += 1
                                continue
                                
                            # Check if current line is an equation
                            is_equation = "\\text" in lines[i] or "\\times" in lines[i] or lines[i].strip() in ["=", "+", "-", "(", ")", "×"]
                            
                            if is_equation:
                                # Find consecutive equation lines
                                equation_block = [lines[i]]
                                j = i + 1
                                while j < len(lines) and ("\\text" in lines[j] or "\\times" in lines[j] or lines[j].strip() in ["=", "+", "-", "(", ")", "×"]):
                                    equation_block.append(lines[j])
                                    j += 1
                                
                                # Display the equation block as a single code block
                                st.code('\n'.join(equation_block), language=None)
                                i = j
                            else:
                                # Find consecutive text lines
                                text_block = [lines[i]]
                                j = i + 1
                                while j < len(lines) and not ("\\text" in lines[j] or "\\times" in lines[j] or lines[j].strip() in ["=", "+", "-", "(", ")", "×"]):
                                    if lines[j].strip():  # Skip empty lines
                                        text_block.append(lines[j])
                                    j += 1
                                
                                # Display the text block
                                st.markdown('\n'.join(text_block))
                                i = j
                    else:
                        # Regular message without equations
                        st.markdown(response)
            
            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.info("Please enter your username and start a session to begin chatting.")

if __name__ == "__main__":
    main() 