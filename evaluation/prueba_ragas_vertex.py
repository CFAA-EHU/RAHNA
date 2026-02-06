import vertexai
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_vertexai import VertexAI, VertexAIEmbeddings
from ragas import evaluate
from ragas.metrics import ContextRelevance, Faithfulness, AnswerRelevancy, FactualCorrectness
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
import pandas as pd
from dotenv import load_dotenv
import re
import os
from ragas.run_config import RunConfig

load_dotenv()

# Initialize VertexAI and models
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
vertexai.init(project=PROJECT_ID, location=LOCATION)

evaluator_llm = LangchainLLMWrapper(VertexAI(model_name="gemini-2.5-pro"))

evaluator_embeddings = LangchainEmbeddingsWrapper(VertexAIEmbeddings(model_name="gemini-embedding-001"))

# Define evaluation metrics
context_relevance = ContextRelevance(llm=evaluator_llm)
faithfulness = Faithfulness(llm=evaluator_llm)
answer_relevancy = AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)
factual_correctness = FactualCorrectness(llm=evaluator_llm)

# CSV file with the answers given by the RAG system
df = pd.read_csv("respuestas_modelo_prueba_parcial.csv")

user_inputs = df['pregunta'].tolist()
retrieved_contexts = df['contexto_usado'].tolist()
responses = df['respuesta_modelo'].tolist()
references = df['respuesta_correcta'].tolist()

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

ragas_metrics = [context_relevance, faithfulness, answer_relevancy, factual_correctness]

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
result_df.to_csv("output_prueba_ragas.csv", index=False)
