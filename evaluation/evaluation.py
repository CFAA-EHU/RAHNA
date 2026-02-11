import vertexai
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from ragas import evaluate
from ragas.metrics import ContextRelevance, Faithfulness, AnswerRelevancy
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
import pandas as pd
from dotenv import load_dotenv
import re
import os
from ragas.run_config import RunConfig
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Initialize VertexAI and models
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
vertexai.init(project=PROJECT_ID, location=LOCATION)

evaluator_llm = LangchainLLMWrapper(VertexAI(model_name="gemini-2.5-pro"))

evaluator_embeddings = LangchainEmbeddingsWrapper(VertexAIEmbeddings(model_name="gemini-embedding-001"))

# Function to compute cosine similarity
def compute_cosine_similarity(text1: str, text2: str) -> float:
    try:
        emb1 = evaluator_embeddings.embed_query(text1)
        emb2 = evaluator_embeddings.embed_query(text2)
        return float(cosine_similarity([emb1], [emb2])[0][0])
    except Exception as e:
        print(f"Error computing cosine similarity: {e}")
        return np.nan

# Define experiment characteristics
experiment_char = {
        "experiment_id": "1",
        "llm": "Qwen2.5-7B-Instruct",
        "quantization": "8-bit",
        "temperature": "0.3",
        "chunk_size_and_overlap": "2000, 200",
        "k_retrieved_contexts": "3",
}

# Define evaluation metrics
context_relevance = ContextRelevance(llm=evaluator_llm)
faithfulness = Faithfulness(llm=evaluator_llm)
answer_relevancy = AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)

# CSV file with the answers given by the RAG system
df = pd.read_csv("respuestas_modelo/respuestas_modelo_default_settings.csv")

user_inputs = df['pregunta'].tolist()
retrieved_contexts = df['contexto_usado'].tolist()
responses = df['respuesta_modelo'].tolist()
references = df['respuesta_correcta'].tolist()
question_types = df['tipo_pregunta'].tolist()
retrieval_time = df['retrieval_time'].tolist()
response_time = df['response_time'].tolist()
generation_prompt_tokens = df['generation_prompt_tokens'].tolist()
total_tokens_budgeted = df['total_tokens_budgeted'].tolist()
question_ids = list(range(len(df)))

# Create samples for RAGAS to evaluate for each entry in the CSV
n = len(user_inputs)
samples = []

for i in range(n):
    split_contexts = re.split(r"(?<!^)(?=\[Fuente:)", retrieved_contexts[i])

    sample = SingleTurnSample(
        user_input=user_inputs[i],
        retrieved_contexts=split_contexts,
        response=responses[i],
        reference=references[i],
    )
    samples.append(sample)

# Create evaluation dataset and metrics list
ragas_eval_dataset = EvaluationDataset(samples=samples)
ragas_eval_dataset.to_pandas()

ragas_metrics = [context_relevance, faithfulness, answer_relevancy]

# Evaluate
run_config = RunConfig(
    max_retries=10,
    max_wait=60,
    max_workers=5,
    log_tenacity=True,
)

result = evaluate(
    metrics=ragas_metrics,
    dataset=ragas_eval_dataset,
    run_config=run_config,
    batch_size=5,
)

# Save the results
result_df = result.to_pandas()

# Compute cosine similarity between generated answer and reference
cosine_similarities = []

for i in range(len(responses)):
    sim = compute_cosine_similarity(responses[i], references[i])
    cosine_similarities.append(sim)

result_df["cosine_similarity"] = cosine_similarities
result_df["question_id"] = question_ids
result_df["question_type"] = question_types
result_df["retrieval_time"] = retrieval_time
result_df["response_time"] = response_time
result_df["generation_prompt_tokens"] = generation_prompt_tokens
result_df["total_tokens_budgeted"] = total_tokens_budgeted
for key, value in experiment_char.items():
    result_df[key] = value

start_columns = [
    "experiment_id",
    "llm",
    "quantization",
    "temperature",
    "chunk_size_and_overlap",
    "k_retrieved_contexts",
    "question_id",
    "question_type",
]

end_columns = [
    "cosine_similarity",
    "retrieval_time",
    "response_time",
    "generation_prompt_tokens",
    "total_tokens_budgeted",
]

ragas_metric_columns = [
    col for col in result_df.columns
    if col not in start_columns + end_columns
]

final_columns = start_columns + ragas_metric_columns + end_columns
result_df = result_df[final_columns]

result_df.to_csv("output_evaluation_ragas_cosine_sim.csv", index=False)
