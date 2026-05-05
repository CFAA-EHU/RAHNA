This folder contains the scripts that extract content from source PDFs, produce text chunks and metadata, and populate a local Chroma vector store.

## Files and purpose

- `Image_descriptions_PDFs/` — Helper scripts used to generate text descriptions for images contained in PDFs (produces the `.txt` files that `extract_images.py` parses).
- `extract_images.py` — Reads an images-descriptions `.txt` (produced by the tools in `Image_descriptions_PDFs`) and returns two lists: image texts and their metadata (page, title, section, source).
- `extract_text.py` — Core PDF parser that opens a PDF with `pdfplumber`, detects columns and tables, groups words into lines, identifies titles/sections by size and regex, converts tables to Markdown when appropriate, and returns `split_texts` and `split_metas` ready for embedding and ingestion.
- `load_db.py` — Orchestrator: calls `extract_text.procesar_pdf` and `extract_images.procesar_descripciones_imagenes`, concatenates results, writes a debug `.txt` of chunks, builds a `HuggingFaceEmbeddings` instance and a `Chroma` vectorstore with `persist_directory="./embeddings_db"`, and stores the chunks in batches.
- `pdf_pages_config.py` — Collection of per-PDF configuration dictionaries (paths, page ranges, margins, parsing rules, title thresholds, etc.). Each config object defines how `extract_text.py` should process a specific PDF.