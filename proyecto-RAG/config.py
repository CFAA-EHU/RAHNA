# Configuraciones específicas para procesar cada manual

config_manual_1 = {
    "nombre": "Manual_1",
    "paginas_dos_columnas": [2, 12, 13, 14],
    "paginas_a_excluir": {1} | set(range(3, 11)),
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
            "margins": {"Y_MIN": 40, "X_MIN": 100, "X_MAX": 535}
        },
        {
            "condition": lambda p: True,
            "margins": {"Y_MIN": 40, "X_MIN": 65, "X_MAX": 490}
        }
    ]
}

config_manual_2 = {
    "nombre": "manual_2",
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
    "nombre": "manual_3",
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