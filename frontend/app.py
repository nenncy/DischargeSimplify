import streamlit as st
import requests
import os
import pycountry
import re
import datetime
import locale
import json
import pandas as pd
from googletrans import Translator

translator = Translator()

# ensure our UI‐language settings persist across all reruns  
if "ui_language_name" not in st.session_state:  
    st.session_state["ui_language_name"] = "English"  
if "ui_language_code" not in st.session_state:  
    st.session_state["ui_language_code"] = "en"  

def tlabel(s: str) -> str:
    lang_code = st.session_state.get("ui_language_code", "en")
    if lang_code == "en":
        return s
    try:
        return translator.translate(s, src="en", dest=lang_code).text
    except Exception:
        return s

# Initialize session state for simplify plus chat
if "instructions" not in st.session_state:
    st.session_state.update({
        "concise_summary": "",
        "instructions": [],
        "importance": [],
        "follow_up": [],
        "medications": [],
        "precautions": [],
        "references": [],
        "chat_history": [],
        "cached_sections": {},
        "symptoms": [],
        "feedback_log": [],
        "run_summary": False
    })

# Language options
all_langs = [(lang.name, lang.alpha_2) for lang in pycountry.languages if hasattr(lang, "alpha_2")]
all_langs.sort(key=lambda x: x[0])

BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SIMPLIFY_URL = BASE_URL + "/simplify"
CHAT_URL = BASE_URL + "/assistant/chat"

# Sidebar for settings & input
with st.sidebar:
    st.header(tlabel("Settings & Input")) 
    # font size
    fontsize = st.sidebar.slider(label=tlabel("Font size"),min_value=12, max_value=24, value=16, key="fontsize_slider")
    st.markdown(f""" <style> /* Apply font size to all main-area elements */ .stApp, .stApp * {{font-size: {fontsize}px !important;}}
        /* Override primary title (h1) back to a fixed larger size */ .stApp h1 {{font-size: 2.5em !important;}}
        /* Override section headers (h2, h3) to scale relative to base */ .stApp h2 {{ font-size: 1.8em !important; }} .stApp h3 {{ font-size: 1.4em !important; }}
        </style> """, unsafe_allow_html=True)
    # reading level
    reading_level = st.sidebar.slider(label=tlabel("Target Reading Level (US Grade)"),min_value=3, max_value=12, value=6, key="reading_level_slider")
    names = [name for name, code in all_langs] 
    lang_map = {n: c for n, c in all_langs} 
    idx = names.index(st.session_state["ui_language_name"]) if st.session_state["ui_language_name"] in names else 0  
    st.selectbox(label=tlabel("Choose Language:"), options=names, index=idx, key="ui_language_name", 
        on_change=lambda: st.session_state.__setitem__(  
            "ui_language_code", lang_map[st.session_state["ui_language_name"]]  
        )  
    )
    METHOD_DISPLAY = {
        "enter_text":  "Enter Text",
        "upload_file": "Upload File",
    }
    method = st.sidebar.radio(label=tlabel("Input Method:"),options = list(METHOD_DISPLAY.keys()), format_func = lambda code: tlabel(METHOD_DISPLAY[code]), key="input_method")
    text_input = ""
    file_content = ""
    if method == "enter_text":
        text_input = st.text_area(tlabel("Paste Discharge Instruction:"), key="text_input")
    else:
        uploaded = st.file_uploader(tlabel("Upload .txt, .json or .pdf file"), type=["txt","json","pdf"], key="file_uploader")
        if uploaded:
            file_content = uploaded.read().decode("utf-8")
            st.write(f"{tlabel('Uploaded')}: {uploaded.name}") 

    if st.button(tlabel("Simplify"), key="simplify_button"):
        payload = text_input if method == "Enter Text" else file_content
        if not payload.strip():
            st.sidebar.warning(tlabel("Please enter text or upload a file."))
        else:
            with st.spinner(tlabel("Simplifying…")):
                try:
                    res = requests.post(SIMPLIFY_URL, json={"raw_text": payload, "language": st.session_state["ui_language_name"], "reading_level": reading_level})
                    res.raise_for_status()
                    data = res.json()
                    st.session_state["raw_text"] = payload
                    st.session_state["concise_summary"] = data.get("concise_summary", "")
                    st.session_state["instructions"] = data.get("instructions", [])
                    st.session_state["importance"]   = data.get("importance", [])
                    st.session_state["follow_up"]    = data.get("follow_up", [])
                    st.session_state["medications"]  = data.get("medications", [])
                    st.session_state["precautions"]  = data.get("precautions", [])
                    st.session_state["references"]   = data.get("references", [])
                    st.session_state["sections"]   = data.get("sections", [])
                    st.session_state.run_summary = True
                    # reset chat history when new summary uploaded
                    st.session_state["chat_history"] = []
                except Exception as e:
                    st.sidebar.error(tlabel("Error: ") + str(e))

