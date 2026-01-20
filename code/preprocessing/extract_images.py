import re

# Sacar las descripciones de las imágenes del txt
def procesar_descripciones_imagenes(config):
    txt_path = config.get("imgs_txt_path")
    if(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            contenido = f.read()

        # Dividir por bloques (cada descripción)
        bloques = re.split(r"\n(?=Sección: )", contenido.strip())
    
        textos = []
        metadatos = []
    
        for bloque in bloques:
            seccion = re.search(r"Sección:\s*(.*)", bloque)
            pagina = re.search(r"Página:\s*(\d+)", bloque)
            titulo = re.search(r"Título:\s*(.*)", bloque)
            descripcion = re.search(r"Descripción:\s*(.*)", bloque, re.DOTALL)
    
            if not descripcion:
                continue
    
            texto = descripcion.group(1).strip()
    
            meta = {
                "page": pagina.group(1) if pagina else "N/A",
                "title": titulo.group(1).strip() if titulo else "",
                "section": seccion.group(1).strip() if seccion else "",
                "source": config.get("nombre", "unknown")
            }
    
            textos.append(texto)
            metadatos.append(meta)
    
        return textos, metadatos
    else:
        return [], []
