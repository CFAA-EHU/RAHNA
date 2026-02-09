import pandas as pd 
from qwen import get_rag_response
import time
import sys

def main(dataset_csv: str, respuestas_csv: str):
    # Cargar el CSV con las preguntas y respuestas correctas
    df = pd.read_csv(dataset_csv, sep=";", encoding="latin1")
    
    tipos = df["Tipo de pregunta"].tolist()
    preguntas = df["Pregunta"].tolist()
    respuestas_correctas = df["Respuesta"].tolist()
    
    output_rows = []
    
    try:
        # Obtener las respuestas del modelo
        cont = 0
        for tipo, pregunta, respuesta_correcta in zip(tipos, preguntas, respuestas_correctas):
            try:
                respuesta_modelo, contexto_usado, retrieval_time, response_time, generation_prompt_tokens, total_tokens_budgeted = get_rag_response(pregunta, "evaluation")  # Generar respuesta del modelo
    
                # Limpiar la respuesta
                respuesta_modelo = str(respuesta_modelo).replace("\n", " ").replace("\r", " ").strip()
                contexto_str = str(contexto_usado).replace("\n", " ").replace("\r", " ").strip()
        
                output_rows.append({
                    "tipo_pregunta": tipo,
                    "pregunta": pregunta,
                    "respuesta_correcta": respuesta_correcta,
                    "respuesta_modelo": respuesta_modelo,
                    "contexto_usado": contexto_str,
                    "retrieval_time": retrieval_time,
                    "response_time": response_time,
                    "generation_prompt_tokens": generation_prompt_tokens,
                    "total_tokens_budgeted": total_tokens_budgeted,
                })
                cont += 1
                print(f"Pregunta procesada: " + str(cont))
        
            except Exception as e:
                print(f"Error con la pregunta: {pregunta}")
                print(f"    {type(e).__name__}: {e}")
        
                output_rows.append({
                    "pregunta": pregunta,
                    "respuesta_correcta": respuesta_correcta,
                    "respuesta_modelo": f"ERROR: {type(e).__name__}",
                    "contexto_usado": "",
                    "retrieval_time": "",
                    "response_time": "",
                    "generation_prompt_tokens": generation_prompt_tokens,
                    "total_tokens_budgeted": total_tokens_budgeted,
                })
        
                time.sleep(1)
        
        # Guardar resultados en CSV
        output_df = pd.DataFrame(output_rows)
        output_df.to_csv(respuestas_csv, index=False, encoding="utf-8-sig")
        
        print(f"Se han guardado {len(output_rows)} respuestas en {respuestas_csv}")

    except KeyboardInterrupt:
        partial_path = respuestas_csv.replace(".csv", "_parcial.csv")
        output_df = pd.DataFrame(output_rows)
        output_df.to_csv(partial_path, index=False, encoding="utf-8-sig")

        print("\nProceso interrumpido por el usuario.")
        print(f"Resultados parciales guardados en: {partial_path}")

    
if __name__=="__main__":
    if len(sys.argv) < 3:
        print("Uso: python generate_answers.py <path_csv_dataset> <path_csv_respuestas>")
        sys.exit(1)
    dataset_file = sys.argv[1]
    respuestas_path = sys.argv[2]
    main(dataset_file, respuestas_path)
