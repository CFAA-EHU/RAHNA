import time
from extract_text import procesar_pdf
from extract_images import procesar_descripciones_imagenes
import config
from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings
import yaml

# Cargar configuracion
with open("conf.yaml", "r") as f:
    conf = yaml.safe_load(f)

# Rutas de archivos a procesar
pdf_path = conf["paths"]["load_db"]["pdf_path"]
imgs_txt_path = conf["paths"]["load_db"]["imgs_txt_path"]
txt_path = conf["paths"]["load_db"]["txt_path"]

# Procesar el PDF y extraer chunks y metadatos
split_texts, split_metas = procesar_pdf(pdf_path, config.config_manual_1)

if (imgs_txt_path):
    img_texts, img_metas = procesar_descripciones_imagenes(imgs_txt_path, config.config_manual_1)
else:
    img_texts, img_metas = [], []

combined_texts = split_texts + img_texts
combined_metas = split_metas + img_metas

# Guardar los chunks en un archivo .txt para revisarlos
with open(txt_path, "w", encoding="utf-8") as f:
    for text, meta in zip(combined_texts, combined_metas):
        title = meta.get("title", "-")
        f.write(f"\n\n--- Páginas: {meta['page']} | Sección: {meta['section']} | Título: {title} ---\n")
        f.write(text)

# Crear la base vectorial o acceder a ella si ya existe
embeddings = MistralAIEmbeddings() # mistral-embed

vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory=conf["paths"]["db"]["persist_directory"]
)

# Almacenar los textos y metadatos en la base vectorial en batches y con pausas para evitar sobrecarga
BATCH_SIZE = 5
PAUSE_SEC = 1
MAX_RETRIES = 3

def batcher(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

for text_batch, meta_batch in zip(batcher(combined_texts, BATCH_SIZE),
                                  batcher(combined_metas, BATCH_SIZE)):
    for attempt in range(MAX_RETRIES):
        try:
            vectorstore.add_texts(texts=text_batch, metadatas=meta_batch)
            print(f"Batch de {len(text_batch)} textos añadido correctamente.")
            break
        except Exception as e:
            print(f"Error al añadir batch: {e}")
        time.sleep(PAUSE_SEC)
    else:
        print(f"No se pudo añadir el batch después de {MAX_RETRIES} intentos. Continuando con el siguiente batch.")

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