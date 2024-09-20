from dspy.retrieve.chromadb_rm import ChromadbRM
import os
import openai
import chromadb
from chromadb.utils import embedding_functions


embedding_function = embedding_functions.DefaultEmbeddingFunction()

retriever_model = ChromadbRM(
    'fufu',
    './data/fufu_chroma.db',
    embedding_function=embedding_function,
    k=5
)

results = retriever_model("请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码", k=5)

for result in results:
    print("Document:", result.long_text, "\n")