import streamlit as st
import requests
st.title("Echo Bot")

# FastAPI 后端 URL
FASTAPI_URL = "http://127.0.0.1:8000"

# 初始化会话状态
if 'history' not in st.session_state:
    st.session_state['history'] = []

# 处理用户输入并发送请求到 FastAPI
def send_query(query):
    response = requests.post(f"{FASTAPI_URL}/query", json={"query": query})
    return response.json()

# 显示对话历史
def display_history():
    for entry in st.session_state['history']:
        st.write(entry)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = send_query(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})