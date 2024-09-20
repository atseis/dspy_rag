from qdrant_client import QdrantClient


def load_and_split_text(file_path, delimiter="-- ----------------------------"):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用分隔符分割文本
    chunks = content.split(delimiter)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def insert_to_chromadb(client, collection, text_chunks):
    client.add(
        collection_name=collection,
        documents=text_chunks,
        ids=[i+1 for i in range(len(text_chunks))]
    )

# Initialize the client
client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")

file_path  = './data/fufu_ds.txt'
chunks=load_and_split_text(file_path)
insert_to_chromadb(client,"fufu", chunks)
