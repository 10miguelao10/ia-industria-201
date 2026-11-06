"""Constrúyelo tú (M04-02): tu propio localizador de rayones.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_02_mi_detector_rayones.py
"""
import numpy as np
import pandas as pd
from PIL import Image

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
BRILLO_RAYON = 230      # brillo medio de fila a partir del cual se considera que hay un rayón
MAS_LUZ = 0             # cuánto se aclara una foto buena en el paso 6 (0 = luz normal)

# --- PASO 1: las fotos, en números (ya está hecho) ---------------------------
fotos = pd.read_csv("/data/imagenes/manifiesto.csv")   # ruta, defecto y fila real del rayón (y)
malas = fotos[fotos["defecto"] == 1]
buenas = fotos[fotos["defecto"] == 0]

def a_numeros(ruta):
    return np.asarray(Image.open(ruta).convert("L"), dtype=np.float32)    # 64 × 64, de 0 a 255

foto = a_numeros(malas["ruta"].iloc[0])
print(f"foto defectuosa: {foto.shape[0]} filas × {foto.shape[1]} columnas; el rayón está en la fila {int(malas['y'].iloc[0])}")

# --- PASO 2: el brillo de cada fila --------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: localizar el rayón y comprobarlo ----------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: decidir si hay rayón ----------------------------------------------
# (pega aquí el bloque del paso 4)
