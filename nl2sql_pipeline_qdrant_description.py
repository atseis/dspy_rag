import time
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
import json

file_path = './data/tables.json'
with open(file_path, 'r', encoding='utf-8') as f:
    tables_dict = json.load(f)
# 设置环境
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)

# client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")
client = QdrantClient(url="http://localhost:6333")  # 指向 Qdrant Server

qdrant_collection_name="fufu_descriptions_no_cols"
qdrant_retriever = QdrantRM(
    qdrant_client=client,
    qdrant_collection_name=qdrant_collection_name,
    # vectorizer=vectorizer,
    # document_field="text",
    k=TOP_K
)

dspy.configure(lm=lm, rm= qdrant_retriever)
# retrieve=dspy.Retrieve()
# retrieve("请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码")
def extract_table_name(s):
    en = re.search(r'CREATE TABLE `([^`]+)`', s).group(1)
    ch = re.search(r'COMMENT\s*=\s*\'([^\']*)\'', s).group(1)
    return en,ch
# 对一个新查询的 SQL 生成 query + context -> answer
class GenSQL_based_on_query(dspy.Signature):
    """It's a NL2SQL task"""
    query = dspy.InputField(desc='User Input')
    context = dspy.InputField(desc="Relevant tables")
    answer = dspy.OutputField(desc="generated sql")
    # tables = dspy.OutputField(desc='Extract all the names of tables from context both in English and Chinese')

class RAG_query(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query)
    def forward(self, query):
        search_result = client.query(
            collection_name=qdrant_collection_name,
            query_text=query
        )[:5]
        tables = [r.metadata['table'] for r in search_result]
        context = [tables_dict[table] for table in tables if table in tables_dict]
        prediction=self.generate_answer(query=query,context=context)
        # return dspy.Prediction(context=context, answer=prediction.answer)
        return prediction.answer, tables

# 判断用户输入内容的种类、意图 query -> intent
class Sig_UserIntentRecog(dspy.Signature):
    """Determine the intent of user input with only a number"""
    query = dspy.InputField()
    intent = dspy.OutputField(desc='output 1 if input is a new query; output 2 if input is a feedback')

# 基于用户的反馈，重新生成 SQL 内容  feedback + history + context -> answer
class GenSQL_based_on_query_and_feedback(dspy.Signature):
    """It's a NL2SQL task based on conversation history and user's feedback"""
    feedback = dspy.InputField()
    history = dspy.InputField(desc="Conversation history between user and LLM.")
    context = dspy.InputField(desc="Relevant tables")
    answer = dspy.OutputField(desc="generated sql")
    # tables = dspy.OutputField(desc='Extract all the names of tables from context both in English and Chinese')

class RAG_query_feedback(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query_and_feedback)
    def forward(self, feedback, history):
        search_result = client.query(
            collection_name=qdrant_collection_name,
            query_text='\n'.join(history)+"\nUser's feedback: "+feedback
        )[:5]
        tables = [r.metadata['table'] for r in search_result]
        context = [tables_dict[table] for table in tables if table in tables_dict]
        # tables
        # context = self.retrieve('\n'.join(history)+"\nUser's feedback: "+feedback).passages
        # tables = [extract_table_name(t) for t in context]
        prediction = self.generate_answer(feedback=feedback, history='\n'.join(history), context=context)
        return prediction.answer, tables



# 创建模块
gensql = RAG_query()
intent_recognizer = dspy.ChainOfThought(Sig_UserIntentRecog)
adjustsql = RAG_query_feedback()

# ======================================== 命令行 ===============================
# 搭建 Pipeline
# query = input("User: >>> ")
# while(True):
#     history = []
#     answer, tables = gensql(query)
#     # tables = ', '.join([t[0]+'='+t[1] for t in tables])
#     tables = ', '.join(tables)
#     output =answer+'\nRelevant tables are as follows:\n'+tables
#     print('Assistant: >>> '+output)

#     history.append("User: "+query)
#     history.append("Assistant: "+output)

#     feedback = input("User: >>> ")
#     intent = intent_recognizer(query=feedback).intent
#     while(intent =='feedback'):
#         answer, tables = adjustsql(feedback, history)
#         tables = ', '.join(tables)
#         output =answer+'\nRelevant tables are as follows:\n'+tables
#         tables = ', '.join(tables)
#         # tables = ', '.join([t[0]+'='+t[1] for t in tables])
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
    'intent': '1',
    'query': '',
    'feedback': ''
}

# 请求体模型
class QueryModel(BaseModel):
    query: str

@app.post("/query")
def handle_query(input_data: QueryModel):
    query = input_data.query
    if session_state['intent'] =='0':
        start_time = time.time()
        session_state['intent'] = intent_recognizer(query=query).intent
        end_time = time.time()
        print(f"intent_recognizer 运行时间: {end_time - start_time} 秒")

    if session_state['intent'] =='1': # new query
        session_state['history'] =[]
        session_state['query'] = query

        start_time = time.time()
        answer, tables = gensql(query)
        end_time = time.time()
        print(f"gensql 运行时间: {end_time - start_time} 秒")

        # tables_str = ', '.join([t[0]+'='+t[1] for t in tables])
        tables_str = ', '.join(tables)
        output = answer + '\nRelevant tables are as follows:\n' + tables_str
        session_state['history'].append(f"User: {query}")
        session_state['history'].append(f"Assistant: {output}")

        session_state['intent']='0'
        return {"output": output, "intent": session_state['intent'], "history": session_state['history']}
    elif session_state['intent'] =='2': # feedback 
        session_state['feedback'] = query

        start_time = time.time()
        answer, tables = adjustsql(session_state['feedback'], session_state['history'])
        end_time = time.time()
        print(f"adjustsql 运行时间: {end_time - start_time} 秒")
        
        # tables_str = ', '.join([t[0]+'='+t[1] for t in tables])
        tables_str = ', '.join(tables)
        output = answer + '\nRelevant tables are as follows:\n' + tables_str
        session_state['history'].append(f"User: {query}")
        session_state['history'].append(f"Assistant: {output}")
        
        session_state['intent']='0'
        return {"output": output, "intent": session_state['intent'], "history": session_state['history']}
    else:
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(session_state['intent'])


@app.get("/history")
def get_history():
    return {"history": session_state['history']}

# # debugpy.listen(("0.0.0.0", 5678))  # 监听端口 5678
# print("Debugger is ready and listening on port 5678")


# if __name__ == "__main__":
#     uvicorn.run("nl2sql_pipeline_qdrant:app", host="0.0.0.0", port=8000, reload=True)

