import os
import requests
import pycountry
import json
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# ─── Page config & environment ─────────────────────────────────────────────────
st.set_page_config(page_title="Discharge Helper", layout="wide")
load_dotenv(find_dotenv(), override=True)

# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://localhost:8000")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"
VALIDATE_URL = f"{BASE_URL}/validate"
TOFHIR_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/to_fhir"
FHIR_AUTHOR_REF = os.getenv("FHIR_AUTHOR_REF", "Device/DischargeSimplify")

# ─── Full language list ─────────────────────────────────────────────────────────
languages = sorted([lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")])

# ─── Streamlit components ────────────────────────────────────────────────────
@st.dialog("View Original Content")
def open_content(text_input: str, file_content: str):
     st.markdown("### Original Content")
     if text_input:
         st.markdown(f"**Text Input:**\n{text_input}")
     if file_content:
         st.markdown(f"**File Content:**\n{file_content}")
         
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
        "selected_language": "English",
        "patient_id": "", 
        "fhir_composition_str": None, 
    })

# ─── Simplify function ────────────────────────────────────────────────────────
def do_simplify():
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
        st.session_state.update({
            "summary":      d.get("summary", ""),
            "instructions": d.get("instructions", []),
            "importance":   d.get("importance", []),
            "follow_up":    d.get("follow_up", []),
            "medications":  d.get("medications", []),
            "precautions":  d.get("precautions", []),
            "references":   d.get("references", []),
            "disclaimer":   d.get("disclaimer", ""),
            "chat_history": [],
            "fhir_composition_str": None, 
        })
         # ── AUTOMATIC FHIR CONVERSION ────────────────────────────────────
        if st.session_state.patient_id:
            payload = { k: st.session_state[k] for k in [
                "summary","instructions","importance",
                "follow_up","medications","precautions","references","disclaimer"
            ] }
            payload["patient_id"] = st.session_state.patient_id
            payload["author_reference"] = FHIR_AUTHOR_REF
            try:
                to_fhir_resp = requests.post(TOFHIR_URL, json=payload, timeout=60)
                to_fhir_resp.raise_for_status()
                st.session_state.fhir_composition_str = json.dumps(
                    to_fhir_resp.json(), indent=2
                )
            except Exception as fhir_e:
                st.error(f"{'FHIR conversion failed'}: {fhir_e}")
        # ────────────────────────────────────────────────────────────────────
    except Exception as e:
        st.error(f"Simplify error: {e}")

# ─── Header & language selector ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title("Discharge Instructions Simplifier & Assistant")
with col2:
    st.markdown("**Language**")
    st.selectbox(
        label="Select language:",
        options=languages,
        key="selected_language",
        on_change=do_simplify,
        label_visibility="collapsed"
    )

# ─── Sidebar: Input & Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Discharge Instructions Input")
    st.text_input(
        "Patient ID",
        value=st.session_state.get("patient_id", ""),
        key="patient_id",
        help="Enter the FHIR Patient resource ID to reference in the Composition"
    )
    method = st.radio("Input method:", ("Enter text", "Upload file"))
    if method == "Enter text":
        st.text_area(
            "Paste or edit here:",
            value=st.session_state["raw_text"],
            key="raw_text",
            height=200
        )
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
if st.session_state.get("summary"):
    st.subheader("Summary")
    st.write(st.session_state["summary"])

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


display_section("Instructions", st.session_state["instructions"], "instructions")
display_section("Importance", st.session_state["importance"], "importance")
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
    q = st.text_input("Ask a follow-up question:", key="chat_input")
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
        st.markdown(f"**You:** {ques}")
        st.markdown(f"**Assistant:** {ans}")