##### QWEN2.5-VL - Extraer y describir imágenes únicas de un PDF #####

import fitz  # PyMuPDF para leer PDFs
from PIL import Image
import torch
import os
import json
import hashlib
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "Qwen/Qwen2.5-VL-3B-Instruct"  # también puedes usar "Qwen/Qwen2.5-VL-7B-Instruct" si tienes VRAM suficiente (~20GB)

print("🔄 Cargando modelo Qwen2.5-VL...")
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto",
)
model = torch.compile(model)
processor = AutoProcessor.from_pretrained(model_id)

# --- 2. Función para describir una imagen ---
def describe_image(image_path):
    """Genera una descripción detallada de la imagen usando Qwen2.5-VL."""
    image = Image.open(image_path).reduce(2).convert("RGB")
    temp_path = "temp_for_qwen.jpg"
    image.save(temp_path)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": f"file://{temp_path}"},
                {"type": "text", "text": "Describe this image"},
            ],
        }
    ]

    # Procesamiento del input
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    # Generación
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=500, eos_token_id=processor.tokenizer.eos_token_id)

    # Decodificación
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    return output_text.strip()

# --- 3. Hash para eliminar imágenes duplicadas ---
def get_image_hash(image_bytes):
    return hashlib.sha256(image_bytes).hexdigest()

# --- 4. Extraer imágenes únicas del PDF ---
pdf_path = "/home/leonardo/Descargas/ttr.pdf"
output_dir = "pdf_images_qwen"
os.makedirs(output_dir, exist_ok=True)

doc = fitz.open(pdf_path)
descriptions = []
seen_hashes = set()

print("🔍 Extrayendo imágenes únicas del PDF...")

for i, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        # Evitar duplicados
        img_hash = get_image_hash(image_bytes)
        if img_hash in seen_hashes:
            print(f"⚠️ Imagen duplicada detectada en página {i}, se omite.")
            continue
        seen_hashes.add(img_hash)

        # Guardar imagen
        img_path = os.path.join(output_dir, f"page_{i}_img_{img_index}.jpg")
        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # --- 5. Generar descripción ---
        print(f"\n🧠 Describiendo imagen de la página {i}, índice {img_index}...")
        caption = describe_image(img_path)
        print(f"✅ Descripción: {caption[:200]}...\n")

        descriptions.append({
            "page": i,
            "image_index": img_index,
            "file": img_path,
            "description": caption
        })

# --- 6. Guardar resultados en JSON ---
output_json = "image_descriptions_qwen.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(descriptions, f, indent=4, ensure_ascii=False)

print(f"\n✅ Descripciones guardadas en {output_json}")
print(f"🖼️ Imágenes únicas procesadas: {len(descriptions)}")







################################ QWEN descripcion imagen funciona #####################################
'''

from PIL import Image
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

# --- 1. Configuración ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "Qwen/Qwen2.5-VL-3B-Instruct"   # más ligero, si tienes GPU de <8GB

print("🔄 Cargando modelo Qwen2.5-VL...")
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto",
)
model = torch.compile(model)

processor = AutoProcessor.from_pretrained(model_id)

# --- 2. Cargar tu imagen local ---
image_path = "/home/leonardo/Descargas/imagen_llm.jpg"  # ⚡ cámbiala por tu imagen
image = Image.open(image_path).reduce(2).convert("RGB")
image.save("temp.jpg")  # se usa como referencia local

# --- 3. Crear mensaje de entrada ---
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": f"file://temp.jpg"},
            {"type": "text", "text": "Describe this image in detail."},
        ],
    }
]

# --- 4. Procesar texto e imagen ---
text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
image_inputs, video_inputs = process_vision_info(messages)

inputs = processor(
    text=[text],
    images=image_inputs,
    videos=video_inputs,
    padding=True,
    return_tensors="pt",
).to(model.device)

# --- 5. Generar descripción ---
print("🧠 Generando descripción...")
with torch.no_grad():
    #generated_ids = model.generate(**inputs, max_new_tokens=200)
    generated_ids = model.generate(**inputs, max_new_tokens=500, eos_token_id=processor.tokenizer.eos_token_id)




# --- 6. Decodificar resultado ---
generated_ids_trimmed = [
    out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
]
output_text = processor.batch_decode(
    generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
)[0]

print("\n🧾 Descripción generada:\n")
print(output_text)


'''
