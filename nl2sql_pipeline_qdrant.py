import debugpy,uvicorn
import streamlit as st
import dspy
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

from lms.DeepSeek import DeepSeek
from dspy.retrieve.chromadb_rm import ChromadbRM
import os
import openai
from dspy.retrieve.qdrant_rm import QdrantRM
import re
from fastapi import FastAPI, Body
from pydantic import BaseModel

app = FastAPI()

TOP_K = 5


def extract_table_name(s):
    en = re.search(r'CREATE TABLE `([^`]+)`', s).group(1)
    ch = re.search(r'COMMENT\s*=\s*\'([^\']*)\'', s).group(1)
    return en,ch
# 对一个新查询的 SQL 生成 query + context -> answer
class GenSQL_based_on_query(dspy.Signature):
    """This is an NL2SQL task that requires generating SQL based on user input and relevant table creation statements matched from the database."""
    query = dspy.InputField(desc='User Input')
    context = dspy.InputField(desc="Relevant tables retrieved from database based on User Input")
    answer = dspy.OutputField(desc="If the provided information is sufficient to generate SQL, then return the generated SQL; otherwise, return the current generation status (communicate with the user to confirm the retrieval results, and describe what additional information is needed for generation .etc).")
    # tables = dspy.OutputField(desc='Extract all the names of tables from context both in English and Chinese')

class RAG_query(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query)
    def forward(self, query):
        context= self.retrieve(query).passages
        tables = [extract_table_name(t) for t in context]
        prediction=self.generate_answer(query=query,context=context)
        # return dspy.Prediction(context=context, answer=prediction.answer)
        return prediction.answer, tables

# 判断用户输入内容的种类、意图 query -> intent
class Sig_UserIntentRecog(dspy.Signature):
    """Determine the category and intent of the user input: a new query? Feedback on the old query result? Execute the generated SQL?"""
    query = dspy.InputField()
    intent = dspy.OutputField(desc='If it is a new query (i.e., unrelated to previous conversations), output new; if it is to execute SQL (generated SQL results will be given in previous conversations), output exec; otherwise, treat it as feedback on previous conversation content, output feedback; only the above three outputs are possible, no additional or other content in output')

# 基于用户的反馈，重新生成 SQL 内容  feedback + history + context -> answer
class GenSQL_based_on_query_and_feedback(dspy.Signature):
    """This is a NL2SQL task to adjust the SQL generated based on user's feedback, its relevant table creation statements matched from the database and the conversation history."""
    feedback = dspy.InputField()
    history = dspy.InputField(desc="Conversation history between user and LLM.")
    context = dspy.InputField(desc="Relevant tables retrieved from database based on User Input")
    answer = dspy.OutputField(desc="If the provided information is sufficient to generate SQL, then return the SQL and the names(includes the Chinese names) of the relevant tables currently retrieved ; otherwise, return the current generation status (the names of the relevant tables currently retrieved, communicate with the user to confirm the retrieval results, and describe what additional information is needed for generation).")
    tables = dspy.OutputField(desc='Extract all the names of tables from context both in English and Chinese')

class RAG_query_feedback(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query_and_feedback)
    def forward(self, feedback, history):
        # tables
        context = self.retrieve('\n'.join(history)+"\nUser's feedback: "+feedback).passages
        tables = [extract_table_name(t) for t in context]
        prediction = self.generate_answer(feedback=feedback, history='\n'.join(history), context=context)
        return prediction.answer, tables

# 设置环境
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)

# client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")
client = QdrantClient(url="http://localhost:6333")  # 指向 Qdrant Server

qdrant_retriever = QdrantRM(
    qdrant_client=client,
    qdrant_collection_name="fufu",
    # vectorizer=vectorizer,
    # document_field="text",
    k=TOP_K
)

dspy.configure(lm=lm, rm= qdrant_retriever)
# retrieve=dspy.Retrieve()
# retrieve("请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码")

# 创建模块
gensql = RAG_query()
intent_recognizer = dspy.ChainOfThought(Sig_UserIntentRecog)
adjustsql = RAG_query_feedback()

# ======================================== 命令行 ===============================
# # 搭建 Pipeline
# query = input("User: >>> ")
# while(True):
#     history = []
#     answer, tables = gensql(query)
#     tables = ', '.join([t[0]+'='+t[1] for t in tables])
#     output =answer+'\nRelevant tables are as follows:\n'+tables
#     print('Assistant: >>> '+output)

#     history.append("User: "+query)
#     history.append("Assistant: "+output)

#     feedback = input("User: >>> ")
#     intent = intent_recognizer(query=feedback).intent
#     while(intent =='feedback'):
#         answer, tables = adjustsql(feedback, history)
#         output =answer+'\nRelevant tables are as follows:\n'+tables
#         tables = ', '.join([t[0]+'='+t[1] for t in tables])
#         print('Assistant: >>> '+output)
#         history.append("User: "+feedback)
#         history.append("Assistant: "+output)

#         feedback = input("User: >>> ")
#         intent = intent_recognizer(query=feedback).intent
#     if intent == 'new':
#         query = feedback
#         continue
#     else:
#         break

# ======================================== fastapi ===============================
# 会话状态存储 (全局变量)
session_state = {
    'history': [],
    'intent': 'new',
    'query': '',
    'feedback': ''
}

# 请求体模型
class QueryModel(BaseModel):
    query: str

@app.post("/query")
def handle_query(input_data: QueryModel):
    query = input_data.query
    
    # 新查询阶段
    if session_state['intent'] == 'new':
        session_state['query'] = query
        answer, tables = gensql(query)
        tables_str = ', '.join([t[0]+'='+t[1] for t in tables])
        output = answer + '\nRelevant tables are as follows:\n' + tables_str
        session_state['history'].append(f"User: {query}")
        session_state['history'].append(f"Assistant: {output}")
        session_state['intent'] = intent_recognizer(query=query).intent
        return {"output": output, "intent": session_state['intent'], "history": session_state['history']}

    # 反馈调整阶段
    elif session_state['intent'] == 'feedback':
        session_state['feedback'] = query
        answer, tables = adjustsql(session_state['feedback'], session_state['history'])
        tables_str = ', '.join([t[0]+'='+t[1] for t in tables])
        output = answer + '\nRelevant tables are as follows:\n' + tables_str
        session_state['history'].append(f"User: {query}")
        session_state['history'].append(f"Assistant: {output}")
        session_state['intent'] = intent_recognizer(query=query).intent
        return {"output": output, "intent": session_state['intent'], "history": session_state['history']}


@app.get("/history")
def get_history():
    return {"history": session_state['history']}

# # debugpy.listen(("0.0.0.0", 5678))  # 监听端口 5678
# print("Debugger is ready and listening on port 5678")


# if __name__ == "__main__":
#     uvicorn.run("nl2sql_pipeline_qdrant:app", host="0.0.0.0", port=8000, reload=True)

