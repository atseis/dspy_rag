import dspy
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

from lms.DeepSeek import DeepSeek
from dspy.retrieve.chromadb_rm import ChromadbRM
import os
import openai
from dspy.retrieve.qdrant_rm import QdrantRM

TOP_K = 5

# 对一个新查询的 SQL 生成 query + context -> answer
class GenSQL_based_on_query(dspy.Signature):
    """This is an NL2SQL task that requires generating SQL based on user input and relevant table creation statements matched from the database."""
    query = dspy.InputField(desc='User Input')
    context = dspy.InputField(desc="Relevant tables retrieved from database based on User Input")
    answer = dspy.OutputField(desc="If the provided information is sufficient to generate SQL, then return the generated SQL; otherwise, return the current generation status (communicate with the user to confirm the retrieval results, and describe what additional information is needed for generation .etc).")
    tables = dspy.OutputField(desc='Extract the names of tables from context both in English and Chinese')

class RAG_query(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query)
    def forward(self, query):
        context= self.retrieve(query).passages
        prediction=self.generate_answer(query=query,context=context)
        return dspy.Prediction(context=context, answer=prediction.answer)

# 判断用户输入内容的种类、意图 query -> intent
class Sig_UserIntentRecog(dspy.Signature):
    """Determine the category and intent of the user input: a new query? Feedback on the old query result? Execute the generated SQL?"""
    query = dspy.InputField()
    intent = dspy.OutputField(desc='If it is a new query (i.e., unrelated to previous conversations), output new; if it is to execute SQL (generated SQL results will be given in previous conversations), output exec; otherwise, treat it as feedback on previous conversation content, output feedback; only the above three outputs are possible, no additional or other content in output')

# 基于用户的反馈，重新生成 SQL 内容 query + feedback + context -> answer
class GenSQL_based_on_query_and_feedback(dspy.Signature):
    """This is an NL2SQL task that requires generating SQL based on user input and relevant table creation statements matched from the database."""
    query = dspy.InputField()
    feedback = dspy.InputField()
    context = dspy.InputField(desc="Relevant tables retrieved from database based on User Input")
    answer = dspy.OutputField(desc="If the provided information is sufficient to generate SQL, then return the SQL and the names(includes the Chinese names) of the relevant tables currently retrieved ; otherwise, return the current generation status (the names of the relevant tables currently retrieved, communicate with the user to confirm the retrieval results, and describe what additional information is needed for generation).")

class RAG_query_feedback(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve=dspy.Retrieve()
        self.generate_answer=dspy.ChainOfThought(GenSQL_based_on_query)
    def forward(self, query):
        context= self.retrieve(query).passages
        prediction=self.generate_answer(query=query,context=context)
        return dspy.Prediction(context=context, answer=prediction.answer)




load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

lm = DeepSeek(model='deepseek-chat', api_key=api_key)

client = QdrantClient(path="./data/fufu_qdrant.db")  # or QdrantClient(path="path/to/db")


intent_recognizer = dspy.ChainOfThought(Sig_UserIntentRecog)




qdrant_retriever = QdrantRM(
    qdrant_client=client,
    qdrant_collection_name="fufu",
    # vectorizer=vectorizer,
    # document_field="text",
    k=TOP_K
)

dspy.configure(lm=lm, rm= qdrant_retriever)
# retrieve=dspy.Retrieve()
# retrieve("请帮我查询态势平台的所有角色的信息，包括角色名称、角色编码")

rag= RAG_query()
my_question= '列出 t_sys_role_menu 表中所有内容'
pred=rag(my_question)


print(f"Question: {my_question}")
print(f"Predicted Answer: {pred.answer}")
print(f"Retrieved Contexts (truncated): {[c[:200] + '...' for c in pred.context]}")