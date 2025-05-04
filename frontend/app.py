import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from language import t, at, language_selector
from sqlalchemy import text

# ─── Page config & environment ─────────────────────────────────────────────────
load_dotenv(find_dotenv(), override=True)
st.set_page_config(page_title="Discharge Helper", layout="wide")

# ─── Backend endpoints ─────────────────────────────────────────────────────────
BASE_URL     = os.getenv("BACKEND_URL", "http://127.0.0.1:8001")
SIMPLIFY_URL = f"{BASE_URL}/simplify"
CHAT_URL     = f"{BASE_URL}/assistant/chat"
VALIDATE_URL = f"{BASE_URL}/validate"
TOFHIR_URL   = os.getenv("BACKEND_URL", "http://127.0.0.1:8001") + "/to_fhir"
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

# ─── Simplify function ────────────────────────────────────────────────────────
def do_simplify():
    txt = st.session_state["raw_text"].strip()
    lang = st.session_state["selected_language"]
    if not txt:
        st.warning(t("Please provide discharge instructions text before simplifying."))
        return
    with st.spinner(t("Simplifying...")):
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
            payload = { k: st.session_state[k] for k in [
                    "summary","instructions","importance",
                    "follow_up","medications","precautions","references"
            ] }
            patient_id = st.session_state.patient_id.strip()
            payload["patient_id"] = patient_id if patient_id else None
            payload["author_reference"] = FHIR_AUTHOR_REF
            try:
                to_fhir_resp = requests.post(TOFHIR_URL, json=payload, timeout=60)
                to_fhir_resp.raise_for_status()
                st.session_state.fhir_composition_str = json.dumps(
                    to_fhir_resp.json(), indent=2
                )
            except Exception as fhir_e:
                st.error(f"{t('FHIR conversion failed')}: {fhir_e}")
        except Exception as e:
            st.error(f"{t('Simplify error')}: {e}")
            st.session_state.update({
                "summary": "",
                "instructions": [],
                "importance": [],
                "follow_up": [],
                "medications": [],
                "precautions": [],
                "references": [],
                "disclaimer": "",
                "chat_history": [],
                "fhir_composition_str": None,
            })

# ─── Validators ───────────────────────────────────────────────────────────────
VALIDATE = lambda item: requests.post(
    VALIDATE_URL,
    json={"simplified_text": item, "original_text": st.session_state["raw_text"]},
    timeout=30
)

@st.dialog(t("Validate All"))
def validate_all(items, section_key=None):
    for item in items:
        res = VALIDATE(item)
        if res.status_code == 200:
            r = res.json()
            st.markdown(f"- **{t(item)}**")
            st.markdown(f"  {t('Match Found')}: {'✅' if r.get('is_valid') else '❌'}")
            explanation = r.get("explanation", "")
            st.markdown(f"  {t('Explanation')}: _{t(explanation)}_")
        else:
            st.markdown(f"- ❌ {t('Error validating')}: {item}")
            
# ─── Section renderers ───────────────────────────────────────────────────────      
def display_section(title, items, key, color="#f8f6ff"):
    if not items:
        return
    if st.button(t("Validate All"), key=f"validate_{key}"):
        validate_all(items)
    item_html = "".join(f"<li>{t(item)}</li>" for item in items)
    st.markdown(f"""
    <div style="
        background-color: {color};
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
    ">
        <h4 style="margin: 0;">{t(title)}</h4>
        <ul style="padding-left: 20px; margin-top: 10px;">{item_html}</ul>
    </div>
    """, unsafe_allow_html=True)

def render_cards(title: str, emoji: str, content, color: str, is_list: bool = False , key: str = None):
    if not content:
        return
    if st.button(t("Validate All"), key=f"validate_{key}"):
        validate_all([content] if not is_list else content)
    if is_list:
        body = "".join(f"<li>{t(item)}</li>" for item in content)
        html = f"<ul style='padding-left: 20px;'>{body}</ul>"
    else:
        html = f"<p>{t(content)}</p>"
    st.markdown(f"""
    <div style="
        background-color: {color};
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    ">
        <h4 style="margin-bottom: 10px;">{emoji} {t(title)}</h4>
        {html}
    </div>
    """, unsafe_allow_html=True)

