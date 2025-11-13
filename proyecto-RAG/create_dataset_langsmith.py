from langsmith import Client
import pandas as pd
from dotenv import load_dotenv
import yaml

# Cargar variables de entorno y configuracion
load_dotenv()

with open("conf.yaml", "r") as f:
    conf = yaml.safe_load(f)

# Leer el archivo CSV con las preguntas y reference outputs y guardarlo en Langsmith
csv_path = conf["paths"]["langsmith"]["csv_path"]
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

dataset = ls_client.create_dataset(conf["variables"]["langsmith"]["dataset_name"])
ls_client.create_examples(dataset_id=dataset.id, examples=examples)