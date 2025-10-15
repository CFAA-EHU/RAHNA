
##### kosmos funciona extraer imagenes del pdf ####

'''

##### KOSMOS #####
import fitz  # PyMuPDF para leer PDFs
from PIL import Image
import torch
import os
import json
from transformers import AutoProcessor, AutoModelForVision2Seq

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "microsoft/kosmos-2-patch14-224"

print("🔄 Cargando modelo Kosmos-2...")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

# --- 2. Función para describir imágenes ---
def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    prompt = "Describe this image in detail."
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=200)
    return processor.decode(outputs[0], skip_special_tokens=True)

# --- 3. Extraer imágenes del PDF ---
pdf_path = "/home/leonardo/Descargas/TWIN5 Memoria Tecnica CPP 2024.pdf"  # <-- cambia a tu ruta
doc = fitz.open(pdf_path)

descriptions = []
output_dir = "pdf_images_kosmos"
os.makedirs(output_dir, exist_ok=True)

for i, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        img_path = os.path.join(output_dir, f"page_{i}_img_{img_index}.png")

        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # --- 4. Generar descripción ---
        caption = describe_image(img_path)
        print(f"[Page {i}, Image {img_index}] {caption}")

        descriptions.append({
            "page": i,
            "image_index": img_index,
            "file": img_path,
            "description": caption
        })

# --- 5. Guardar resultados en JSON ---
with open("image_descriptions_kosmos.json", "w", encoding="utf-8") as f:
    json.dump(descriptions, f, indent=4, ensure_ascii=False)

print("✅ Descripciones guardadas en image_descriptions_kosmos.json")


'''


##### KOSMOS - Extraer y Describir Imágenes Únicas de un PDF #####
'''
import fitz  # PyMuPDF para leer PDFs
from PIL import Image
import torch
import os
import json
import hashlib
from transformers import AutoProcessor, AutoModelForVision2Seq

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "microsoft/kosmos-2-patch14-224"

print("🔄 Cargando modelo Kosmos-2...")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

# --- 2. Función para describir imágenes ---
def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    prompt = "Describe this image in detail."
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=500)
    return processor.decode(outputs[0], skip_special_tokens=True)

# --- 3. Función para obtener el hash de una imagen ---
def get_image_hash(image_bytes):
    """Devuelve un hash SHA256 para detectar imágenes duplicadas."""
    return hashlib.sha256(image_bytes).hexdigest()

# --- 4. Extraer imágenes del PDF (sin duplicados) ---
pdf_path = "/home/leonardo/Descargas/TWIN5 Memoria Tecnica CPP 2024.pdf"
doc = fitz.open(pdf_path)

descriptions = []
output_dir = "pdf_images_kosmos"
os.makedirs(output_dir, exist_ok=True)

seen_hashes = set()

print("🔍 Extrayendo imágenes únicas del PDF...")

for i, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        # Verificar duplicados por hash
        img_hash = get_image_hash(image_bytes)
        if img_hash in seen_hashes:
            print(f"⚠️ Imagen duplicada detectada en página {i}, se omite.")
            continue
        seen_hashes.add(img_hash)

        # Guardar imagen única
        img_path = os.path.join(output_dir, f"page_{i}_img_{img_index}.png")
        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # --- 5. Generar descripción ---
        caption = describe_image(img_path)
        print(f"[Page {i}, Image {img_index}] ✅ {caption[:150]}...")

        descriptions.append({
            "page": i,
            "image_index": img_index,
            "file": img_path,
            "description": caption
        })

# --- 6. Guardar resultados en JSON ---
output_json = "image_descriptions_kosmos.json"
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(descriptions, f, indent=4, ensure_ascii=False)

print(f"\n✅ Descripciones guardadas en {output_json}")
print(f"🖼️ Imágenes únicas procesadas: {len(descriptions)}")


'''


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























################################ PRUEBAS ADICIONALES #####################################




