import streamlit as st
import requests
import os
import pycountry

# Initialize session state for simplify plus chat
if "instructions" not in st.session_state:
    st.session_state.update({
        "instructions": [],
        "importance": [],
        "follow_up": [],
        "medications": [],
        "precautions": [],
        "references": [],
        "chat_history": []
    })

# Language options
languages = sorted(
    {lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")}
)

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SIMPLIFY_URL = BASE_URL + "/simplify"
CHAT_URL = BASE_URL + "/assistant/chat"

st.title("Discharge Instructions Simplifier & Assistant")

# Sidebar for settings & input
with st.sidebar:
    st.header("Settings & Input")
    language = st.selectbox("Choose Language:", languages)
    method = st.radio("Input Method:", ("Enter Text", "Upload File"), label_visibility="visible")

    text_input = ""
    file_content = ""
    if method == "Enter Text":
        text_input = st.text_area("Paste Discharge Instruction:")
    else:
        uploaded = st.file_uploader("Upload .txt or .json file", type=["txt","json"])
        if uploaded:
            file_content = uploaded.read().decode("utf-8")
            st.write(f"Uploaded: {uploaded.name}")

    if st.button("Simplify"):
        payload = text_input if method == "Enter Text" else file_content
        if not payload.strip():
            st.sidebar.warning("Please enter text or upload a file.")
        else:
            with st.spinner("Simplifying…"):
                try:
                    res = requests.post(SIMPLIFY_URL, json={"raw_text": payload, "language": language})
                    res.raise_for_status()
                    data = res.json()
                    st.session_state["instructions"] = data.get("instructions", [])
                    st.session_state["importance"]   = data.get("importance", [])
                    st.session_state["follow_up"]    = data.get("follow_up", [])
                    st.session_state["medications"]  = data.get("medications", [])
                    st.session_state["precautions"]  = data.get("precautions", [])
                    st.session_state["references"]   = data.get("references", [])
                    # reset chat history when new summary uploaded
                    st.session_state["chat_history"] = []
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")

# Main area for simplified output
st.header("Simplified Output")

def display_section(title, items):
    if items:
        st.subheader(title)
        for item in items:
            st.markdown(f"- {item}")
display_section("Instructions", st.session_state["instructions"] )
display_section("Importance",   st.session_state["importance"]   )
display_section("Follow-Up Tasks",st.session_state["follow_up"]    )
display_section("Medications",    st.session_state["medications"]  )
display_section("Precautions",    st.session_state["precautions"]  )
display_section("References",     st.session_state["references"]   )

# Chat panel appears once simplification has run
if st.session_state["instructions"]:
    st.markdown("---")
    st.header("Assistant Chat")
    user_q = st.text_input("Ask questions:", key="chat_input")
    if st.button("Send", key="send_chat"):
        if not user_q.strip():
            st.warning("Enter a question before sending.")
        else:
            with st.spinner("Contacting assistant…"):
                try:
                    res = requests.post(CHAT_URL, json={"user_id":"user1","message":user_q, "context": st.session_state["instructions"]})
                    res.raise_for_status()
                    reply = res.json().get("reply", "")
                    st.session_state["chat_history"].append(("You", user_q))
                    st.session_state["chat_history"].append(("Assistant", reply))
                except Exception as e:
                    st.error(f"Chat error: {e}")
    for speaker, msg in st.session_state["chat_history"]:
        prefix = "**You:**" if speaker=="You" else "**Assistant:**"
        st.markdown(f"{prefix} {msg}")
