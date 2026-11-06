"""Constrúyelo tú (M04-01): tu propio clasificador de imágenes.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_01_mi_clasificador.py
"""
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.linear_model import LogisticRegression

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
LADO = 16          # la foto se reduce a LADO × LADO puntos antes de dársela al modelo

# --- PASO 1: las fotos (ya está hecho) ---------------------------------------
fotos = pd.read_csv("/data/imagenes/manifiesto.csv")     # una fila por foto: ruta y si es defectuosa
primera = Image.open(fotos["ruta"][0])
print(f"fotos={len(fotos)} defectuosas={int(fotos['defecto'].sum())}  tamaño de cada foto={primera.size}")

# --- PASO 2: convertir una foto en números -------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: preparar todas las fotos ------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: entrenar y examinar -----------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: ver dónde se fija el modelo ---------------------------------------
# (pega aquí el bloque del paso 5)
