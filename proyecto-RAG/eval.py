from langchain_mistralai.chat_models import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from enum import Enum
import pandas as pd
import time
from langchain_mistralai import MistralAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Score(str, Enum):
    no_relevance = "0"
    low_relevance = "1"
    medium_relevance = "2"
    high_relevance = "3"

SCORE_DESCRIPTION = (
    "Score as a string between '0' and '3'. "
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
    context_relevance: ContextRelevance | None = None
    answer_relevance: AnswerRelevance | None = None
    groundedness: Groundedness | None = None


llm_judge = ChatMistralAI(model="mistral-small-2402", temperature=0)

rag_eval_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Eres un evaluador imparcial para un sistema de Generación Aumentada por Recuperación (RAG).\n"
        "Debes evaluar tres criterios:\n"
        "1. Relevancia del Contexto — qué tan bien se alinea el contexto recuperado con la consulta humana.\n"
        "2. Relevancia de la Respuesta — qué tan bien la respuesta aborda la consulta.\n"
        "3. Fundamentación — qué tan fiel es la respuesta al contexto proporcionado.\n"
        "Proporciona un razonamiento estructurado y una puntuación (0–3) para cada criterio."
    ),
    (
        "human",
        "Consulta: {query}\n\n"
        "Contexto Recuperado:\n{context}\n\n"
        "Respuesta Generada:\n{answer}"
    )
])

rag_evaluator = rag_eval_prompt | llm_judge.with_structured_output(RAGEvaluation)


def evaluate_rag_langchain(query: str, retrieved_context: str, generated_answer: str):
    """Evalúa un ejemplo RAG usando Mistral como juez."""
    result = rag_evaluator.invoke({
        "query": query,
        "context": retrieved_context,
        "answer": generated_answer
    })
    return result

embeddings_model = MistralAIEmbeddings(model="mistral-embed")

def compute_cosine_similarity(text1: str, text2: str) -> float:
    """Calcula la similitud coseno entre dos textos usando huggingface embeddings."""
    try:
        emb1 = embeddings_model.embed_query(text1)
        emb2 = embeddings_model.embed_query(text2)
        return float(cosine_similarity([emb1], [emb2])[0][0])
    except Exception as e:
        print(f"⚠ Error calculando similitud: {e}")
        return np.nan

chunk_size = 20
results = []

try:
    for chunk_number, chunk in enumerate(pd.read_csv("modelo_respuestas_completo_t0.3.csv", chunksize=chunk_size), start=1):
        for i, row in chunk.iterrows():
            query = row["Pregunta"]
            generated_answer = row["RespuestaModelo"]
            correct_answer = row["RespuestaCorrecta"]
            retrieved_context = row["ContextoUsado"]
            answer_time = row["TiempoRespuesta"]

            try:
                cosine_sim = compute_cosine_similarity(correct_answer, generated_answer)

                eval_result = evaluate_rag_langchain(query, retrieved_context, generated_answer)

                results.append({
                    "Tipo": row["Tipo"],
                    "Pregunta": query,
                    "RespuestaCorrecta": correct_answer,
                    "RespuestaModelo": generated_answer,
                    "Contexto": retrieved_context,
                    "TiempoRespuesta": answer_time,
                    "CosineSimilarity": round(cosine_sim, 4),
                    "ContextRelevance": eval_result.context_relevance.score.value,
                    "AnswerRelevance": eval_result.answer_relevance.score.value,
                    "Groundedness": eval_result.groundedness.score.value,
                    "Exp_ContextRelevance": eval_result.context_relevance.explanation,
                    "Exp_AnswerRelevance": eval_result.answer_relevance.explanation,
                    "Exp_Groundedness": eval_result.groundedness.explanation,
                })
                print(f"Fila {i+1} evaluada del chunk {chunk_number}/{len(chunk)}")
                time.sleep(1.2)  # Para no saturar el API

            except Exception as e:
                print(f"⚠ Error en la fila {i}: {e}")
                results.append({
                    "Tipo": row["Tipo"],
                    "Pregunta": query,
                    "RespuestaCorrecta": row["RespuestaCorrecta"],
                    "RespuestaModelo": generated_answer,
                    "Contexto": retrieved_context,
                    "TiempoRespuesta": answer_time,
                    "Error": str(e)
                })
                time.sleep(2)

    # Guardar resultados
    eval_df = pd.DataFrame(results)
    eval_df.to_csv("evaluacion_RAG_resultados_completo_t0.3.csv", index=False, encoding="utf-8")

    print("EVALUACION COMPLETADA")

except KeyboardInterrupt:
    eval_df = pd.DataFrame(results)
    eval_df.to_csv("evaluacion_RAG_resultados_cortado_t0.3.csv", index=False, encoding="utf-8")
    print("EVALUACION INTERRUMPIDA, RESULTADOS GUARDADOS")