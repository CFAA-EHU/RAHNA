import pdfplumber
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

def procesar_pdf(config):

    pdf_path = config.get("pdf_path", "")
    paginas_dos_columnas = config.get("paginas_dos_columnas", [])
    paginas_a_excluir = config.get("paginas_a_excluir", set())
    paginas_sin_tablas = config.get("paginas_sin_tablas", set())
    CID_REGEX = re.compile(r'\(cid:\d+\)')

    # Limpiar (cid:x) del texto
    def limpiar_cids(texto: str) -> str:
        return CID_REGEX.sub('', texto).strip()

    def tabla_es_semantica(md):
        # Quitar líneas de separadores markdown
        lineas = [
            l.strip()
            for l in md.splitlines()
            if l.strip() and not re.fullmatch(r'\|?\s*-+\s*\|?', l)
        ]
    
        # Muy pocas líneas -> no es tabla útil
        if len(lineas) < 3:
            return False
    
        texto = " ".join(lineas)
    
        total = len(texto)
        if total == 0:
            return False
    
        espacios = texto.count(" ")
        ratio_espacios = espacios / total
    
        # Demasiados espacios -> layout / gráfico
        if ratio_espacios > 0.3:
            return False
        return True

    # Convertir una tabla a formato markdown
    def tabla_a_markdown(table):
        if not table:
            return ""
        table = [[limpiar_cids(str(c)) if c is not None else "" for c in row] for row in table]
        n_cols = max(len(row) for row in table)
        for row in table:
            while len(row) < n_cols:
                row.append("")
        header = table[0]
        md = []
        md.append("| " + " | ".join(header) + " |")
        md.append("| " + " | ".join(["---"] * n_cols) + " |")
        for row in table[1:]:
            md.append("| " + " | ".join(row) + " |")
        md = "\n".join(md)
        if not tabla_es_semantica(md):
            return ""
        return md

    # Verificar si una palabra está dentro de alguna de las áreas de tablas (si lo están, no hay que meterlas con el texto normal)
    def dentro_de_tabla(word, table_areas):
        for x0, top, x1, bottom in table_areas:
            if x0 <= word['x0'] <= x1 and top <= word['top'] <= bottom:
                return True
        return False

    # Agrupar palabras en líneas basándose en la coordenada 'top'
    # Ordenar primero por top (de arriba a abajo) y luego por x0 (izquierda a derecha)
    # Tolerancia = margen de diferencia permitido entre líneas consecutivas (por si hay ligeras variaciones)
    def agrupar_por_linea(palabras, tolerancia = 2):
        palabras_ordenadas = sorted(palabras, key=lambda w: (w['top'], w['x0']))

        lineas = []
        linea_actual = []
        last_top = None

        for w in palabras_ordenadas:
            if last_top is None or abs(w['top'] - last_top) <= tolerancia:
                linea_actual.append(w)
                last_top = w['top'] if last_top is None else (last_top + w['top']) / 2
            else:
                lineas.append(linea_actual)
                linea_actual = [w]
                last_top = w['top']

        if linea_actual:
            lineas.append(linea_actual)

        return lineas

    # Calcula la densidad de letras y números sobre todos los caracteres de la línea para filtrar ruido
    def densidad_texto_valido(texto):
        if not texto:
            return 0
        validos = sum(c.isalnum() for c in texto)
        return validos / len(texto)

    # Procesar una columna de texto de una página, dados sus límites en el eje x
    def procesar_columna(X_min, X_max):
        elementos = []

        if page_num in paginas_sin_tablas:
            palabras = [w for w in page.extract_words(extra_attrs=["size"])
                if X_min <= w['x0'] <= X_max and X_min <= w['x1'] <= X_max
                and Y_MIN <= w['top'] <= Y_MAX and Y_MIN <= w['bottom'] <= Y_MAX]
        else:
            palabras = [w for w in page.extract_words(extra_attrs=["size"])
                if X_min <= w['x0'] <= X_max and X_min <= w['x1'] <= X_max
                and Y_MIN <= w['top'] <= Y_MAX and Y_MIN <= w['bottom'] <= Y_MAX and not dentro_de_tabla(w, table_areas)]

        lineas = agrupar_por_linea(palabras)
        for l in lineas:
            y_avg = sum(w['top'] for w in l)/len(l)
            size_avg = sum(w['size'] for w in l)/len(l)
            text = " ".join(w['text'] for w in l)
            text = limpiar_cids(text)
            if not text:
                continue
            if densidad_texto_valido(text) < 0.5:
                continue
            elementos.append({"type": "text", "y": y_avg, "text": text, "size": size_avg, "words": l})

        # Agregar tablas que estén en esta columna
        if page_num in paginas_sin_tablas:
            return elementos
        else:
            for t_index, table in enumerate(tables or [], start=1):
                x0, top, x1, bottom = page.find_tables()[t_index-1].bbox
                if (
                    ((x0 >= X_min and x1 <= X_max) or (X_min <= x0 <= X_max) or (X_min <= x1 <= X_max))
                    and ((top >= Y_MIN and bottom <= Y_MAX) or (Y_MIN <= top <= Y_MAX) or (Y_MIN <= bottom <= Y_MAX))
                ):
                    tabla_md = tabla_a_markdown(table)
                    elementos.append({"type": "table", "y": top, "md": f"\n\n{tabla_md}\n"})
            return elementos

    # Obtener los márgenes para una página específica según las reglas definidas en la configuración
    def get_margenes_para_pagina(page_num, rules):
        for rule in rules:
            if rule["condition"](page_num):
                return rule["margins"]
        return {"Y_MIN": 0, "X_MIN": 0, "X_MAX": 600}

    # Variables para detección de títulos
    titulo_threshold = config.get("titulo_threshold", 14)
    min_len_palabra = config.get("min_len_palabra", 3) # Alguna palabra de lo que podría ser un título tiene que tener más de 3 caracteres; si no, es probable que sea ruido y no un título real
    titulo_actual = ""
    en_titulo = False

    regex_subapartado = re.compile(r'^\d+\.\d+(?:\.\d+)?\b')

    # Variables para almacenar los chunks extraídos
    chunks = []
    chunk_paginas = []
    texto_lineas = []

    # Procesar el PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):

            if page_num in paginas_a_excluir:
                continue

            # Definir los límites de la zona de interés para quitar encabezados innecesarios y ruido de los márgenes
            margenes_pagina = get_margenes_para_pagina(page_num, config["margen_rules"])
            Y_MIN = margenes_pagina.get("Y_MIN", 0)
            Y_MAX = margenes_pagina.get("Y_MAX", page.height)
            X_MIN = margenes_pagina.get("X_MIN", 0)
            X_MAX = margenes_pagina.get("X_MAX", page.width)
            
            # Sacar las tablas y sus áreas
            tables = page.extract_tables()
            table_areas = [table.bbox for table in page.find_tables()]

            # Procesar columnas (Hay páginas escritas en dos columnas o en una sola)
            if page_num in paginas_dos_columnas:
                # Columnas separadas
                mid_x = (X_MIN + X_MAX)/2
                elementos_izq = procesar_columna(X_MIN, mid_x)
                elementos_der = procesar_columna(mid_x, X_MAX)

                # Ordenar solo dentro de cada columna por y
                elementos_izq.sort(key=lambda e: e["y"])
                elementos_der.sort(key=lambda e: e["y"])

                # Concatenar columnas
                elementos = elementos_izq + elementos_der
            else:
                elementos = procesar_columna(X_MIN, X_MAX)
                elementos.sort(key=lambda e: e["y"])

            # Construir chunks basados en títulos, texto y tablas
            for elem in elementos:
                if elem["type"] == "text":
                    linea_valida_para_titulo = any(len(w['text']) >= min_len_palabra for w in elem["words"])
                    match = regex_subapartado.match(elem["text"].strip())
                    if (elem["size"] >= titulo_threshold and linea_valida_para_titulo) or match:
                        if texto_lineas:
                            chunks.append({
                                "page": chunk_paginas,
                                "section": titulo_actual,
                                "text": " ".join(texto_lineas)
                            })
                            texto_lineas = []
                            chunk_paginas = []

                        titulo_actual = elem["text"].strip() if not en_titulo else titulo_actual + " - " + elem["text"].strip()
                        en_titulo = True
                    else:
                        en_titulo = False
                        texto_lineas.append(elem["text"])
                        if page_num not in chunk_paginas:
                            chunk_paginas.append(page_num)

                elif elem["type"] == "table":
                    texto_lineas.append(elem["md"])
                    if page_num not in chunk_paginas:
                        chunk_paginas.append(page_num)

    # Añadir el último chunk si queda alguno pendiente
    if texto_lineas:
        chunks.append(
            {
                "page": chunk_paginas,
                "section": titulo_actual,
                "text": " ".join(texto_lineas)
            }
        )

    # Sacar texto por un lado, metadatos por otro
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "page": str(c["page"]),
            "section": c["section"],
            "source": config.get("nombre", "unknown")
        }
        for c in chunks
    ]

    # Limpiar metadatos para que no haya listas o diccionarios (que dan problemas al guardar en Chroma)
    def clean_metadata(meta):
        cleaned = {}
        for k, v in meta.items():
            if isinstance(v, (list, dict)):
                cleaned[k] = str(v)
            else:
                cleaned[k] = v
        return cleaned

    metadatas = [clean_metadata(m) for m in metadatas]

    # Dividir los textos que sean demasiado largos (más de 2000 caracteres)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2000, # Aprox. un token = 4 caracteres (varía dependiendo del idioma) // Límite de tokens para mistral-embed = 8192 // Así aseguramos no pasarnos del límite
        chunk_overlap = 200
    )

    split_texts = []
    split_metas = []

    for text, meta in zip(texts, metadatas):
        subchunks = splitter.split_text(text)
        split_texts.extend(subchunks)
        split_metas.extend([meta] * len(subchunks))
    
    return split_texts, split_metas
