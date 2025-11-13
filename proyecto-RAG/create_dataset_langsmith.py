from langsmith import Client
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

csv_path = "BBDD Preguntas evaluación RAG.csv"
df = pd.read_csv(csv_path, sep=";", encoding='latin1')

ls_client = Client()

examples = [
    {
        "inputs": {"query": row['Pregunta']},
        "outputs": {"answer": row['Respuesta']},
        "metadata": {"tipo": row['Tipo de pregunta']}
    }
    for _, row in df.iterrows()
]

dataset = ls_client.create_dataset("RAG Evaluation Dataset")
ls_client.create_examples(dataset_id=dataset.id, examples=examples)