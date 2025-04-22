import streamlit as st
import requests
import os
import pycountry

# Initialize session state for six sections
if "instructions" not in st.session_state:
    st.session_state.update({
        "instructions": [],
        "importance":   [],
        "follow_up":    [],
        "medications":  [],
        "precautions":  [],
        "references":   []
    })

# Build language list via pycountry
languages = sorted(
    {lang.name for lang in pycountry.languages if hasattr(lang, "alpha_2")}
)

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000") + "/simplify"

st.title("Discharge Instructions Simplifier")

# ————— Sidebar for settings & input —————
with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Choose Language:", languages)

    st.header("Input Method")
    method = st.radio("Select input method:", ("Enter Text", "Upload File"), label_visibility="visible")

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
            st.sidebar.warning("Please enter text or upload a file.")
        else:
            with st.spinner("Processing…"):
                try:
                    res = requests.post(
                        API_URL,
                        json={"raw_text": payload, "language": language}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state["instructions"] = data.get("instructions", [])
                        st.session_state["importance"]   = data.get("importance", [])
                        st.session_state["follow_up"]    = data.get("follow_up", [])
                        st.session_state["medications"]  = data.get("medications", [])
                        st.session_state["precautions"]  = data.get("precautions", [])
                        st.session_state["references"]   = data.get("references", [])
                    else:
                        st.sidebar.error(f"Backend error {res.status_code}: {res.text}")
                except Exception as e:
                    st.sidebar.error(f"Request failed: {e}")

# ————— Main area for output —————
st.header("Simplified Output")

has_content = False

# Simplified Instructions
if st.session_state["instructions"]:
    has_content = True
    st.subheader("Instructions")
    for s in st.session_state["instructions"]:
        st.markdown(f"- {s}")

# Importance
if st.session_state["importance"]:
    has_content = True
    st.subheader("Importance")
    for imp in st.session_state["importance"]:
        st.markdown(f"- {imp}")

# Follow‑Up Tasks
if st.session_state["follow_up"]:
    has_content = True
    st.subheader("Follow‑Up Appointments or Tasks")
    for f in st.session_state["follow_up"]:
        st.markdown(f"- {f}")

# Medications
if st.session_state["medications"]:
    has_content = True
    st.subheader("Medications")
    for m in st.session_state["medications"]:
        st.markdown(f"- {m}")

# Precautions
if st.session_state["precautions"]:
    has_content = True
    st.subheader("Precautions")
    for p in st.session_state["precautions"]:
        st.markdown(f"- {p}")

# References
if st.session_state["references"]:
    has_content = True
    st.subheader("References")
    for r in st.session_state["references"]:
        st.markdown(f"- {r}")

if not has_content:
    st.info("Your simplified output will appear here.")