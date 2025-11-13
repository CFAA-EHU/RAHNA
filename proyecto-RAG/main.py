from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import START, StateGraph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import uuid
import sys

load_dotenv()

embeddings = MistralAIEmbeddings()
chat_model = ChatMistralAI(
    model = "mistral-medium",
    temperature = 0.3
)
rewrite_model = ChatMistralAI(
    model = "mistral-medium",
    temperature = 0.0
)

vectorstore = Chroma(
    persist_directory = "./mistral-embeddings_db",
    embedding_function = embeddings
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Eres un asistente que ayuda a responder preguntas\n"
         "Usa el siguiente contexto para responder a la pregunta del final.\n"
         "Si no sabes la respuesta simplemente dí 'no sé', no intentes inventar una respuesta.\n\n"
         "Haz tu respuesta corta y concisa. No superes las 100 palabras en la respuesta.\n"),
        ("human", "Contexto: {context}\n"),
        MessagesPlaceholder(variable_name="messages", n_messages=5)
    ]
)

runnable = prompt | chat_model

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    query: str

def generate(state: State):
    response = runnable.invoke(state)
    return {"messages": [response]}

def retrieve(state: State):
    retrieved_docs = vectorstore.similarity_search(state["query"])
    docs_content = "\n\n".join(
        f"[Documento: {doc.metadata.get('source', 'N/A')} | Página: {doc.metadata.get('page', 'N/A')} | Sección: {doc.metadata.get('section', 'N/A')} | Título: {doc.metadata.get('title', 'N/A')}]\n{doc.page_content}\n"
        for doc in retrieved_docs
    )
    return {"context": docs_content}

rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Reformula la última pregunta del usuario de forma clara y autónoma, pero responde únicamente con la pregunta reescrita.\n"
         "No des explicaciones, no contestes la pregunta, no añadas contexto extra.\n"
         "Si la pregunta original ya es una pregunta clara y autónoma, simplemente repítela en el mismo idioma en el que se formuló.\n"),
        MessagesPlaceholder(variable_name="messages")
    ]
)

query_rewriter = rewrite_prompt | rewrite_model

def rewrite_query(state: State):
    rewritten = query_rewriter.invoke(state)
    print(rewritten.content)
    return {"query": rewritten.content}

workflow = StateGraph(state_schema=State)
graph_builder = workflow.add_sequence([rewrite_query, retrieve, generate])
graph_builder.add_edge(START, "rewrite_query")

memory = MemorySaver()
app = graph_builder.compile(checkpointer=memory)

### METODO PARA HACER PREGUNTAS DE EVALUACION
def get_rag_response(question: str) -> tuple[str, str]:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    input_dict = {
        "messages": [HumanMessage(question)],
        "context": []
    }
    output = app.invoke(input_dict, config)
    generated_answer = output["messages"][-1].content
    retrieved_context = output["context"]

    return generated_answer, retrieved_context


if __name__ == "__main__":
    while True:
        config = {"configurable": {"thread_id": "abc345"}}
        print(">> ", end="", flush=True)
        user_question = sys.stdin.readline().strip()
        input_dict = {
            "messages": [HumanMessage(user_question)],
            "context": []
        }
        output = app.invoke(input_dict, config)
        output["messages"][-1].pretty_print()