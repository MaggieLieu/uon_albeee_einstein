import streamlit as st
import os
from uon_agent_albeee.agent import root_agent

# --- 1. CONFIG & SECURITY ---
st.set_page_config(page_title="Albeee Einstein - UoN", page_icon="⚛️")

# Use st.secrets for the API Key (Secure!)
# This prevents the key from being hardcoded in your agent.py
os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]

st.title("Albeee Einstein: UoN Ambassador")
st.write("Ask me anything about Physics at Nottingham!")

# --- 2. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 3. CHAT INPUT ---
if prompt := st.chat_input("Guten Tag! What would you like to know about the University of Nottingham and the School of Physics and Astronomy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Calling the agent from your student's agent.py
        response = root_agent.run(prompt)
        full_text = response.text
        
        st.markdown(full_text)
        st.session_state.messages.append({"role": "assistant", "content": full_text})

        # --- 4. THE TALKING HEAD (Piper) ---
        # When you're ready to integrate the voice:
        # audio_path = generate_piper_audio(full_text) 
        # st.audio(audio_path, autoplay=True)
