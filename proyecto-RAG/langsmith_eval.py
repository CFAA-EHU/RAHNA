from langchain_mistralai.chat_models import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from langchain_mistralai import MistralAIEmbeddings
from pydantic import BaseModel, Field
from langsmith import traceable, Client
from enum import Enum
from main import get_rag_response
import pandas as pd
from dotenv import load_dotenv
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import time
import yaml

# Cargar variables de entorno y configuracion
load_dotenv()

with open("conf.yaml", "r") as f:
    conf = yaml.safe_load(f)

# Definir el esquema de evaluacion RAG
class Score(str, Enum):
    no_relevance = "0"
    low_relevance = "1"
    medium_relevance = "2"
    high_relevance = "3"

SCORE_DESCRIPTION = (
    "Puntuación entre '0' y '3'. "
    "0: Sin relevancia - completamente irrelevante. "
    "1: Baja relevancia - mínimamente relevante. "
    "2: Relevancia media - mayormente relevante. "
    "3: Alta relevancia - altamente relevante o completamente fundamentada."
)

class ContextRelevance(BaseModel):
    explanation: str = Field(..., description="Razonando sobre qué tan bien el contexto recuperado se alinea con la consulta.")
    score: Score = Field(..., description=SCORE_DESCRIPTION)

class AnswerRelevance(BaseModel):
    explanation: str = Field(..., description="Razonando sobre qué tan bien la respuesta aborda la consulta.")
    score: Score = Field(..., description=SCORE_DESCRIPTION)

class Groundedness(BaseModel):
    explanation: str = Field(..., description="Razonando sobre qué tan fiel es la respuesta al contexto recuperado.")
    score: Score = Field(..., description=SCORE_DESCRIPTION)

class RAGEvaluation(BaseModel):
    context_relevance: ContextRelevance
    answer_relevance: AnswerRelevance
    groundedness: Groundedness

llm_judge = ChatMistralAI(model="mistral-small-2402", temperature=0)

rag_eval_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un evaluador imparcial para un sistema de Generación Aumentada por Recuperación (RAG).\n"
        "Debes evaluar tres criterios:\n"
        "1. Relevancia del Contexto — qué tan bien se alinea el contexto recuperado con la consulta humana.\n"
        "2. Relevancia de la Respuesta — qué tan bien la respuesta aborda la consulta.\n"
        "3. Fundamentación — qué tan fiel es la respuesta al contexto proporcionado.\n"
        "Proporciona un razonamiento estructurado y una puntuación (0–3) para cada criterio.\n"
    ),
    (
        "human",
        "Consulta: {query}\n\n"
        "Contexto Recuperado:\n{context}\n\n"
        "Respuesta Generada:\n{answer}"
    )
])

rag_evaluator = rag_eval_prompt | llm_judge.with_structured_output(RAGEvaluation)
embeddings_model = MistralAIEmbeddings(model="mistral-embed")

@retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RemoteProtocolError, httpx.ReadTimeout)),
)
def safe_invoke_model(evaluator, payload: dict):
    """Invoca un Runnable con un ÚNICO input dict."""
    try:
        return evaluator.invoke(payload)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            print("Capacidad del modelo excedida (429). Reintentando…")
            raise
        raise

@traceable
def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Calcula similitud coseno entre dos textos."""
    emb1 = np.array(embeddings_model.embed_query(text1))
    emb2 = np.array(embeddings_model.embed_query(text2))
    emb1, emb2 = emb1 / np.linalg.norm(emb1), emb2 / np.linalg.norm(emb2)
    return float(np.dot(emb1, emb2))

@traceable
def evaluate_with_llm_judge(query: str, retrieved_context: str, generated_answer: str) -> RAGEvaluation:
    payload = {
        "query": query,
        "context": retrieved_context,
        "answer": generated_answer,
    }
    time.sleep(1.0)  # un pequeño respiro para no golpear el rate limit
    return safe_invoke_model(rag_evaluator, payload)

@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=40),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
def safe_get_rag_response(query: str):
    return get_rag_response(query)

@traceable
def rag_system(inputs: dict) -> dict:
    query = inputs["query"]

    generated_answer = ""
    retrieved_context = ""
    error_msg = None

    # Ejecuta el pipeline RAG (si recibe error reintenta)
    try:
        generated_answer, retrieved_context = safe_get_rag_response(query)
    except httpx.HTTPStatusError as e:
        error_msg = f"RAG HTTP error {e.response.status_code}"
    except Exception as e:
        error_msg = f"RAG error: {type(e).__name__}: {e}"

    # Evalua con el juez LLM (si recibe error, pasa)
    try:
        if generated_answer or retrieved_context:
            eval_result = evaluate_with_llm_judge(
                query, retrieved_context, generated_answer
            )
        else:
            eval_result = None
    except Exception as e:
        error_msg = f"Judge error: {type(e).__name__}: {e}"
        eval_result = None

    # Construye el output
    out = {
        "query": query,
        "generated_answer": generated_answer,
        "retrieved_context": retrieved_context,
        "error": error_msg,
    }

    if eval_result:
        out.update({
            "context_relevance": eval_result.context_relevance.score.value,
            "answer_relevance": eval_result.answer_relevance.score.value,
            "groundedness": eval_result.groundedness.score.value,
            "exp_context": eval_result.context_relevance.explanation,
            "exp_answer": eval_result.answer_relevance.explanation,
            "exp_groundedness": eval_result.groundedness.explanation
        })
    else:
        # Valores por defecto para que no fallen los evaluadores
        out.update({
            "context_relevance": None,
            "answer_relevance": None,
            "groundedness": None,
            "exp_context": None,
            "exp_answer": None,
            "exp_groundedness": None
        })
    return out

def _metric(key, value):
    return {"key": key, "score": value} if value is not None else None

def rag_judge(inputs: dict, outputs: dict, reference_outputs: dict):
    gen_answer = outputs.get("generated_answer", "")
    ref_answer = reference_outputs.get("answer", "")
    metrics = [
        _metric("context_relevance", float(outputs.get("context_relevance")) if outputs.get("context_relevance") is not None else None),
        _metric("answer_relevance", float(outputs.get("answer_relevance")) if outputs.get("answer_relevance") is not None else None),
        _metric("groundedness", float(outputs.get("groundedness")) if outputs.get("groundedness") is not None else None),
        _metric("cosine_similarity", compute_cosine_similarity(gen_answer, ref_answer) if gen_answer and ref_answer else None)
    ]
    # Filtra None
    metrics = [m for m in metrics if m is not None]

    if not metrics:
        return [
            {"key": "context_relevance", "score": 0.0},
            {"key": "answer_relevance", "score": 0.0},
            {"key": "groundedness", "score": 0.0},
            {"key": "cosine_similarity", "score": 0.0},
        ]
    
    return metrics

# Configurar cliente LangSmith y ejecutar evaluacion
ls_client = Client()
dataset_name = conf["variables"]["langsmith"]["dataset_name"]
datasets = ls_client.list_datasets(dataset_name=dataset_name)
dataset = next(datasets, None)
if not dataset:
    raise ValueError(f"No se encontró el dataset '{dataset_name}'. Tienes que crearlo primero.")

results = ls_client.evaluate(
    rag_system,
    data=dataset,
    evaluators=[rag_judge],
    experiment_prefix=conf["variables"]["langsmith"]["experiment_prefix"]
)
