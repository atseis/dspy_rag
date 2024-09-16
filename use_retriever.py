import chromadb
from chromadb.utils import embedding_functions


# 初始化 ChromaDB 客户端
client = chromadb.PersistentClient(path='./data/fufu_chroma.db')

# 创建一个默认的嵌入函数
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# 创建一个集合，假设集合名为 "demo_collection"
collection = client.get_collection("fufu", embedding_function=embedding_function)


results = collection.query(query_texts=["请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码"],n_results=5)
print(results["documents"])