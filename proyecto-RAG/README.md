# Archivos .py:
- main.py: Flujo RAG.
- load_db.py: Llama a los métodos para procesar los PDFs y las imágenes de extract_text.py y extract_images.py para conseguir los chunks, crea los embeddings y los guarda en la base de datos vectorial. La extracción de texto de cada PDF se hace un poco diferente en base a la configuraciones definidas en config.py.
- generate_answers.py: Carga las preguntas para la evaluación del CSV, consigue las respuestas del modelo y las guarda en un CSV.
- langsmith_eval.py: Evaluación con LangSmith

# Otros archivos:
- chunks_*.txt: Los .txt que ha generado load_db.py para ver la estructura de los chunks creados.
- modelo_respuestas.csv: El CSV con las respuestas del modelo a las preguntas de evaluación. (Los campos están separados por comas: Tipo, Pregunta, RespuestaCorrecta, RespuestaModelo)
- Pipfile y Pipfile.lock: Archivos de configuración del entorno virtual con todas las dependencias.

- ./mistral-embeddings_db: Base de datos vectorial de Chroma con todos los embeddings.

# Resultados de las evaluaciones:
Hemos evaluado las respuestas poniendole al modelo temperature = 0.1 y temperature = 0.3. Los resultados de la evaluación están en:
- Temperatura = 0.3: modelo_respuestas_completo_t0.3.csv
- Temperatura = 0.1: modelo_respuestas_completo_t0.1.csv

# Notas:
Para usar MistralAIEmbeddings hace falta una API key de MistralAI y la primera vez también me pidió un Access Token de HuggingFace
