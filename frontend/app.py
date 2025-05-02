import os
import requests
import pycountry
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text

# ─── Page config & environment ─────────────────────────────────────────────────
st.set_page_config(page_title="Discharge Helper", layout="wide")
load_dotenv(find_dotenv(), override=True)

# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"
VALIDATE_URL = f"{BASE_URL}/validate"

# ─── Full language list ─────────────────────────────────────────────────────────
languages = sorted([lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")])

# ─── Streamlit components ────────────────────────────────────────────────────
@st.dialog("View Original Content")
def open_content(text_input: str, file_content: str):
    content_to_show = text_input or file_content
    st.markdown("### Original Content")
    st.markdown(f"**Input:**\n{content_to_show}")

# ─── Session state init ───────────────────────────────────────────────────────
if "raw_text" not in st.session_state:
    st.session_state.update({
        "raw_text":          "",
        "file_content":      "",
        "summary":           "",
        "instructions":      [],
        "importance":        [],
        "follow_up":         [],
        "medications":       [],
        "precautions":       [],
        "references":        [],
        "disclaimer":        "",
        "chat_history":      [],
        "selected_language": "English"
    })

# ─── Simplify function ────────────────────────────────────────────────────────
def do_simplify():
    txt = (st.session_state["file_content"] or st.session_state["raw_text"]).strip()
    lang = st.session_state["selected_language"]
    if not txt:
        return
    with st.spinner("Simplifying..."):
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

# ─── Validators ───────────────────────────────────────────────────────────────
VALIDATE = lambda item: requests.post(
    VALIDATE_URL,
    json={"simplified_text": item, "original_text": st.session_state["raw_text"]},
    timeout=30
)

@st.dialog("Validate All")
def validate_all(items, key):
    for item in items:
        res = VALIDATE(item)
        if res.status_code == 200:
            r = res.json()
            st.markdown(f"- **{item}**")
            st.markdown(f"  Match Found: {'✅' if r.get('is_valid') else '❌'}")
            st.markdown(f"  Explanation: _{r.get('explanation','')}_")
        else:
            st.markdown(f"- ❌ Error validating: {item}")

# ─── Section renderers ───────────────────────────────────────────────────────
def display_section(title, items, key, color="#f8f6ff"):
    if not items:
        return
    if st.button("Validate", key=f"validate_{key}"):
        validate_all(items, key)
    item_html = ''.join(f"<li>{itm}</li>" for itm in items)
    st.markdown(f"""
    <div style="background-color:{color};padding:20px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:20px;">
      <h4 style="margin:0">{title}</h4>
      <ul style="padding-left:20px;margin-top:10px;">{item_html}</ul>
    </div>
    """, unsafe_allow_html=True)

def render_cards(title, emoji, content, color, is_list=False, key=None):
    if not content:
        return
    if st.button("Validate", key=f"validate_{key}"):
        validate_all(content, key)
    if is_list:
        body = ''.join(f"<li>{i}</li>" for i in content)
        html = f"<ul style='padding-left:20px;'>{body}</ul>"
    else:
        html = f"<p>{content}</p>"
    st.markdown(f"""
    <div style="background-color:{color};padding:15px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:20px;">
      <h4 style="margin-bottom:10px;">{emoji} {title}</h4>
      {html}
    </div>
    """, unsafe_allow_html=True)

# ─── Layout & controls ───────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title("Discharge Instructions Simplifier & Assistant")
with col2:
    st.markdown("**Language**")
    st.selectbox("Select a language", options=languages, key="selected_language", on_change=do_simplify,
                 label_visibility="collapsed")

with st.sidebar:
    st.header("Discharge Instructions Input")
    method = st.radio("Input method:", ("Enter text", "Upload file"))
    st.session_state["input_method"] = method
    if method == "Enter text":
        st.text_area("Paste or edit here:", value=st.session_state["raw_text"], key="raw_text", height=200)
        st.session_state["file_content"] = ""
    else:
        up = st.file_uploader("Choose .txt or .json:", type=["txt", "json"])
        if up:
            c = up.read().decode("utf-8")
            st.session_state["raw_text"] = c
            st.session_state["file_content"] = c
    if st.button("View Original Content"):
        open_content(st.session_state["raw_text"], st.session_state["file_content"])
    if st.button("Simplify"):
        do_simplify()

# ─── Main Output ─────────────────────────────────────────────────────────────
st.header("Simplified Output")
summary      = st.session_state.get("summary", "")
instructions = st.session_state.get("instructions", [])
importance   = st.session_state.get("importance", [])
follow_up    = st.session_state.get("follow_up", [])
medications  = st.session_state.get("medications", [])
precautions  = st.session_state.get("precautions", [])
references   = st.session_state.get("references", [])
disclaimer   = st.session_state.get("disclaimer", "")

# 1) Summary (purple)
if summary:
    st.markdown(f"""
    <div style="background-color:#f8f6ff;padding:15px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:20px;">
      <h4>🗒️ Summary</h4><p>{summary}</p>
    </div>
    """, unsafe_allow_html=True)

# 2) Instructions, Importance, Follow-Up (blue, yellow, blue)
c1, c2, c3 = st.columns(3)
with c1:
    render_cards("Instructions", "📝", instructions, "#eef4ff", is_list=True, key="instruction")
with c2:
    render_cards("Importance", "⚠️", importance, "#fff5e6", is_list=True, key="importance")
with c3:
    display_section("Follow-Up Tasks", follow_up, "follow_up", color="#eef4ff")

# 3) Medications combined (yellow)
c1, c2, c3 = st.columns(3)
with c1:
    # Combine ToTake and ToAvoid into one list for validation
    meds_list = medications.get('ToTake', []) + medications.get('ToAvoid', []) if isinstance(medications, dict) else medications
    if st.button("Validate", key="validate_medications"):
        validate_all(meds_list, "medications")
    if isinstance(medications, dict):
        html_take = ''.join(f"<li>{m}</li>" for m in medications['ToTake'])
        html_avoid = ''.join(f"<li>{m}</li>" for m in medications['ToAvoid'])
        st.markdown(f"""
        <div style="background-color:#fff5e6;padding:15px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:20px;">
          <h4>💊 Medications</h4>
          <strong>To Take:</strong>
          <ul style='padding-left:20px;'>{html_take}</ul>
          <strong>To Avoid:</strong>
          <ul style='padding-left:20px;'>{html_avoid}</ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        display_section("Medications", medications, "medications", color="#fff5e6")
with c2:
    display_section("Precautions", precautions, "precautions", color="#eef4ff")
with c3:
    display_section("References", references, "references", color="#fff5e6")

# 4) Disclaimer (purple)
if disclaimer:
    st.markdown(f"""
    <div style="background-color:#f8f6ff;padding:15px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-top:20px;">
      <h4>⚠️ Disclaimer</h4><p>{disclaimer}</p>
    </div>
    """, unsafe_allow_html=True)

# 5) Assistant Chat
if instructions:
    st.markdown("---")
    st.header("Assistant Chat")
    st.markdown("""
      <div style="border:1px solid #eee;padding:10px;margin-bottom:10px;border-radius:8px;background-color:#f9f6ff;">
      💬 Ask a question below and I’ll answer based on the instructions above.
      </div>
    """, unsafe_allow_html=True)

    # on_change callback instead of separate button
    def submit_chat():
        q = st.session_state.chat_input.strip()
        if not q:
            return
        try:
            r = requests.post(
                CHAT_URL,
                json={"user_id":"user1","user_message":q,"context":instructions},
                timeout=30
            )
            r.raise_for_status()
            st.session_state["chat_history"].append((q, r.json().get("reply", "")))
        except Exception as e:
            st.error(f"Chat error: {e}")
        st.session_state.chat_input = ""

    st.text_input(
        "Ask a follow-up question:",
        key="chat_input",
        label_visibility="collapsed",
        placeholder="Ask a follow-up question...",
        on_change=submit_chat
    )

    for uq, ans in st.session_state.get("chat_history", []):
        with st.chat_message("user"):
            st.markdown(uq)
        with st.chat_message("assistant"):
            st.markdown(ans)