'''
import fitz  # PyMuPDF
from PIL import Image
import torch
import os
import json

from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path
from llava.constants import IMAGE_TOKEN_INDEX
from llava.mm_utils import tokenizer_image_token, KeywordsStoppingCriteria
from transformers import StoppingCriteriaList

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "liuhaotian/llava-v1.5-7b"   # puedes cambiar a llava-v1.6-mistral-7b si tu GPU lo aguanta

print("🔄 Cargando modelo LLaVA...")
model_name = get_model_name_from_path(model_path)
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path,
    None,
    model_name,
    device=device
)



def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = image_processor.preprocess(image, return_tensors="pt")["pixel_values"].to(model.device)

    # Prompt siguiendo el formato de LLaVA
    prompt = "USER: <image>\nPlease provide a detailed description of this image.\nASSISTANT:"

    input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt").unsqueeze(0).to(model.device)

    stopping_criteria = StoppingCriteriaList([KeywordsStoppingCriteria(["###"], tokenizer, input_ids)])
    output = model.generate(
        input_ids=input_ids,
        images=image_tensor,
        max_new_tokens=300,
        stopping_criteria=stopping_criteria
    )

    return tokenizer.decode(output[0], skip_special_tokens=True)




# --- 3. Extraer imágenes del PDF ---
pdf_path = "/home/leonardo/Descargas/TWIN5 Memoria Tecnica CPP 2024.pdf"   # <-- cambia a la ruta de tu PDF
doc = fitz.open(pdf_path)

descriptions = []
output_dir = "pdf_images_llava"
os.makedirs(output_dir, exist_ok=True)

for i, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        img_path = os.path.join(output_dir, f"page_{i}_img_{img_index}.png")

        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # --- 4. Generar descripción con LLaVA ---
        caption = describe_image(img_path)
        print(f"[Page {i}, Image {img_index}] {caption}")

        descriptions.append({
            "page": i,
            "image_index": img_index,
            "file": img_path,
            "description": caption
        })

# --- 5. Guardar resultados en JSON ---
with open("image_descriptions_llava.json", "w", encoding="utf-8") as f:
    json.dump(descriptions, f, indent=4, ensure_ascii=False)

print("✅ Descripciones guardadas en image_descriptions_llava.json")


'''












############## CON el repo GIT ############
'''
import fitz  # PyMuPDF
from PIL import Image
import torch
import os
import json

from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, tokenizer_image_token, KeywordsStoppingCriteria
from llava.constants import IMAGE_TOKEN_INDEX
from transformers import StoppingCriteriaList

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "liuhaotian/llava-v1.5-7b"   # o "liuhaotian/llava-v1.6-mistral-7b"
#model_path = "liuhaotian/llava-v1.5-3b"

print("🔄 Cargando modelo LLaVA...")
model_name = get_model_name_from_path(model_path)
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path,
    None,
    model_name,
    device=device,
    load_8bit=True   # 👈 usa quantización 8-bit
)

from types import SimpleNamespace
from llava.eval.run_llava import eval_model

def describe_image(image_path):
    prompt = "Please provide a detailed description of this image."

    args = SimpleNamespace(
        # ---- Rutas del modelo ----
        model_path=model_path,
        model_base=None,
        model_name=model_name,

        # ---- Imagen y prompt ----
        image_file=image_path,
        query=prompt,

        # ---- Configuración de conversación ----
        conv_mode=None,
        sep=",",

        # ---- Parámetros de decodificación ----
        temperature=0.2,
        top_p=1.0,
        num_beams=1,
        max_new_tokens=300,

        # ---- Otros parámetros esperados ----
        do_sample=True,
        max_length=None,
        repetition_penalty=1.0
    )

    output_text = eval_model(args)
    return output_text


# --- 3. Extraer imágenes del PDF ---
pdf_path = "/home/leonardo/Descargas/TWIN5 Memoria Tecnica CPP 2024.pdf"
doc = fitz.open(pdf_path)

descriptions = []
output_dir = "pdf_images_llava"
os.makedirs(output_dir, exist_ok=True)

for i, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        img_path = os.path.join(output_dir, f"page_{i}_img_{img_index}.png")

        with open(img_path, "wb") as f:
            f.write(image_bytes)

        # --- 4. Generar descripción con LLaVA ---
        caption = describe_image(img_path)
        print(f"[Page {i}, Image {img_index}] {caption}")

        descriptions.append({
            "page": i,
            "image_index": img_index,
            "file": img_path,
            "description": caption
        })

# --- 5. Guardar resultados en JSON ---
with open("image_descriptions_llava.json", "w", encoding="utf-8") as f:
    json.dump(descriptions, f, indent=4, ensure_ascii=False)

print("✅ Descripciones guardadas en image_descriptions_llava.json")
'''












