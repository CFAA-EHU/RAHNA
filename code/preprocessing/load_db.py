import time
from extract_text import procesar_pdf
from extract_images import procesar_descripciones_imagenes
import pdf_pages_config as config
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

curr_config = config.config_manual_6

# Procesar el PDF y extraer chunks y metadatos
split_texts, split_metas = procesar_pdf(curr_config)
img_texts, img_metas = procesar_descripciones_imagenes(curr_config)

combined_texts = split_texts + img_texts
combined_metas = split_metas + img_metas

# Guardar los chunks en un archivo .txt para revisarlos
txt_path = curr_config.get("txt_path")
with open(txt_path, "w", encoding="utf-8") as f:
    for text, meta in zip(combined_texts, combined_metas):
        title = meta.get("title", "-")
        f.write(f"\n\n--- Páginas: {meta['page']} | Sección: {meta['section']} | Título: {title} ---\n")
        f.write(text)

# Crear la base vectorial o acceder a ella si ya existe
embeddings = HuggingFaceEmbeddings(
    model_name="/home/niturregi/proyecto/modelos/modelo",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"batch_size": 4, "normalize_embeddings": True},
    cache_folder="./hf_cache",
)

vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="./embeddings_db"
)

# Almacenar los textos y metadatos en la base vectorial en batches y con pausas para evitar sobrecarga
BATCH_SIZE = 5
PAUSE_SEC = 1

def batcher(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

for text_batch, meta_batch in zip(batcher(combined_texts, BATCH_SIZE),
                                  batcher(combined_metas, BATCH_SIZE)):
    try:
        vectorstore.add_texts(texts=text_batch, metadatas=meta_batch)
        print(f"Batch de {len(text_batch)} textos añadido correctamente.")
    except Exception as e:
        print(f"Error al añadir batch: {e}")
    time.sleep(PAUSE_SEC)

print(f"Base vectorial creada con {len(combined_texts)} chunks")

# Imprimir algunos chunks para verificar que se están almacenando correctamente
all_docs = vectorstore.get()['documents']
all_metas = vectorstore.get()['metadatas']

print("=== Primeros 5 chunks ===")
for text, meta in zip(all_docs[:5], all_metas[:5]):
    title = meta.get("title", "-")
    print(f"\n--- Páginas: {meta['page']} | Sección: {meta['section']} | Título: {title} ---\n")
    print(text)

print("\n=== Últimos 5 chunks ===")
for text, meta in zip(all_docs[-5:], all_metas[-5:]):
    title = meta.get("title", "-")
    print(f"\n--- Páginas: {meta['page']} | Sección: {meta['section']} | Título: {title} ---\n")
    print(text)
