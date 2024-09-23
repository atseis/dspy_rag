from qdrant_client import QdrantClient
import re
# client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")
client = QdrantClient(url="http://localhost:6333")  # 指向 Qdrant Server
collection_name='fufu_descriptions_no_cols'
# collection_name='fufu'

search_result = client.query(
    collection_name=collection_name,
    query_text="请帮我输出一份态势感知平台全网各单位的信息系统以及底下关联的数据库资产清单，清单中剔除无效的信息系统和数据库资产。"
)

# def extract_table_name(s):
#     en = re.search(r'CREATE TABLE `([^`]+)`', s).group(1)
#     ch = re.search(r'COMMENT\s*=\s*\'([^\']*)\'', s).group(1)
#     return en,ch

# tables= [extract_table_name(r.metadata['document']) for r in search_result]

# print(tables)
table = [r.metadata['table'] for r in search_result]
print(table)