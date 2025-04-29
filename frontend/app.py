import os
import json
import requests
import pycountry
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# ─── Fix googletrans/httpcore compatibility ────────────────────────────────────
try:
    import httpcore
    if not hasattr(httpcore, 'SyncHTTPTransport'):
        class SyncHTTPTransport:
            pass
        httpcore.SyncHTTPTransport = SyncHTTPTransport
except ImportError:
    pass

from googletrans import Translator, LANGUAGES
translator = Translator()

# ─── Language Configuration ────────────────────────────────────────────────────
LANGUAGE_MAPPING = {name.title(): code for code, name in LANGUAGES.items()}
languages = sorted(LANGUAGE_MAPPING.keys())

# ─── Page config & environment ─────────────────────────────────────────────────
load_dotenv(find_dotenv(), override=True)

# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://localhost:8000")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"
VALIDATE_URL = f"{BASE_URL}/validate"
TOFHIR_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/to_fhir"
FHIR_AUTHOR_REF = os.getenv("FHIR_AUTHOR_REF", "Device/DischargeSimplify")

# ─── Session State Initialization ──────────────────────────────────────────────
session_defaults = {
    "selected_language": "English",
    "ui_language_code": "en",
    "translations": {},
    "raw_text": "",
    "input_method": "enter",
    "file_uploaded": False,
    "summary": "",
    "instructions": [],
    "importance": [],
    "follow_up": [],
    "medications": [],
    "precautions": [],
    "references": [],
    "disclaimer": "",
    "chat_history": [],
    "patient_id": "", 
    "fhir_composition_str": None, 
}

for key, val in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val
        
# ─── Translation System ────────────────────────────────────────────────────────
def t(s: str) -> str:
    if st.session_state.ui_language_code == "en":
        return s
    
    cache_key = (s, st.session_state.ui_language_code)
    if cache_key in st.session_state.translations:
        return st.session_state.translations[cache_key]
    
    try:
        translated = translator.translate(s, dest=st.session_state.ui_language_code).text
        st.session_state.translations[cache_key] = translated
        return translated
    except Exception:
        return s

# ─── Core Language Functions ────────────────────────────────────────────────────────────
def update_language():
    new_lang = st.session_state.selected_language
    st.session_state.ui_language_code = LANGUAGE_MAPPING.get(new_lang, "en")
    st.session_state.translations.clear()

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
            timeout=120
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
                st.error(f"{t('FHIR conversion failed')}: {fhir_e}")
        # ────────────────────────────────────────────────────────────────────

    except Exception as e:
        st.error(f"Simplify error: {e}")
        
# ─── Selection functions ────────────────────────────────────────────────────────
def language_selector():
    current_idx = languages.index(st.session_state.selected_language)
    st.selectbox(
        t("Language"),
        languages,
        index=current_idx,
        key="selected_language",
        on_change=update_language,
        label_visibility="collapsed"
    )

def input_method_selector():
    method = st.radio(
        t("Input method:"),
        ["enter", "upload"],
        index=0 if st.session_state.input_method == "enter" else 1,
        format_func=lambda v: t("Enter text") if v == "enter" else t("Upload file"),
        key="input_method",
        on_change=lambda: st.session_state.update({"file_uploaded": False})
    )
    
    if method == "enter":
        text_input_component()
    else:
        file_upload_component()

def text_input_component():
    new_text = st.text_area(
        t("Paste or edit here:"),
        value=st.session_state.raw_text,
        height=200,
        key="text_input_area"
    )
    if new_text != st.session_state.raw_text:
        st.session_state.raw_text = new_text
        do_simplify()

def file_upload_component():
    uploaded = st.file_uploader(
        t("Choose .txt or .json:"),
        type=["txt", "json"],
        key="file_uploader"
    )
    if uploaded is not None:
        text = uploaded.read().decode("utf-8")
        st.session_state.raw_text = text
        st.session_state.file_uploaded = True

    elif st.session_state.file_uploaded:
        st.info(t("Using previously uploaded content"))
        st.text_area(
            t("Uploaded content:"),
            value=st.session_state.raw_text,
            height=200,
            disabled=True   
        )

# ─── Page config (uses translation) ──────────────────────────────────────────
st.set_page_config(page_title=t("Discharge Helper"), layout="wide")

# ─── Header & language selector ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title(t("Discharge Instructions Simplifier & Assistant"))
with col2:
    st.markdown(f"**{t('Language')}**")
    language_selector()

# ─── Sidebar: Input & Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.header(t("Discharge Instructions Input"))
    st.text_input(
        t("Patient ID"),
        value=st.session_state.get("patient_id", ""),
        key="patient_id",
        help=t("Enter the FHIR Patient resource ID to reference in the Composition")
    )
    input_method_selector()

    if st.button(t("Simplify")):
        do_simplify()

    if st.button(t("View Original Content")):
        with st.expander(t("Original Content"), expanded=True):
            st.text(st.session_state.raw_text)

# ─── Main: Simplified Output ──────────────────────────────────────────────────
st.header(t("Simplified Output"))
if st.session_state.get("summary"):
    st.subheader(t("Summary"))
    st.write(t(st.session_state["summary"]))

# Validation helper
VALIDATE = lambda item: requests.post(
    VALIDATE_URL,
    json={"simplified_text": item, "original_text": st.session_state["raw_text"]},
    timeout=30
)

def display_section(title, items, key):
    if not items:
        return
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader(t(title))
    with col2:
        if st.button(t("Validate All"), key=f"validate_{key}"):
            with st.expander(t("Validation Report"), expanded=True):
                for item in items:
                    res = VALIDATE(item)
                    if res.status_code == 200:
                        r = res.json()
                        st.markdown(f"- **{item}**")
                        st.markdown(f"  {t('Match Found')}: {'✅' if r.get('is_valid') else '❌'}")
                        st.markdown(f"  {t('Explanation')}: _{r.get('explanation','')}_")
                    else:
                        st.markdown(f"- ❌ {t('Error validating')}: {item}")
    for itm in items:
        st.markdown(f"- {t(itm)}")

# Sections
display_section("Instructions", st.session_state["instructions"], "instructions")
display_section("Importance", st.session_state["importance"], "importance")
display_section("Follow-Up Tasks", st.session_state["follow_up"], "follow_up")
display_section("Medications", st.session_state["medications"], "medications")
display_section("Precautions", st.session_state["precautions"], "precautions")
display_section("References", st.session_state["references"], "references")

if st.session_state.get("disclaimer"):
    st.subheader(t("Disclaimer"))
    st.write(t(st.session_state["disclaimer"]))

# ─── Chat Assistant ───────────────────────────────────────────────────────────
if st.session_state.get("instructions"):
    st.markdown("---")
    st.header(t("Assistant Chat"))
    q = st.text_input(t("Ask a follow-up question:"), key="chat_input")
    if st.button(t("Send"), key="btn_chat"):        
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
        st.markdown(f"**{t('You')}:** {t(ques)}")
        st.markdown(f"**{t('Assistant')}:** {t(ans)}")