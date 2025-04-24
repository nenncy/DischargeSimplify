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

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000") 

st.title("Discharge Instructions Simplifier")

# ————— Sidebar for settings & input —————
with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Choose Language:", languages , index=languages.index("English"), label_visibility="visible")

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
                        API_URL + "/simplify",
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


# def validate(idx: int, text: str, section: str):
#     key_prefix = f"{section}_{idx}"
#     col1, col2 = st.columns([5, 1])

#     with col1:
#         st.markdown(f"- {text}")
#     with col2:
#         if st.button("Validate", key=f"validate_{key_prefix}"):
#             st.session_state[f"show_trace_{key_prefix}"] = True

#     # Show popup-like expander if opened
#     if st.session_state.get(f"show_trace_{key_prefix}", False):
#         with st.expander("📌 Original Statement", expanded=True):
#             # Optional: Replace this with real API call to /trace
#             st.markdown("_Fetching source..._")
#             response = requests.post(
#                 API_URL + "/validate",
#                 json={
#                     "simplified_text": text,
#                     "original_text": text_input or file_content
#                 }
#             )

#             # Example live fetch (uncomment if backend is ready):
#             # response = requests.post("http://localhost:8000/trace", json={
#             #     "simplified_text": text,
#             #     "original_text": text_input or file_content
#             # })
#             if response.status_code == 200:
#                 result = response.json()
#                 print(result,"***********")
#                 # st.markdown(f"**Simplified Instruction:** {result.get('simplified_text')}")
#                 st.markdown(f"**Match Found:** {'✅ Yes' if result.get('is_valid') else '❌ No'}")
#                 st.markdown(f"**Explanation:** {result.get('explanation')}")

#             else:
#                 st.warning("Error fetching source.")

#             if st.button("Close", key=f"close_{key_prefix}"):
#                 st.session_state[f"show_trace_{key_prefix}"] = False

@st.dialog("Validate Simplified Instructions")
def validate_section(items: list, idx: int, original_text: str):
    # key_prefix = f"{section_name}_{idx}"
    st.markdown("_Fetching source..._")
    for item in items:
                
                response = requests.post(
                    API_URL + "/validate",
                    json={
                        "simplified_text": item,
                        "original_text": original_text
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    st.markdown(f"- **{item}**")
                    st.markdown(f"  Match Found: {'✅' if result['is_valid'] else '❌'}")
                    st.markdown(f"  Explanation: _{result['explanation']}_")
                else:
                    st.markdown(f"- ❌ Error validating: {item}")

    # col1, col2 = st.columns([2, 1])
    # with col1:
    #     st.markdown(f"### {section_name}")
    # with col2:
    #     if st.button("Validate", key=f"validate_{key_prefix}"):
    #         st.session_state[f"show_section_trace_{key_prefix}"] = True

    # if st.session_state.get(f"show_section_trace_{key_prefix}", True):
    #     # if st.button("Close", key=f"close_section_{key_prefix}"):
    #     #     st.session_state[f"show_section_trace_{key_prefix}"] = False
    #     #     return 
    #     with st.expander(f"Validation Report for {section_name}", expanded=True):
    #         for item in items:
    #             response = requests.post(
    #                 API_URL + "/validate",
    #                 json={
    #                     "simplified_text": item,
    #                     "original_text": original_text
    #                 }
    #             )
    #             if response.status_code == 200:
    #                 result = response.json()
    #                 st.markdown(f"- **{item}**")
    #                 st.markdown(f"  Match Found: {'✅' if result['is_valid'] else '❌'}")
    #                 st.markdown(f"  Explanation: _{result['explanation']}_")
    #             else:
    #                 st.markdown(f"- ❌ Error validating: {item}")

           

# ————— Main area for output —————
st.header("Simplified Output")

has_content = False

# Simplified Instructions
if st.session_state["instructions"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("Instructions")
    with col2:
        if st.button("Validate All Instructions"):
            validate_section(st.session_state["instructions"], idx=0, original_text=text_input or file_content)
    for s in st.session_state["instructions"]:
        st.markdown(f"- {s}")

# Importance
if st.session_state["importance"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("Importance")
    with col2:
        if st.button("Validate All Importance"):
            validate_section(st.session_state["importance"], idx=1, original_text=text_input or file_content)

    # for idx, imp in enumerate(st.session_state["importance"]):
    #     validate(idx, imp, "importance")
    for imp in st.session_state["importance"]:
        st.markdown(f"- {imp}")

# Follow‑Up Tasks
if st.session_state["follow_up"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("Follow‑Up Appointments or Tasks")
    with col2:
        if st.button("Validate All Follow-Up"):
            validate_section(st.session_state["follow_up"], idx=2, original_text=text_input or file_content)
    # for idx, imp in enumerate(st.session_state["follow_up"]):
    #     validate(idx, imp, "follow_up")
    for f in st.session_state["follow_up"]:
        st.markdown(f"- {f}")

# Medications
if st.session_state["medications"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("Medications")
    with col2:
        if st.button("Validate All Medications"):
            validate_section(st.session_state["medications"], idx=3, original_text=text_input or file_content)
    
    # for idx, imp in enumerate(st.session_state["medications"]):
    #     validate(idx, imp, "medications")
    for m in st.session_state["medications"]:
        st.markdown(f"- {m}")

# Precautions
if st.session_state["precautions"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("Precautions")
    with col2:
        if st.button("Validate All Precautions"):
            validate_section(st.session_state["precautions"], idx=3, original_text=text_input or file_content)
    # for idx, imp in enumerate(st.session_state["precautions"]):
    #     validate(idx, imp, "precautions")
    for p in st.session_state["precautions"]:
        st.markdown(f"- {p}")

# References
if st.session_state["references"]:
    has_content = True
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("References")
    with col2:
        if st.button("Validate All References"):
            validate_section(st.session_state["references"], idx=3, original_text=text_input or file_content)
    
    # for idx, imp in enumerate(st.session_state["references"]):
    #     validate(idx, imp, "references")
    for r in st.session_state["references"]:
        st.markdown(f"- {r}")

if not has_content:
    st.info("Your simplified output will appear here.")