import streamlit as st
import os
from agent import root_agent

# Set up API key
# Option 1: From Streamlit secrets
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
# Option 2: From environment variable (already set)
elif "GOOGLE_API_KEY" not in os.environ:
    # Option 3: Prompt user to enter it
    st.error("⚠️ Google API Key not found!")
    api_key = st.text_input("Enter your Google API Key:", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.rerun()
    else:
        st.stop()

# Page configuration
st.set_page_config(
    page_title="Albeee Einstein - UoN Physics Assistant",
    page_icon="🔬",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        max-width: 800px;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔬 Albeee Einstein")
st.caption("Your University of Nottingham Physics & Astronomy Ambassador")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    welcome_msg = (
        "Hello! I'm Albeee Einstein, your guide to the University of Nottingham's "
        "School of Physics and Astronomy. Ask me anything about our courses, research, "
        "or the university!"
    )
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_msg
    })

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about Physics & Astronomy at UoN..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Send message to agent
                response = root_agent.send_message(prompt)
                
                # Extract the text response
                response_text = response.text if hasattr(response, 'text') else str(response)
                
                # Display response
                st.markdown(response_text)
                
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Sidebar with additional info
with st.sidebar:
    st.header("About")
    st.info(
        "This chatbot uses AI to answer questions about the University of Nottingham's "
        "School of Physics and Astronomy. Information may change, so always verify "
        "with the official university website."
    )
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    st.markdown("### Quick Links")
    st.markdown("""
    - [University of Nottingham](https://www.nottingham.ac.uk)
    - [Physics & Astronomy](https://www.nottingham.ac.uk/physics)
    """)
