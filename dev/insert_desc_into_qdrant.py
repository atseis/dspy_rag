from qdrant_client import QdrantClient

client = QdrantClient(url="http://127.0.0.1:6333")  # 指向 Qdrant Server

file_path  = './data/descriptions_no_cols.json'

import json

with open(file_path, 'r', encoding='utf-8') as f:
    descriptions = json.load(f)

id = 1
for table, description in descriptions.items():
    client.add(
        collection_name="fufu_descriptions_no_cols",
        documents=[description],
        ids=[id],
        metadata=[{"table": table}]
    )
    id+=1
