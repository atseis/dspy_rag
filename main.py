import dspy
import os
from dotenv import load_dotenv

from DeepSeek import DeepSeek
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
)

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)

dspy.configure(lm=lm,rm=retriever_model)

class GenerateAnswer(dspy.Signature):
    """It is a NL2SQL task. Given user query and relavant sql table infos, generate the corresponding sql."""

    query = dspy.InputField()
    context = dspy.InputField(desc="may contain relevant SQL tables")
    sql = dspy.OutputField(desc="sql that user wants")

class RAG(dspy.Module):
    def __init__(self, num_passages=3):
        super().__init__()

        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate_answer = dspy.ChainOfThought(GenerateAnswer)
    
    def forward(self, question):
        context = self.retrieve(question).passages
        prediction = self.generate_answer(query=question,context=context)
        return dspy.Prediction(context=context, answer=prediction.sql)
    
rag = RAG()
my_question= '请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码'
pred = rag(my_question)

print(f"Question: {my_question}")
print(f"Predicted Answer: {pred.answer}")
print(f"Retrieved Contexts (truncated): {[c[:200] + '...' for c in pred.context]}")