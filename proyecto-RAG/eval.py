import torch
import pandas as pd
from bert_score import BERTScorer
from tqdm import tqdm

csv_path = "modelo_respuestas.csv"

df = pd.read_csv(csv_path, sep=',')

# Extraemos listas de candidatos y referencias
refs = df['RespuestaCorrecta'].tolist()
cands = df['RespuestaModelo'].tolist()

# Inicializamos BERTScorer con modelo ligero para CPU
# HEMOS TENIDO QUE DESCARGAR EL MODELO Y USARLO EN LOCAL PORQUE SI NO DABA ERROR
scorer = BERTScorer(
    model_type="distilbert-base-multilingual-cased", # path al modelo local
    num_layers=5,
    lang="es",
    device="cuda" if torch.cuda.is_available() else "cpu",
    rescale_with_baseline=False,
    idf=False
)

# Configuramos batch muy pequeño para no saturar la RAM
batch_size = 1
all_f1 = []

# Procesamos los pares en batches
for i in tqdm(range(0, len(cands), batch_size), desc="Evaluando batches"):
    batch_cands = cands[i:i+batch_size]
    batch_refs = refs[i:i+batch_size]
    with torch.no_grad():  # evita guardar gradientes y reduce memoria
        P, R, F1 = scorer.score(batch_cands, batch_refs)
        all_f1.append(F1)

# Guardamos los resultados
df["BERTScore_F1"] = torch.cat(all_f1).tolist()
df.to_csv("resultados_con_bertscore_distilbert_5capas.csv", index=False)