############### DESCRIBIR UNA SOLA IMAGEN con KOSMOS ###################
'''
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

# --- 1. Configurar modelo Kosmos-2 ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "microsoft/kosmos-2-patch14-224"

print("🔄 Cargando modelo Kosmos-2...")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

# --- 2. Función para describir imagen ---
def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    prompt = "Describe this image in detail."
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=200)
    description = processor.decode(outputs[0], skip_special_tokens=True)
    return description

# --- 3. Ruta a tu imagen ---
image_path = "/home/leonardo/Descargas/imagen_llm.PNG"  # <-- cambia esto por la ruta de tu imagen

# --- 4. Describir la imagen ---
print(f"🖼️ Analizando imagen: {image_path}")
caption = describe_image(image_path)

print("\n🧾 Descripción generada:")
print(caption)
'''


'''
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "Qwen/Qwen2-VL-7B-Instruct"

print("🔄 Cargando modelo Qwen2-VL (modo conversación)...")

processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    trust_remote_code=True
)

def describe_image(image_path):
    print("a")
    image = Image.open(image_path).convert("RGB")
    print("b")

    # 🧠 Prompt multimodal compatible con Qwen2-VL
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "Describe this image in detail."},
            {"type": "image", "image": image}
        ]}
    ]

    # 🔹 Convierte el mensaje a texto con formato de chat
    text_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    print("c")

    # 🔹 Prepara tensores
    inputs = processor(text=[text_prompt], images=[image], return_tensors="pt").to(device)
    print("d")

    # 🔹 Genera respuesta
    output_ids = model.generate(**inputs, max_new_tokens=300)
    print("e")
    output_text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    print("f")

    return output_text.strip()

# --- 3. Ruta a tu imagen ---
image_path = "/home/leonardo/Descargas/imagen_llm.PNG"

#print(f"🖼️ Analizando imagen: {image_path}")
print("gggg")
caption = describe_image(image_path)

print("\n🧾 Descripción generada:\n", caption)

'''


##### QWEN INFERENCE CLIENT ###########


'''
from huggingface_hub import InferenceClient
import base64
import json

client = InferenceClient("Qwen/Qwen2.5-VL-7B-Instruct")

image_path = "/home/leonardo/Descargas/imagen_llm.jpg"
with open(image_path, "rb") as f:
    image_bytes = f.read()

# codificar en base64
image_b64 = base64.b64encode(image_bytes).decode("utf-8")

# construir el mensaje
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this image in detail."},
            {"type": "file", "mime_type": "image/jpeg", "data": f"data:image/jpeg;base64,{image_b64}"},
        ],
    }
]

# llamada al modelo
response = client.chat_completion(
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    messages=messages,
    max_tokens=400,
)

# mostrar estructura completa
print("\n🔍 Estructura completa de la respuesta:\n")
print(json.dumps(response, indent=2, ensure_ascii=False))

# si quieres solo el texto final:
try:
    print("\n🧾 Descripción generada:\n")
    print(response.choices[0].message["content"])
except Exception as e:
    print("❌ No se pudo extraer el texto:", e)

'''










