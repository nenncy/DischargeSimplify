import os
import requests
import pycountry
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import text

# ─── Page config & environment ─────────────────────────────────────────────────
st.set_page_config(page_title="Discharge Helper", layout="wide" )

load_dotenv(find_dotenv(), override=True)



# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"
VALIDATE_URL = f"{BASE_URL}/validate"

# ─── Full language list ─────────────────────────────────────────────────────────
languages = sorted([lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")])



# ─── Streamlit components ────────────────────────────────────────────────────
@st.dialog("View Original Content")
def open_content(text_input: str, file_content: str):
     content_to_show = text_input if text_input else file_content
     st.markdown("### Original Content")
    #  if text_input:
     st.markdown(f"**Input:**\n{content_to_show}")
    #  if file_content:
    #      st.markdown(f"**File Content:**\n{file_content}")
         
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
    if st.session_state["file_content"]:
        txt = st.session_state["file_content"].strip()
    else:
        txt = st.session_state["raw_text"].strip()
    lang = st.session_state["selected_language"]
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
        # print("🔍 Simplify response:", d)
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

# ─── Header & language selector ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title("Discharge Instructions Simplifier & Assistant")
with col2:
    st.markdown("**Language**")
    st.selectbox(
        "Select a language",  
        options=languages,
        key="selected_language",
        on_change=do_simplify,
        label_visibility="collapsed"
    )

# ─── Sidebar: Input & Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Discharge Instructions Input")
    method = st.radio("Input method:", ("Enter text", "Upload file"))
    st.session_state["input_method"] = method 
    if method == "Enter text":
        st.text_area(
            "Paste or edit here:",
            value=st.session_state["raw_text"],
            key="raw_text",
            height=200
        )
        # st.session_state["raw"] = st.session_state["raw_text"].strip()
        st.session_state["file_content"] = ""
    else:
        uploaded = st.file_uploader(
            "Choose .txt or .json:",
            type=["txt", "json"]
        )
        if uploaded:
            content = uploaded.read().decode("utf-8")
            st.session_state["raw_text"] = content
            st.session_state["file_content"] = content
    
    if st.button("View Original Content"):
         open_content(st.session_state["raw_text"], st.session_state["file_content"])
    if st.button("Simplify"):
        do_simplify()

# ─── Main: Simplified Output ──────────────────────────────────────────────────
st.header("Simplified Output")
# if st.session_state.get("summary"):
#     st.subheader("Summary")
#     st.write(st.session_state["summary"])

# print("🔍 Instructions:", st.session_state["raw"])
VALIDATE = lambda item: requests.post(
    VALIDATE_URL,
    json={"simplified_text": item, "original_text": st.session_state["raw_text"]},
    timeout=30
)

# ─── Validation function ────────────────────────────────────────────────────
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

def display_section(title, items, key):
    if not items:
        return
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader(title)
    with col2:
        if st.button("Validate All", key=f"validate_{key}"):
            validate_all(items, key)
    for itm in items:
        st.markdown(f"- {itm}")



# ─── Render cards ────────────────────────────────────────────────────────────
def render_cards(title: str, emoji: str, content, color: str, is_list: bool = False):
    if not content:
        return

    body = (
        "".join(f"<li>{item}</li>" for item in content)
        if is_list else f"<p>{content}</p>"
    )

    st.markdown(f"""
    <div style="
        background-color: {color};
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 100%;  /* 👈 Dynamic fill */
    ">
        <h4 style="margin-bottom: 10px;">{emoji} {title}</h4>
        {'<ul style="padding-left: 20px;">' + body + '</ul>' if is_list else body}
    </div>
    """, unsafe_allow_html=True)

summary = st.session_state.get("summary", "")
instructions = st.session_state.get("instructions", [])
importance = st.session_state.get("importance", [])

col1, col2, col3 = st.columns(3)
with col1:
    with st.container():
        render_cards("Summary", "🗒️", summary, "#f8f6ff", is_list=False)
with col2:
    with st.container():
        render_cards("Instructions", "📝", instructions, "#eef4ff", is_list=True)
with col3:
    with st.container():
        render_cards("Importance", "⚠️", importance, "#fff5e6", is_list=True)


# display_section("Instructions", st.session_state["instructions"], "instructions")
# display_section("Importance", st.session_state["importance"], "importance")
display_section("Follow-Up Tasks", st.session_state["follow_up"], "follow_up")
display_section("Medications", st.session_state["medications"], "medications")
display_section("Precautions", st.session_state["precautions"], "precautions")
display_section("References", st.session_state["references"], "references")

if st.session_state.get("disclaimer"):
    st.subheader("Disclaimer")
    st.write(st.session_state["disclaimer"])


# ─── Chat Assistant ───────────────────────────────────────────────────────────
if st.session_state.get("instructions"):
    st.markdown("---")
    st.header("Assistant Chat")
    st.markdown("""
<div style="border: 1px solid #eee; padding: 10px; margin-bottom:10px;  border-radius: 8px; background-color: #f9f6ff;">
<b>💬 Assistant Chat</b><br>
Ask your question in the box below, and the assistant will respond based on your discharge instructions.
</div>
""", unsafe_allow_html=True)

    
    # Input row layout
    col1, col2 = st.columns([7, 1])
    with col1:
        q = st.text_input(
            "Ask a follow-up question:",
            key="chat_input",
            label_visibility="collapsed",
            placeholder="Ask a follow-up question..."
        )
    with col2:
        # st.markdown("##")  # Align button
        if st.button("Send", key="btn_chat"):
            if q.strip():
                try:
                    resp = requests.post(
                        CHAT_URL,
                        json={
                            "user_id": "user1",
                            "user_message": q,
                            "context": st.session_state["instructions"]
                        },
                        timeout=30
                    )
                    resp.raise_for_status()
                    reply = resp.json().get("reply", "")
                    st.session_state["chat_history"].append((q, reply))
                except Exception as e:
                    st.error(f"Chat error: {e}")

   
    for ques, ans in st.session_state.get("chat_history", []):
        with st.chat_message("user"):
            st.markdown(ques)
        with st.chat_message("assistant"):
            st.markdown(ans)

#  if st.session_state.get("instructions"):
#     st.markdown("---")
#     st.header("Assistant Chat")
#     col1, col2 = st.columns([5, 1])
#     with col1:
#         q = st.text_input("Ask a follow-up question:", key="chat_input", label_visibility="collapsed" ,  placeholder="Ask a follow-up question...")
#     with col2:
#         st.markdown("##")
#         if st.button("Send", key="btn_chat"):
#             if q.strip():
#                 try:
#                     resp = requests.post(
#                         CHAT_URL,
#                         json={
#                             "user_id": "user1",
#                             "user_message": q,
#                             "context": st.session_state["instructions"]
#                         },
#                         timeout=30
#                     )
#                     resp.raise_for_status()
#                     reply = resp.json().get("reply", "")
#                     st.session_state["chat_history"].append((q, reply))
#                 except Exception as e:
#                     st.error(f"Chat error: {e}")
#         for ques, ans in st.session_state.get("chat_history", []):
#             with st.chat_message("user"):
#                 st.markdown(ques)
#             with st.chat_message("assistant"):
#                 st.markdown(ans)
#             # st.markdown(f"**You:** {ques}")
#             # st.markdown(f"**Assistant:** {ans}")