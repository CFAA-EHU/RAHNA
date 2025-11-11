# QWEN2.5-VL — Automatic Extraction and Description of Unique Images from PDF

This project uses the multimodal model **[Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)** (by Alibaba Cloud) to **extract unique images from a PDF and automatically generate natural-language descriptions**.  
It is designed for analyzing technical, scientific, or industrial documents containing multiple figures and illustrations.

---

## Main Features

- 📄 **Automatic image extraction** from PDF files using `PyMuPDF`.
- 🔍 **Duplicate removal** via SHA-256 hashing.
- 🧠 **Automatic image captioning** with the **Qwen2.5-VL** model.
- 💾 **Structured JSON export**, including page number, image index, file path, and description.
- ⚙️ Compatible with both **GPU (CUDA)** and **CPU** execution.

---

## Requirements

### Environment
- Python **>= 3.9**
- GPU with at least **12 GB VRAM** (recommended for `Qwen2.5-VL-3B`)
- For `Qwen2.5-VL-7B-Instruct`, **20 GB VRAM or more** is recommended.

### Dependencies
Install the required packages with:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate
pip install pillow pymupdf
pip install qwen-vl-utils
