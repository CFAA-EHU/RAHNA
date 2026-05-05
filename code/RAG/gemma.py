from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
from typing import Sequence
from langchain_chroma import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from transformers import AutoProcessor, Gemma3ForConditionalGeneration, BitsAndBytesConfig
from langchain_huggingface import HuggingFaceEmbeddings

import torch
import uuid
import sys
import os
import time

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"DEVICE: {device}")

# --- Embeddings ---
embeddings = HuggingFaceEmbeddings(
    model_name="/home/niturregi/proyecto/modelos/modelo",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"batch_size": 4, "normalize_embeddings": True},
    cache_folder="./hf_cache"
)

# --- LLM: Gemma-3-4b-it ---
model_path = "/home/niturregi/proyecto/modelos/gemma_4b"

#bnb_config = BitsAndBytesConfig(
#    load_in_8bit=True
#)

#bnb_config = BitsAndBytesConfig(
#    load_in_4bit=True,
#    bnb_4bit_compute_dtype=torch.float16,
#    bnb_4bit_quant_type="nf4",
#    bnb_4bit_use_double_quant=True
#)

model = Gemma3ForConditionalGeneration.from_pretrained(
    model_path, 
    device_map="auto",
    #quantization_config=bnb_config,
    dtype=torch.bfloat16,
).eval()

model.generation_config.top_p = None
model.generation_config.top_k = None
model.generation_config.temperature = None

processor = AutoProcessor.from_pretrained(model_path, use_fast=True)

MAX_NEW_TOKENS = 512
def gemma_chat(messages, temp):
    """
    messages: [{'role': 'system/user/assistant', 'content': str}]
    """
    gemma_msgs = []
    for msg in messages:
        gemma_msgs.append({
            "role": msg['role'],
            "content": [{"type": "text", "text": msg['content']}]
        })

    inputs = processor.apply_chat_template(
        gemma_msgs,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt"
    ).to(model.device, dtype=torch.bfloat16)

    input_len = inputs["input_ids"].shape[-1]

    gen_kwargs = {
            "max_new_tokens": MAX_NEW_TOKENS,
            "remove_invalid_values": True,
    }

    if temp==0.0:
        gen_kwargs["do_sample"] = False
    else:
        gen_kwargs.update({
            "do_sample": True,
            "temperature": temp,
            "top_p": 0.9,
            "top_k": 50,
        })

    with torch.inference_mode():
        outputs = model.generate(**inputs, **gen_kwargs)
        outputs = outputs[0][input_len:]

    decoded = processor.decode(outputs, skip_special_tokens=True)
    return decoded, input_len

# --- Vectorstore ---
vectorstore = Chroma(
    persist_directory="./embeddings_db",
    embedding_function=embeddings
)

# --- Prompts para RAG ---
def build_rag_system_prompt(context: str) -> str:
    return (
        "Eres un asistente que responde preguntas basándose únicamente en el contexto.\n"
        "Si no sabes la respuesta, responde: 'No lo sé'.\n"
        "Sé breve (máx. 100 palabras).\n\n"
        f"Contexto:\n{context}\n"
    )

def build_query_rewriter_prompt(messages: list[BaseMessage]) -> list[dict]:
    conversation_text = ""
    for msg in messages:
        role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
        conversation_text += f"{role}: {msg.content}\n"
    return [
        {
            "role": "system",
            "content": (
                "Reformula la última pregunta del usuario para que sea clara, completa e independiente, de manera que pueda ser entendida sin leer la conversación completa. Responde SOLO con la pregunta, sin explicaciones ni contexto adicional. Mantén el idioma original."
            ),
        },
        {"role": "user", "content": conversation_text},
    ]

# --- Estado de LangGraph ---
# Función para limitar la cantidad de mensajes que guardamos en la lista del estado. Para que la memoria no crezca sin control.
MAX_HISTORY = 4
def add_messages_limited(existing_messages, new_messages):
    combined = add_messages(existing_messages, new_messages)
    if len(combined) <= MAX_HISTORY:
        return combined
    excess = len(combined) - MAX_HISTORY
    if excess % 2 != 0:
        excess += 1
    return combined[excess:]

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages_limited]
    context: str
    query: str
    retrieval_time: float
    generation_prompt_tokens: int

# --- Nodos del grafo ---
def rewrite_query(state: State):
    prompt_msgs = build_query_rewriter_prompt(state["messages"])
    rewritten = gemma_chat(prompt_msgs, 0.0)
    return {"query": rewritten}

def retrieve(state: State):
    t0 = time.perf_counter()
    retrieved_docs = vectorstore.similarity_search(state["query"], k=3)
    retrieval_time = time.perf_counter() - t0
    docs_content = "\n\n".join(
        f"[Fuente: {doc.metadata.get('source', 'N/A')} | "
        f"Página: {doc.metadata.get('page', 'N/A')} | "
        f"Sección: {doc.metadata.get('section', 'N/A')} | "
        f"Título: {doc.metadata.get('title', 'N/A')}]\n"
        f"{doc.page_content}"
        for doc in retrieved_docs
    )
    return {"context": docs_content, "retrieval_time": retrieval_time}

def generate(state: State):
    system_prompt = build_rag_system_prompt(state["context"])

    # Convertir todos los mensajes previos a formato Gemma
    formatted_msgs = [{"role": "system", "content": system_prompt}]

    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            formatted_msgs.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            formatted_msgs.append({"role": "assistant", "content": msg.content})

    output_text, prompt_tokens = gemma_chat(formatted_msgs, 0.3)
    return {"messages": [AIMessage(output_text)], "generation_prompt_tokens": prompt_tokens}

# --- Construcción del grafo ---
workflow = StateGraph(state_schema=State)
graph = workflow.add_sequence([rewrite_query, retrieve, generate])
graph.add_edge(START, "rewrite_query")

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# --- Función para usar el RAG desde Python ---
def get_rag_response(question: str, thread_id: str) -> tuple[str, str, float, float, int, int]:
    input_dict = {
        "messages": [HumanMessage(question)],
        "context": ""
    }
    config = {"configurable": {"thread_id": thread_id}}

    t0 = time.perf_counter()
    output = app.invoke(input_dict, config)
    response_time = time.perf_counter() - t0

    generation_prompt_tokens = output["generation_prompt_tokens"]

    total_tokens_budgeted = (
        generation_prompt_tokens + MAX_NEW_TOKENS
    )

    answer = output["messages"][-1].content
    retrieved_context = output["context"]
    retrieval_time = output["retrieval_time"]

    return answer, retrieved_context, retrieval_time, response_time, generation_prompt_tokens, total_tokens_budgeted

# --- CLI interactivo ---
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "gemma-rag"}}
    print("RAG-Gemma-3-4b-it listo. Escribe tu pregunta.\n")

    while True:
        print(">> ", end="", flush=True)
        user_q = sys.stdin.readline().strip()
        if not user_q:
            continue

        input_dict = {
            "messages": [HumanMessage(user_q)],
            "context": ""
        }

        output = app.invoke(input_dict, config)
        output["messages"][-1].pretty_print()

