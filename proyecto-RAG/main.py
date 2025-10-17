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

load_dotenv()

embeddings = MistralAIEmbeddings()
llm = ChatMistralAI()

vectorstore = Chroma(
    persist_directory = "./mistral-embeddings_db",
    embedding_function = embeddings
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Eres un asistente que ayuda a responder preguntas\n"
         "Usa el siguiente contexto para responder a la pregunta del final.\n"
         "Si no sabes la respuesta simplemente dí que no sabes, no intentes inventar una respuesta.\n\n"),
        ("human", "Contexto: {context}\n"),
        MessagesPlaceholder(variable_name="messages", n_messages=5)
    ]
)

runnable = prompt | llm

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    query: str

def generate(state: State):
    response = runnable.invoke(state)
    return {"messages": [response]}

def retrieve(state: State):
    print("MSG:" + state["messages"][-1].content)
    print("QUERY:" + state["query"])
    retrieved_docs = vectorstore.similarity_search(state["query"])
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return {"context": docs_content}

rewrite_prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Reformula la última pregunta del usuario de forma clara y autónoma,\n"
         "pero responde únicamente con la pregunta reescrita.\n"
         "No des explicaciones, no contestes la pregunta, no añadas contexto extra.\n"
         "Devuelve solo la query reescrita en una sola línea.\n"
         "Si la pregunta original ya es una pregunta clara y autónoma, simplemente repítela en el mismo idioma en el que se formuló.\n"),
        MessagesPlaceholder(variable_name="messages")
    ]
)

query_rewriter = rewrite_prompt | llm

def rewrite_query(state: State):
    rewritten = query_rewriter.invoke(state)
    return {"query": rewritten.content}

workflow = StateGraph(state_schema=State)
graph_builder = workflow.add_sequence([rewrite_query, retrieve, generate])
graph_builder.add_edge(START, "rewrite_query")

memory = MemorySaver()
app = graph_builder.compile(checkpointer=memory)

### METODO PARA HACER PREGUNTAS DE EVALUACION
def get_rag_response(question: str) -> str:
    config = {"configurable": {"thread_id": "evaluation"}}
    input_dict = {
        "messages": [HumanMessage(question)],
        "context": []
    }
    output = app.invoke(input_dict, config)
    return output["messages"][-1].content

if __name__ == "__main__":
    while True:
        config = {"configurable": {"thread_id": "abc345"}}
        user_question = input(">> ")
        input_dict = {
            "messages": [HumanMessage(user_question)],
            "context": []
        }
        output = app.invoke(input_dict, config)
        output["messages"][-1].pretty_print()