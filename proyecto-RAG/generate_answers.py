import pandas as pd
from main import get_rag_response
import csv
import time

# Cargar el CSV con las preguntas y respuestas correctas
df = pd.read_csv("BBDD Preguntas evaluación RAG.csv", sep=";", encoding="latin1")

tipos = df["Tipo de pregunta"].tolist()
preguntas = df["Pregunta"].tolist()
respuestas_correctas = df["Respuesta"].tolist()

output_rows = []

# Obtener las respuestas del modelo
for tipo, pregunta, respuesta_correcta in zip(tipos, preguntas, respuestas_correctas):
    try:
        respuesta_modelo = get_rag_response(pregunta)  # Generar respuesta del modelo
        output_rows.append([tipo, pregunta, respuesta_correcta, respuesta_modelo])
        time.sleep(1.5)  # Esperar 1 segundo entre preguntas para evitar sobrecarga
        print(f"Pregunta procesada")
    except Exception as e:
        # Capturar cualquier error y continuar con la siguiente pregunta
        print(f"⚠ Error con la pregunta: {pregunta}")
        print(f"    {type(e).__name__}: {e}")

        output_rows.append([tipo, pregunta, respuesta_correcta, f"ERROR: {type(e).__name__}"])

        time.sleep(2)

# Guardar en CSV
with open("modelo_respuestas.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Tipo", "Pregunta", "RespuestaCorrecta", "RespuestaModelo"])
    writer.writerows(output_rows)