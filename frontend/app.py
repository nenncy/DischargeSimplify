import os
import requests
import pycountry
import streamlit as st
from dotenv import load_dotenv

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Discharge Helper", layout="wide")
load_dotenv()

# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://localhost:8000")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"

# ─── Language list ─────────────────────────────────────────────────────────────
languages = sorted([lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")])

# ─── Session state init ───────────────────────────────────────────────────────
if "raw_text" not in st.session_state:
    st.session_state.update({
        "raw_text":          "",
        "summary":           "",
        "instructions":      [],
        "importance":        [],
        "follow_up":         [],
        "medications":       [],
        "precautions":       [],
        "references":        [],
        "disclaimer":        "",
        "chat_history":      [],
        "selected_language": "English",
    })

# ─── Simplify function ────────────────────────────────────────────────────────
def do_simplify():
    txt  = st.session_state["raw_text"].strip()
    lang = st.session_state["selected_language"]
    st.write("📢 Will simplify into:", lang)
    if not txt:
        return
    try:
        res = requests.post(
            SIMPLIFY_URL,
            json={"raw_text": txt, "language": lang},
            timeout=60
        )
        res.raise_for_status()
        d = res.json()
        st.session_state.update({
            "summary":      d.get("summary", ""),
            "instructions": d.get("instructions", []),
            "importance":   d.get("importance", []),
            "follow_up":    d.get("follow_up", []),
            "medications":  d.get("medications", []),
            "precautions":  d.get("precautions", []),
            "references":   d.get("references", []),
            "disclaimer":   d.get("disclaimer", ""),
            "chat_history": []
        })
    except Exception as e:
        st.error(f"Simplify error: {e}")

# ─── Top bar ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title("Discharge Instructions Simplifier & Assistant")
col2.selectbox(
    "Choose Language:",
    options=languages,
    key="selected_language",
    on_change=do_simplify
)

# ─── Sidebar: Input + Simplify ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Input Discharge Instructions")

    # --- REVISED: trigger simplify on every edit ---
    st.text_area(
        "Paste or edit text below:",
        value=st.session_state["raw_text"],
        key="raw_text",
        height=200,
        on_change=do_simplify
    )

    # --- REVISED: use a key and on_change for file uploads ---
    uploaded = st.file_uploader(
        "Or upload a .txt/.json file:",
        type=["txt", "json"],
        key="upload",
        on_change=do_simplify
    )
    if uploaded:
        # load it into raw_text (so do_simplify sees it)
        st.session_state["raw_text"] = uploaded.read().decode("utf-8")
        st.sidebar.success(f"Loaded file: {uploaded.name}")

    # manual fallback (optional)
    if st.button("Simplify"):
        do_simplify()

# ─── Main: Simplified Output ─────────────────────────────────────────────────
st.header("Simplified Output")

if st.session_state["summary"]:
    st.subheader("Summary")
    st.write(st.session_state["summary"])

def display_section(title, items):
    if items:
        st.subheader(title)
        for itm in items:
            st.markdown(f"- {itm}")

display_section("Instructions",    st.session_state["instructions"])
display_section("Importance",      st.session_state["importance"])
display_section("Follow-Up Tasks", st.session_state["follow_up"])
display_section("Medications",     st.session_state["medications"])
display_section("Precautions",     st.session_state["precautions"])
display_section("References",      st.session_state["references"])

if st.session_state["disclaimer"]:
    st.subheader("Disclaimer")
    st.write(st.session_state["disclaimer"])

# ─── Chat panel ───────────────────────────────────────────────────────────────
if st.session_state["instructions"]:
    st.markdown("---")
    st.header("Assistant Chat")
    q = st.text_input("Ask follow-up questions:", key="chat_input")
    if st.button("Send", key="btn_chat"):
        if q.strip():
            try:
                chat_resp = requests.post(
                    CHAT_URL,
                    json={
                        "user_id":      "user1",
                        "user_message": q,
                        "context":      st.session_state["instructions"]
                    },
                    timeout=30
                )
                chat_resp.raise_for_status()
                reply = chat_resp.json().get("reply", "")
                st.session_state["chat_history"].append((q, reply))
            except Exception as e:
                st.error(f"Chat error: {e}")
    for ques, ans in st.session_state["chat_history"]:
        st.markdown(f"**You:** {ques}")
        st.markdown(f"**Assistant:** {ans}")