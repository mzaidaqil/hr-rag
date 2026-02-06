import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.title("HR RAG Assistant (Phase 1)")

api_base = os.environ.get("HR_RAG_API_BASE", "http://localhost:8000")
user_id = st.sidebar.text_input("user_id", value="demo-user")
region = st.sidebar.text_input("region", value="US")

if "history" not in st.session_state:
    st.session_state.history = []

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

prompt = st.chat_input("Ask an HR policy question, or say: update my address")
if prompt:
    st.session_state.history.append(("user", prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        r = requests.post(
            f"{api_base}/chat",
            json={"user_id": user_id, "text": prompt, "region": region or None},
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        answer = data.get("text", "")
    except Exception as e:
        answer = f"API error: {e}"

    st.session_state.history.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)

