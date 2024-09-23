from fastapi import FastAPI
from pydantic import BaseModel
import dspy,os
from lms.DeepSeek import DeepSeek
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)

app = FastAPI()

# 定义请求体模型
class Message(BaseModel):
    query: str

# Echo 路由
@app.post("/query/")
async def echo_message(message: Message):
    response = lm(message.query)
    return {"query": response}

# 根路由（GET）
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Echo server!"}
