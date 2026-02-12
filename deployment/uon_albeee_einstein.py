import streamlit as st
import os
from google.adk.runners import InMemoryRunner # New import
from google.genai import types # Required for message formatting
from uon_agent_albeee.agent import root_agent

# --- SECURE API KEY ---
# This pulls the key you just put in the 'Advanced Settings' (Secrets)
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Albeee Einstein", page_icon="⚛️")
st.title("Einstein UoN Ambassador")

# --- INITIALIZE RUNNER ---
# The Runner manages the execution and session history
if "runner" not in st.session_state:
    st.session_state.runner = InMemoryRunner(agent=root_agent)

# Chat history initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- CHAT INPUT & EXECUTION ---
if prompt := st.chat_input("Ask about Physics at Nottingham..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Format the message for ADK
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    with st.spinner("Einstein is thinking..."):
        # The ADK Runner requires a user_id and session_id to track the chat
        event_stream = st.session_state.runner.run(
            user_id="streamlit_user",
            session_id="current_chat",
            new_message=user_message
        )
        
        # Collect the final text response from the event stream
        answer = ""
        for event in event_stream:
            if event.is_final_response():
                answer = event.content.parts[0].text

    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").write(answer)
