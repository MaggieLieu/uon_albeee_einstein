import streamlit as st
import os
from uon_agent_albeee.agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

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
                # 1. Initialize the runner with your agent
                runner = InMemoryRunner(agent=root_agent)
                
                # 2. Format the message correctly for ADK
                user_content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
    
                # 3. Run the agent (use session_id to maintain history if desired)
                # For a simple stateless feel, you can use a fixed session_id
                events = runner.run(
                    user_id="streamlit_user",
                    session_id="default_session",
                    new_message=user_content
                )
    
                response_text = ""
                for event in events:
                    # Check for the final text response from the agent
                    if event.is_final_response() and event.content.parts:
                        response_text = event.content.parts[0].text
                
                if not response_text:
                    response_text = "I couldn't generate a response."
    
                # 4. Display and save the response
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

            except Exception as e:
                st.error(f"Error: {str(e)}")

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