####### CON LLAVA (pruebas)#####

'''

from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

# --- 1. Configurar modelo LLaVA 1.6 Mistral ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "liuhaotian/llava-v1.6-mistral-7b"   # modelo más potente que Kosmos-2

print("🔄 Cargando modelo LLaVA 1.6 (Mistral 7B)...")
processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForVision2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

# --- 2. Función para describir imagen ---
def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    prompt = (
        "Provide a long, detailed, and technical description of this image, "
        "including all visible objects, context, and relationships between them."
    )
    inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=300)
    description = processor.decode(outputs[0], skip_special_tokens=True)
    return description

# --- 3. Ruta a tu imagen ---
image_path = "/home/leonardo/Descargas/imagen_llm.PNG"  # <-- cambia esto por tu ruta

# --- 4. Describir la imagen ---
print(f"🖼️ Analizando imagen: {image_path}")
caption = describe_image(image_path)

print("\n🧾 Descripción generada:")
print(caption)


'''

####### CON LLAVA (pruebas)#####


'''

import torch
from PIL import Image
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, tokenizer_image_token
from llava.constants import IMAGE_TOKEN_INDEX

# --- 1. Configuración del modelo ---
device = "cuda" if torch.cuda.is_available() else "cpu"
model_path = "liuhaotian/llava-v1.6-mistral-7b"

print("🔄 Cargando modelo LLaVA 1.6 (Mistral 7B)...")
model_name = get_model_name_from_path(model_path)

# Carga el modelo desde el repositorio de LLaVA (NO transformers)
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path, 
    None, 
    model_name, 
    device=device
)

# --- 2. Función para describir una imagen ---
def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")

    # Preprocesar la imagen
    image_tensor = image_processor.preprocess(
        image, return_tensors="pt"
    )["pixel_values"].to(model.device)

    # Prompt compatible con LLaVA
    prompt = "USER: <image>\nDescribe this image in detail.\nASSISTANT:"
    input_ids = tokenizer_image_token(
        prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt"
    ).unsqueeze(0).to(model.device)

    # Generar texto
    output_ids = model.generate(
        input_ids=input_ids,
        images=image_tensor,
        max_new_tokens=200
    )
    caption = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return caption

# --- 3. Ruta a tu imagen ---
image_path = "/home/leonardo/Descargas/imagen_llm.PNG"  # <-- cámbialo si hace falta

print(f"🖼️ Analizando imagen: {image_path}")
caption = describe_image(image_path)

print("\n🧾 Descripción generada:")
print(caption)
'''



####### CON LLAVA (pruebas)#####

'''
from PIL import Image
import torch
from transformers import LlavaProcessor, LlavaForConditionalGeneration

device = "cuda" if torch.cuda.is_available() else "cpu"

# --- Usa el modelo más nuevo, pero el processor de la versión anterior ---
model_id = "liuhaotian/llava-v1.6-mistral-7b"
processor_id = "liuhaotian/llava-v1.5-7b"

print("🔄 Cargando modelo LLaVA 1.6 (Mistral 7B)...")

# Procesador de la v1.5
processor = LlavaProcessor.from_pretrained(processor_id)

# Modelo v1.6
model = LlavaForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    low_cpu_mem_usage=True,
    device_map="auto"
)

def describe_image(image_path):
    image = Image.open(image_path).convert("RGB")
    prompt = "USER: <image>\nPlease describe this image in detail.\nASSISTANT:"
    inputs = processor(prompt, image, return_tensors="pt").to(model.device)
    output = model.generate(**inputs, max_new_tokens=300)
    return processor.decode(output[0], skip_special_tokens=True)

# --- Imagen de prueba ---
image_path = "/home/leonardo/Descargas/imagen_llm.PNG"
print(f"🖼️ Analizando imagen: {image_path}")

caption = describe_image(image_path)
print("\n🧾 Descripción generada:")
print(caption)
'''
