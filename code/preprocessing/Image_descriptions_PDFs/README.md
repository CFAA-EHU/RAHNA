# Automatic Extraction and Description of Unique Images from PDF - QWEN2.5-VL

This project uses the multimodal model **[Qwen2.5-VL](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct)** (by Alibaba Cloud) to **extract unique images from a PDF and automatically generate natural-language descriptions**.  
It is designed for analyzing technical, scientific, or industrial documents containing multiple figures and illustrations.

---

## Main Features

-  **Automatic image extraction** from PDF files using `PyMuPDF`.
-  **Duplicate removal** via SHA-256 hashing.
-  **Automatic image captioning** with the **Qwen2.5-VL** model.
-  **Structured JSON export**, including page number, image index, file path, and description.
-  Compatible with both **GPU (CUDA)** and **CPU** execution.

---

## Requirements

### Environment
- Python **>= 3.9**
- GPU with at least **12 GB VRAM** (recommended for `Qwen2.5-VL-3B-Instruct`)
- For `Qwen2.5-VL-7B-Instruct`, **20 GB VRAM or more** is recommended.

### Dependencies
Install the required packages with:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate
pip install pillow pymupdf
pip install qwen-vl-utils
```

---

## Project Structure

```
qwen2.5-vl-pdf-extractor
├── image_descriptions_pdf_qwen.py    # Main script
├── pdf_images_qwen/                  # Folder where extracted images are stored
├── image_descriptions_qwen.json      # JSON file containing generated captions
└── README.md
```

---

## Usage

**Place your PDF file** in the desired location, for example:
```
/home/user/Downloads/document.pdf
```

**Edit the path inside `main.py`:**
```python
pdf_path = "/path/to/your/file.pdf"
```

**Run the script:**
```bash
python main.py
```

The program will:
- Extract all images from the PDF.
- Automatically skip duplicate images.
- Generate detailed captions using **Qwen2.5-VL**.
- Save the results to a structured JSON file.

---

## Example Output (JSON)

```json
[
  {
    "page": 3,
    "image_index": 1,
    "file": "pdf_images_qwen/page_3_img_1.jpg",
    "description": "A bar chart comparing the efficiency of different machine learning models."
  },
  {
    "page": 5,
    "image_index": 0,
    "file": "pdf_images_qwen/page_5_img_0.jpg",
    "description": "A schematic diagram showing a multi-axis milling process."
  }
]
```
