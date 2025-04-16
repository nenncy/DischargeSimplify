import streamlit as st
import requests

st.title("Discharge Instructions Simplifier")

API_ENDPOINT = "http://localhost:8000/simplify"
col1, col2 = st.columns(2)

with col1:
    st.header("Choose Input Method")
    input_method = st.radio(" ", ("Enter Text", "Upload File"))

    text_input = ""
    file_content = ""

    if input_method == "Enter Text":
        text_input = st.text_area("Paste Discharge Instruction:")
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader("Choose a file (.txt or .json)", type=['txt', 'json'])
        if uploaded_file:
            file_content = uploaded_file.read().decode("utf-8")
            st.write(f"Uploaded file: {uploaded_file.name}")

    if st.button("Simplify"):
        content_to_send = text_input if input_method == "Enter Text" else file_content

        if not content_to_send.strip():
            st.warning("No input provided. Please enter text or upload a file.")
        else:
            with st.spinner("Processing with backend..."):
                st.session_state["result"] = None
                try:
                    res = requests.post(API_ENDPOINT, json={"text": content_to_send})
                    if res.status_code == 200:
                        st.session_state["result"] = res.json().get("result", "No result found.")
                    else:
                        st.session_state["result"] = f"Backend error: {res.status_code} - {res.text}"
                except Exception as e:
                    st.session_state["result"] = str(e)
     
                

with col2:
    st.header("Simplified Instruction:")
    if st.session_state.get("result"):
                    # st.subheader("")
        st.write(st.session_state["result"])
    else:
        st.info("Your simplified result will appear here after submission.")