# Main area for simplified output
st.title(tlabel("Discharge Instructions Simplifier & Assistant"))

if st.session_state.run_summary and st.session_state.concise_summary:
    st.header(tlabel("Discharge Summary"))
    st.markdown(st.session_state["concise_summary"])
    
st.header(tlabel("Simplified Output"))

def display_section(title, items):
    if items:
        st.subheader(tlabel(title))
        for item in items:
            st.markdown(f"- {tlabel(item)}")
if st.session_state.run_summary:
    display_section("Instructions", st.session_state["instructions"] )
    display_section("Importance",   st.session_state["importance"]   )
    display_section("Follow-Up Tasks",st.session_state["follow_up"]    )
    display_section("Medications",    st.session_state["medications"]  )
    display_section("Precautions",    st.session_state["precautions"]  )
    display_section("References",     st.session_state["references"]   )

    # medication checklist
    if st.session_state["medications"]:
        st.subheader(tlabel("Medication Checklist & Reminders"))
        for med in st.session_state["medications"]:
            st.checkbox(tlabel(med), key=f"med_{med}")
            
    # symptom tracker
    st.subheader(tlabel("Symptom Tracker"))
    # auto-detect sample symptoms
    allSymptoms = ["pain", "swelling", "fever", "nausea", "vomiting", "headache", "dizziness", "fatigue",
        "shortness of breath", "cough", "chills", "sore throat", "congestion", "runny nose", "sneezing",
        "abdominal pain", "diarrhea", "constipation", "bloating", "cramps", "gas", "indigestion",
        "chest pain", "palpitations", "irregular heartbeat", "high blood pressure", "low blood pressure",
        "back pain", "joint pain", "muscle aches", "stiffness", "tremors", "numbness", "tingling",
        "rash", "itching", "bruising", "bleeding", "skin discoloration", "sensitivity to light",
        "sensitivity to sound", "loss of taste", "loss of smell", "dry mouth", "mouth ulcers",
        "difficulty swallowing", "hoarseness", "ear pain", "hearing loss", "tinnitus",
        "blurred vision", "double vision", "eye pain", "red eyes", "watery eyes", "yellowing of skin",
        "weight loss", "weight gain", "loss of appetite", "increased appetite", "thirst",
        "urinary frequency", "burning with urination", "incontinence", "urine discoloration",
        "difficulty urinating", "sexual dysfunction", "menstrual irregularities", "hot flashes",
        "night sweats", "anxiety", "depression", "confusion", "memory loss", "hallucinations",
        "insomnia", "agitation", "irritability", "restlessness", "slurred speech", "balance problems",
        "coordination problems", "fainting", "seizures", "numbness", "tingling", "paralysis",
        "cold extremities", "cyanosis", "shaking", "clumsiness", "vision loss",
        "blurred speech", "visual hallucinations", "auditory hallucinations", "muscle weakness",
        "facial drooping", "gait instability", "vertigo", "delayed reflexes", "loss of coordination",
        "memory lapses", "trouble concentrating", "brain fog", "numbness on one side of body",
        "orthopnea", "paroxysmal nocturnal dyspnea", "wheezing", "hemoptysis",
        "cold intolerance", "heat intolerance", "dry skin", "brittle nails", "hair thinning",
        "excessive sweating", "frequent infections", "slow wound healing", "polyuria", "polydipsia",
        "polyphagia", "mood swings", "panic attacks", "intrusive thoughts", "paranoia", "hopelessness",
        "suicidal thoughts", "compulsive behavior", "phobias", "muscle cramps",
        "joint stiffness in the morning", "limited range of motion", "weakness after exertion",
        "bone pain", "foot drop", "easy bruising", "recurrent nosebleeds", "petechiae",
        "swollen lymph nodes", "autoimmune flares", "malaise", "night pain", "sudden weight changes",
        "skin sensitivity", "change in body odor", "pale skin", "general weakness", "intolerance to exercise",
        "hot flashes", "cold flashes"]
    raw = st.session_state.get("raw_text", "")
    found = [
        s for s in allSymptoms
        if re.search(rf"\b{re.escape(s.lower())}\b", raw.lower())
    ]    
    selected = st.multiselect(
        tlabel("Select symptoms to log"),
        options=found,
        default=found
    )
    d = st.date_input(tlabel("Date"), datetime.date.today())
    levels = {
        sym: st.slider(
            tlabel(f"{sym} level"),
            0, 10, 0,
            key=f"lvl_{sym}"
        )
        for sym in selected
    }
    if st.button(tlabel("Log Symptoms")):
        entry = {"date": str(d), **levels}
        st.session_state.symptoms.append(entry)
    if st.session_state.symptoms:
        st.dataframe(pd.DataFrame(st.session_state.symptoms))

    # Chat panel appears once simplification has run
    if st.session_state["instructions"]:
        st.markdown("---")
        st.header(tlabel("Assistant Chat"))
        user_q = st.text_input(tlabel("Ask questions:"), key="chat_input")
        if st.button(tlabel("Send"), key="send_chat"):
            if not user_q.strip():
                st.warning(tlabel("Enter a question before sending."))
            else:
                with st.spinner(tlabel("Contacting assistant…")):
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

    # feedback
    st.subheader(tlabel("Send Feedback to Provider"))
    fb = st.text_area(tlabel("Your message"), key="feedback_msg")
    if st.button(tlabel("Send Message")):
        st.session_state.feedback_log.append(fb)
        st.success(tlabel("Feedback logged."))
        
    # export JSON & clear
    st.subheader(tlabel("Export All Data as JSON"))
    lang = st.session_state.get("ui_language_code", "en")
    def to_en(item):
        if not isinstance(item, str) or lang == "en":
            return item
        try:
            return translator.translate(item, src=lang, dest="en").text
        except Exception:
            return item
    def to_en_list(lst):
        return [to_en(x) for x in lst]
    export = {
        "Raw Text": to_en(text_input or file_content),
        "Discharge Summary": to_en(st.session_state.get("concise_summary", "")),
        "Categories": {
            "Instructions": to_en_list(st.session_state.get("instructions",[])),
            "Importance": to_en_list(st.session_state.get("importance", [])),
            "Follow-up": to_en_list(st.session_state.get("follow_up", [])),
            "Medications": to_en_list(st.session_state.get("medications", [])),
            "Precautions": to_en_list(st.session_state.get("precautions", [])),
            "References": to_en_list(st.session_state.get("references", [])),
        },
        "Symptoms": st.session_state.get("symptoms",[]),
        "Feedback": to_en_list(st.session_state.get("feedback_log",[])),
    }
    st.json(export)
    st.download_button(tlabel("Download JSON"), json.dumps(export, indent=2), file_name="data.json")