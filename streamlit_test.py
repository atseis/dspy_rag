import streamlit as st
from lms.DeepSeek import DeepSeek

from dotenv import load_dotenv
import dspy,os

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)
dspy.configure(lm=lm)

st.title("Echo Bot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

cot = dspy.ChainOfThought('question -> answer')
# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    response = f"Echo: {cot(question=prompt).answer}"
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})