# ─── Selection functions ────────────────────────────────────────────────────────
def input_method_selector():
    if st.session_state.input_method not in ("enter", "upload"):
        st.session_state.input_method = "enter"
    method = st.radio(
        label=t("Input method:"),
        options=["enter", "upload"],  
        index=0 if st.session_state.input_method == "enter" else 1,
        format_func=lambda v: (
            t("Enter text") if v == "enter"
            else t("Upload file")
        ),
        key="input_method",
        on_change=lambda: st.session_state.update({"file_uploaded": False}),
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

# ─── Header & language selector ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
col1.title(t("Discharge Instructions Simplifier & Assistant"))
with col2:
    st.markdown(f"**{t('Language')}**")
    language_selector()

# ─── Sidebar: Input & Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.header(t("Discharge Instructions Input"))
    #st.text_input(
    #    t("Patient ID (optional)"),
    #    value=st.session_state.get("patient_id", ""),
    #    key="patient_id",
    #    help=t("Optional FHIR Patient resource ID for Composition reference")
    #)
    input_method_selector()
    @st.dialog(t("View Original Content"))
    def open_content():
        st.text(st.session_state.raw_text)
    if st.button(t("View Original Content")):
        with st.expander(t("Original Content"), expanded=True):
            open_content()
    if st.button(t("Simplify")):
        do_simplify()

# ─── Main Output ─────────────────────────────────────────────────────────────
st.header(t("Simplified Output"))
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
      <h4>🗒️ {t("Summary")}</h4><p>{t(summary)}</p>
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
    if st.button(t("Validate"), key="validate_medications"):
        validate_all(meds_list,  "medications")
    if isinstance(medications, dict):
        html_take = ''.join(f"<li>{m}</li>" for m in medications['ToTake'])
        html_avoid = ''.join(f"<li>{m}</li>" for m in medications['ToAvoid'])
        st.markdown(f"""
        <div style="background-color:#fff5e6;padding:15px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:20px;">
          <h4>💊 {t("Medications")}</h4>
          <strong>{t("To Take")}:</strong>
          <ul style='padding-left:20px;'>{t(html_take)}</ul>
          <strong>{t("To Avoid")}:</strong>
          <ul style='padding-left:20px;'>{t(html_avoid)}</ul>
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
      <h4>⚠️ {t("Disclaimer")}</h4><p>{t(disclaimer)}</p>
    </div>
    """, unsafe_allow_html=True)
    
# 5) Assistant Chat
if instructions:
    st.markdown("---")
    st.header(t("Assistant Chat"))
    chatintro = f"""
        <div style="border: 1px solid #eee; padding: 10px; margin-bottom:10px;  border-radius: 8px; background-color: #f9f6ff;">
            💬 {t("Ask a question below and I’ll answer based on the instructions above.")}
        </div>
        """
    st.markdown(chatintro, unsafe_allow_html=True)
    col1, col2 = st.columns([7, 1])
    with col1:
        q = st.text_input(
            t("Ask a follow-up question:"),
            key="chat_input",
            label_visibility="collapsed",
            placeholder=t("Ask a follow-up question...")
        ) 
    with col2:
        if st.button(t("Send"), key="btn_chat") and q.strip():
            if q.strip():
                lang = st.session_state["selected_language"]
                if lang != "English":
                    qen = at(q, tarlang="English")
                else:
                    qen = q
                replyen = ""
                con = []
                if st.session_state["summary"]:
                    con.append(st.session_state["summary"])
                con += st.session_state["instructions"]
                con += st.session_state["importance"]
                con += st.session_state["follow_up"]
                meds = st.session_state["medications"]
                if isinstance(meds, dict):
                    con += meds.get("ToTake", []) + meds.get("ToAvoid", [])
                else:
                    con += meds
                con += st.session_state["precautions"]
                con += st.session_state["references"]
                try:
                    resp = requests.post(
                        CHAT_URL,
                        json={
                            "user_id":      "user1",
                            "user_message": qen,
                            "context":      con,
                        },
                        timeout=30
                    )
                    resp.raise_for_status()
                    replyen = resp.json().get("reply", "")
                except Exception as e:
                    st.error(f"{t('Chat error')}: {e}")
                if lang != "English":
                    replylocal = at(replyen, tarlang=lang)  
                else:
                    replylocal = replyen
                st.session_state["chat_history"].append((qen, replyen))

    lang = st.session_state["selected_language"]
    for quesen, ansen in st.session_state.get("chat_history", []):
        queslocal = t(quesen) if lang != "English" else quesen
        anslocal  = t(ansen)  if lang != "English" else ansen
        with st.chat_message("user"):
            st.markdown(queslocal)
        with st.chat_message("assistant"):
            st.markdown(anslocal)
