# Docker

This folder contains the files needed to run the RAG web application in Docker.

## Before You Run

Create or provide these paths inside this `code/Docker` folder.

Required for the app:

- `modelos/modelo`: embedding model folder downloaded from HuggingFace.
- `modelos/qwen_7b`: generator model folder downloaded from HuggingFace.
- `embeddings_db/`: local ChromaDB data with your document embeddings. The ingestion/build scripts used to create it are in `code/preprocessing`. Once created the folder can be moved to this location.

Path names in this README (such as `modelos/modelo` or `modelos/qwen_7b`) match our tested setup. If your folder/model names differ, update the corresponding references in `rag_code.py` and Docker configuration.

Required only if you use the `nginx` service from `docker-compose.yml`:

- `nginx/default.conf`
- `certs/`

Runtime data folder:

- `docker_data/` is mounted to `/data` in the container and stores `valoraciones.csv`.

## What Each File Is For

- `Dockerfile`: builds the application image.
- `docker-compose.yml`: starts `rag-app` and optionally `nginx`.
- `app_flask.py`: Flask entry point and API routes.
- `rag/rag_code.py`: RAG pipeline implementation (model loading, retrieval, generation).
- `rag/templates` and `rag/static`: web UI assets copied into the image.

## How It Works

1. Docker builds the image from `Dockerfile`.
2. At build time, `app_flask.py` and `rag/` are copied into `/app`.
3. At runtime, compose mounts:
   - `./modelos` -> `/app/modelos`
   - `./docker_data` -> `/data`
4. `app_flask.py` imports `get_rag_response` from `rag_code.py`.
5. `rag_code.py` loads:
   - embeddings model from `/app/modelos/modelo`
   - generator model from `/app/modelos/qwen_7b`
   - vector DB from `./embeddings_db`

## If You Want To Use Other Models

`rag_code.py` is tailored to one tested setup (Qwen-based generation + current embedding model path).

To switch models, you must edit `rag_code.py` to match the new model requirements, especially:

- local model paths
- tokenizer/model loading code
- quantization settings (`BitsAndBytesConfig`)
- any generation parameters if needed

## Notes

- The app runs on port `8080` inside the container.
- `nginx` forwards external traffic to the app when proxy config and certs are present.
- This setup is designed for NVIDIA/CUDA environments (CUDA base image + 8-bit model loading in `rag_code.py`).