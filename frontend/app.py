import streamlit as st
import requests
import os
import pycountry

# Initialize session state
if "summary" not in st.session_state:
    st.session_state["summary"] = ""
    st.session_state["precautions"] = []
    st.session_state["medications"] = []

# Build a sorted list of ISO‑639 language names
languages = sorted(
    {lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")}
)

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/simplify"

st.title("Discharge Instructions Simplifier")
col1, col2 = st.columns(2)

with col1:
    st.header("Settings")
    language = st.selectbox("Choose Language:", languages)

    st.header("Input Method")
    method = st.radio("", ("Enter Text", "Upload File"))
    text_input = ""
    file_content = ""
    if method == "Enter Text":
        text_input = st.text_area("Paste Discharge Instruction:")
    else:
        uploaded = st.file_uploader("Choose a .txt or .json file", type=["txt", "json"])
        if uploaded:
            file_content = uploaded.read().decode("utf-8")
            st.write(f"Uploaded: {uploaded.name}")

    if st.button("Simplify"):
        payload = text_input if method == "Enter Text" else file_content
        if not payload.strip():
            st.warning("Please enter text or upload a file.")
        else:
            with st.spinner("Processing…"):
                try:
                    res = requests.post(
                        API_URL,
                        json={"raw_text": payload, "language": language}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["summary"]     = data["summary"]
                        st.session_state["precautions"] = data["precautions"]
                        st.session_state["medications"] = data["medications"]
                    else:
                        st.error(f"Backend error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

with col2:
    st.header("Simplified Output")
    has_content = False

    # — Summary (cleaned) —
    raw_summary = st.session_state.get("summary", "")
    if raw_summary:
        has_content = True
        clean = raw_summary.replace("Summary:", "").split("Precautions:")[0].strip()
        st.subheader("Summary")
        st.markdown(f"- {clean}")

    # — Precautions —
    precs = st.session_state.get("precautions", [])
    if precs:
        has_content = True
        st.subheader("Precautions")
        for p in precs:
            st.markdown(f"- {p}")

    # — Medications / Tasks —
    meds = st.session_state.get("medications", [])
    if meds:
        has_content = True
        st.subheader("Medications / Tasks")
        for m in meds:
            if isinstance(m, dict):
                sym = m["symptom"].title()
                med = m["medication"]
                instr = m["instructions"]
                st.markdown(f"- **{sym}:** {med}. {instr}")
            else:
                st.markdown(f"- {m}")

    if not has_content:
        st.info("Your simplified output will appear here.")