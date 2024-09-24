import os, time,json
from prompts.prompts import INTENT_RECOG
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
# 加载 .env 文件
load_dotenv()
# 从环境变量中获取 API 密钥和端点
api_key = os.getenv('DEEPSEEK_API_KEY')
endpoint = os.getenv('DEEPSEEK_API_BASE')

client = OpenAI(
    api_key=api_key,
    base_url=endpoint
)
qdrant_client = QdrantClient(url="http://localhost:6333")  # 指向 Qdrant Server

qdrant_collection_name="fufu_descriptions_no_cols"
file_path = './data/tables.json'
with open(file_path, 'r', encoding='utf-8') as f:
    tables_dict = json.load(f)
class DB_RETRIEVER:
    def __init__(self, client,collection_name,  top_k):
        pass
    def retrieve(self, query):
        pass

class Qdrant_Retriver(DB_RETRIEVER):
    def __init__(self, client=qdrant_client,collection_name=qdrant_collection_name,  top_k=5):
        super.__init__()
        self.client=client
        self.collection=collection_name
        self.top_k=top_k
    def retrieve(self, query):
        search_result = self.client.query(
            collection_name=self.collection,
            query_text=query
        )[:self.top_k]
        tables = [r.metadata['table'] for r in search_result]
        context = [tables_dict[table] for table in tables if table in tables_dict]
        return context


class NL2SQL:
    def __init__(self, client=client, model="deepseek-chat" ):
        self.model = model
        self.conversation_history = []
        self.client = client
        self.time = time.time()
        self.TRY_TIME = 6 
    def add_message(self, message):
        self.conversation_history.append(message)

    def change_messages(self,messages):
        self.conversation_history = messages
    def llm_request(self,template,  **kwargs):
        prompt = template.format(**kwargs)
        response = self.client.chat.completions.create(
            messages = [
                {"role":"system","content":""},
                {"role":"user","content":prompt},
            ],
            temperature= 0.7,
            model = self.model
        )
        return response.choices[0].message.content
    def intent_recog(self, user_input):
        intent =  self.llm_request(INTENT_RECOG, conversation_history=self.conversation_history, user_input=user_input)
        if 'new' in intent:
            return 1
        else: # feedback
            return 2
    def retrieve_qdrant_tables(self, query):
        pass
    def retrieve_tables(self, query):
        pass
    def gensql(self, query):
        pass