import chromadb
from chromadb.utils import embedding_functions

def load_and_split_text(file_path, delimiter="-- ----------------------------"):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用分隔符分割文本
    chunks = content.split(delimiter)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def insert_to_chromadb(text_chunks):
    for i, chunk in enumerate(text_chunks):
        collection.add(
            documents=[chunk],  # 文本块
            ids=[str(i)]  # 唯一 ID
        )


# 初始化 ChromaDB 客户端
client = chromadb.PersistentClient(path='./data/fufu_chroma.db')

# 创建一个默认的嵌入函数
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# 创建一个集合，假设集合名为 "demo_collection"
collection = client.create_collection("fufu", embedding_function=embedding_function)

file_path  = './data/fufu_ds.txt'
# 第一步：加载并分割文本
text_chunks = load_and_split_text(file_path)

# 第二步：将文本块插入到 ChromaDB
insert_to_chromadb(text_chunks)