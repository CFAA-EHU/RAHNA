# Configuraciones específicas para procesar cada manual

config_manual_1 = {
    "pdf_path": "data/Manual_1.pdf", #Path al PDF
    "imgs_txt_path": "", #Path al .txt que contiene las descripciones de las imágenes de ese PDF (Si no tiene, dejar string vacío)
    "txt_path": "debug/chunks_manual_1.txt", #Path en el que crear el .txt en el que se escriben los chunks para ver como se han generado y depurar
    "nombre": "Manual 1", #Nombre del PDF, para los metadatos de cada chunk
    "paginas_dos_columnas": [2, 12, 13, 14], #Páginas que están escritas a dos columnas
    "paginas_a_excluir": {1} | set(range(3, 11)), #Páginas que no queremos procesar
    "paginas_sin_tablas": {2}, #Páginas sin tablas (A veces, identifica tablas donde no las hay. Se pueden poner aquí esas páginas para asegurar que no se tratan como tablas)
    "titulo_threshold": 14, #Límite de tamaño de letra a partir del cual un texto se identifica como título
    "min_len_palabra": 3, #Número de letras que algo tiene que tener para identificarse como palabra de un título (Hay algunas letras grandes en algunos diagramas que se leen como título por su tamaño pero no lo son)
    "margen_rules": [ #Reglas para definir donde empiezan y terminan los márgenes de las páginas (p) (Para no coger ruido de los márgenes, logos...)
        {
            "condition": lambda p: p == 2, #Página = 2 (márgenes un poco diferentes)
            "margins": {"Y_MIN": 0, "X_MIN": 0, "X_MAX": 600}
        },
        {
            "condition": lambda p: p % 2 == 0, #Página par
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True, #Página impar
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_2 = {
    "pdf_path": "data/manual_2.pdf",
    "imgs_txt_path": "",
    "txt_path": "debug/chunks_manual_2.txt",
    "nombre": "Manual 2",
    "paginas_dos_columnas": [2],
    "paginas_a_excluir": {1, 3, 4},
    "paginas_sin_tablas": {2},
    "titulo_threshold": 14,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p == 2,
            "margins": {"Y_MIN": 0, "X_MIN": 0, "X_MAX": 600}
        },
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 30, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 30, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_3 = {
    "pdf_path": "data/manual_3.pdf",
    "imgs_txt_path": "data/manual_3_imgs.txt",
    "txt_path": "debug/chunks_manual_3.txt",
    "nombre": "Manual 3",
    "paginas_dos_columnas": [],
    "paginas_a_excluir": {1, 6, 7, 8} | {81} | set(range(89, 103)) | set(range(104, 110)) | {115} | set(range(118, 170)) | set(range(179, 188)),
    "paginas_sin_tablas": {
        i for i in range(1, 187 + 1)
        if i not in ({2, 24, 76, 77, 80, 82, 83, 84} | set(range(89, 188)))
    },
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p <= 88,
            "margins": {"Y_MIN": 120, "Y_MAX": 790, "X_MIN": 0, "X_MAX": 600}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 15, "Y_MAX": 780, "X_MIN": 15, "X_MAX": 1200}
        }
    ]
}

config_manual_4 = {
    "pdf_path": "data/new_docs/manual_4.pdf",
    "imgs_txt_path": "data/new_docs/manual_4_imgs.txt",
    "txt_path": "debug/chunks_manual_4.txt",
    "nombre": "Manual 4",
    "paginas_dos_columnas": [2],
    "paginas_a_excluir": {1, 3, 4, 5, 6, 86, 142, 170, 212, 222, 244, 270, 472, 473, 474},
    "paginas_sin_tablas": {2},
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p == 2,
            "margins": {"Y_MIN": 0, "X_MIN": 0, "X_MAX": 600}
        },
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 30, "Y_MAX": 790, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 30, "Y_MAX": 790, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_5 = {
    "pdf_path": "data/new_docs/manual_5.pdf",
    "imgs_txt_path": "data/new_docs/manual_5_images.txt",
    "txt_path": "debug/chunks_manual_5.txt",
    "nombre": "Manual 5",
    "paginas_dos_columnas": [4, 5, 6, 51],
    "paginas_a_excluir": {1, 2, 3, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 44, 45, 46, 47, 48, 49, 50, 52},
    "paginas_sin_tablas": {},
    "titulo_threshold": 14,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p == 7,
            "margins": {"Y_MIN": 350, "Y_MAX": 800}
        },
        {
            "condition": lambda p: p in (8, 13),
            "margins": {"Y_MIN": 280, "Y_MAX": 800}
        },
        {
            "condition": lambda p: p == 10,
            "margins": {"Y_MIN": 195, "Y_MAX": 800}
        },
        {
            "condition": lambda p: p == 26,
            "margins": {"Y_MIN": 50, "Y_MAX": 200}
        },
        {
            "condition": lambda p: p == 29,
            "margins": {"Y_MIN": 50, "Y_MAX": 160}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 50, "Y_MAX": 800}
        }
    ]
}

config_manual_6 = {
    "pdf_path": "data/new_docs/manual_6.pdf",
    "imgs_txt_path": "data/new_docs/manual_6_images.txt",
    "txt_path": "debug/chunks_manual_6.txt",
    "nombre": "Manual 6",
    "paginas_dos_columnas": [],
    "paginas_a_excluir": set(range(1, 21)) | set(range(167, 171)),
    "paginas_sin_tablas": {},
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_7 = {
    "pdf_path": "data/new_docs/manual_7.pdf",
    "imgs_txt_path": "data/new_docs/manual_7_images.txt",
    "txt_path": "debug/chunks_manual_7.txt",
    "nombre": "Manual 7",
    "paginas_dos_columnas": [],
    "paginas_a_excluir": set(range(1, 25)) | set(range(504, 507)),
    "paginas_sin_tablas": {},
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_8 = {
    "pdf_path": "data/new_docs/manual_8.pdf",
    "imgs_txt_path": "data/new_docs/manual_8_images.txt",
    "txt_path": "debug/chunks_manual_8.txt",
    "nombre": "Manual 8",
    "paginas_dos_columnas": [],
    "paginas_a_excluir": set(range(1, 31)) | set(range(763, 767)),
    "paginas_sin_tablas": {},
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_9 = {
    "pdf_path": "data/new_docs/manual_9.pdf",
    "imgs_txt_path": "data/new_docs/manual_9_imgs.txt",
    "txt_path": "debug/chunks_manual_9.txt",
    "nombre": "Manual 9",
    "paginas_dos_columnas": [],
    "paginas_a_excluir": set(range(1, 27)) | set(range(319, 323)),
    "paginas_sin_tablas": {},
    "titulo_threshold": 13,
    "min_len_palabra": 3,
    "margen_rules": [
        {
            "condition": lambda p: p % 2 == 0,
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}
