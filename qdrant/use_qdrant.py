from qdrant_client import QdrantClient
import re
client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")

collection_name='fufu'

search_result = client.query(
    collection_name=collection_name,
    query_text="请帮我查询态势平台账号状态正常的用户数量"
)

def extract_table_name(s):
    en = re.search(r'CREATE TABLE `([^`]+)`', s).group(1)
    ch = re.search(r'COMMENT\s*=\s*\'([^\']*)\'', s).group(1)
    return en,ch

tables= [extract_table_name(r.metadata['document']) for r in search_result]

print(tables)