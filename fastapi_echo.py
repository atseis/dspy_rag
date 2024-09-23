from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 定义请求体模型
class Message(BaseModel):
    content: str

# Echo 路由
@app.post("/echo/")
async def echo_message(message: Message):
    return {"echo": message.content}

# 根路由（GET）
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Echo server!"}
