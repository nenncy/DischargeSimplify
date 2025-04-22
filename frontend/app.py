# import streamlit as st
# import requests

# st.title("Discharge Instructions Simplifier")

# API_ENDPOINT = "http://localhost:8000/simplify"
# API_ENDPOINT_ans = "http://localhost:8000/chat"
# col1, col2 = st.columns(2)

# with col1:
#     st.header("Choose Input Method")
#     input_method = st.radio(" ", ("Enter Text", "Upload File"))

#     text_input = ""
#     file_content = ""

#     if input_method == "Enter Text":
#         text_input = st.text_area("Paste Discharge Instruction:")
#     elif input_method == "Upload File":
#         uploaded_file = st.file_uploader("Choose a file (.txt or .json)", type=['txt', 'json'])
#         if uploaded_file:
#             file_content = uploaded_file.read().decode("utf-8")
#             st.write(f"Uploaded file: {uploaded_file.name}")

#     if st.button("Simplify"):
#         content_to_send = text_input if input_method == "Enter Text" else file_content

#         if not content_to_send.strip():
#             st.warning("No input provided. Please enter text or upload a file.")
#         else:
#             with st.spinner("Processing with backend..."):
#                 st.session_state["result"] = None
#                 try:
#                     res = requests.post(API_ENDPOINT, json={"text": content_to_send})
#                     if res.status_code == 200:
#                         st.session_state["result"] = res.json().get("result", "No result found.")
#                     else:
#                         st.session_state["result"] = f"Backend error: {res.status_code} - {res.text}"
#                 except Exception as e:
#                     st.session_state["result"] = str(e)
     
                

# # with col2:
# #     st.header("Simplified Instruction:")
# #     if st.session_state.get("result"):
# #                     # st.subheader("")
# #         st.write(st.session_state["result"])
# #     else:
# #         st.info("Your simplified result will appear here after submission.")

# with col2:
#     st.header("Simplified Instruction:")
    
#     if st.session_state.get("result"):
#         st.write(st.session_state["result"])

#         if "chat_history" not in st.session_state:
#             st.session_state.chat_history = []

#         # Display previous messages like chat
#         for msg in st.session_state.chat_history:
#             with st.chat_message("user"):
#                 st.markdown(msg["question"])
#             with st.chat_message("assistant"):
#                 st.markdown(msg["answer"])

#         # Input field for user question
#         user_input = st.chat_input("Ask a question about your instructions...")
        
#         if user_input:
#             with st.chat_message("user"):
#                 st.markdown(user_input)

#             with st.spinner("Processing your question..."):
#                 try:
#                     chat_payload = {
#                         "context": st.session_state["result"],  # Simplified instruction
#                         "question": user_input,
#                         "history": st.session_state.chat_history
#                     }

#                     res = requests.post(API_ENDPOINT_ans, json=chat_payload)
#                     if res.status_code == 200:
#                         answer = res.json().get("answer", "No answer found.")

#                         with st.chat_message("assistant"):
#                             st.markdown(answer)

#                         # Save the interaction to history
#                         st.session_state.chat_history.append({
#                             "question": user_input,
#                             "answer": answer
#                         })

#                     else:
#                         st.error(f"Backend error: {res.status_code} - {res.text}")
#                 except Exception as e:
#                     st.error(f"Chat error: {e}")
#     else:
#         st.info("Your simplified result will appear here after submission.")

import streamlit as st
import requests

st.title("Discharge Instructions Simplifier")

API_ENDPOINT = "http://localhost:8000/simplify"
API_ENDPOINT_ans = "http://localhost:8000/chat"

# ---- Sidebar: Input Section ----
st.sidebar.header("Input Method")
input_method = st.sidebar.radio("Select how you'd like to input instructions:", ("Enter Text", "Upload File"))

text_input = ""
file_content = ""

if input_method == "Enter Text":
    text_input = st.sidebar.text_area("Paste Discharge Instruction:")
elif input_method == "Upload File":
    uploaded_file = st.sidebar.file_uploader("Choose a file (.txt or .json)", type=['txt', 'json'])
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        st.sidebar.success(f"Uploaded: {uploaded_file.name}")

if st.sidebar.button("Simplify"):
    content_to_send = text_input if input_method == "Enter Text" else file_content

    if not content_to_send.strip():
        st.sidebar.warning("No input provided. Please enter text or upload a file.")
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

# ---- Main Area: Output and Chat ----
col2 = st.container()

with col2:
    st.header("Simplified Instruction")
    
    if st.session_state.get("result"):
        st.write(st.session_state["result"])

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message("user"):
                st.markdown(msg["question"])
            with st.chat_message("assistant"):
                st.markdown(msg["answer"])

        user_input = st.chat_input("Ask a question about your instructions...")

        if user_input:
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.spinner("Processing your question..."):
                try:
                    chat_payload = {
                        "context": st.session_state["result"],
                        "question": user_input,
                        "history": st.session_state.chat_history
                    }

                    res = requests.post(API_ENDPOINT_ans, json=chat_payload)
                    if res.status_code == 200:
                        answer = res.json().get("answer", "No answer found.")

                        with st.chat_message("assistant"):
                            st.markdown(answer)

                        st.session_state.chat_history.append({
                            "question": user_input,
                            "answer": answer
                        })
                    else:
                        st.error(f"Backend error: {res.status_code} - {res.text}")
                except Exception as e:
                    st.error(f"Chat error: {e}")
    else:
        st.info("Your simplified result will appear here after submission.")

