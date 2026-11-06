"""Constrúyelo tú (M04-03): tu propio puesto de inspección.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_03_mi_puesto.py
"""
import csv
import hashlib
from collections import Counter
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from PIL import Image

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
UMBRAL = 0.5          # probabilidad de defecto a partir de la cual la carcasa va a revisión
DUDA = 0.0            # ± alrededor del umbral en que decide una persona (0 = sin zona de duda)

# --- PASO 1: el modelo y las carcasas que llegan (ya está hecho) -------------
RUTA_MODELO = "/data/modelo_vision.joblib"            # el que guardó lab m04-01
modelo = joblib.load(RUTA_MODELO)
fotos = pd.read_csv("/data/imagenes/manifiesto.csv")
llegan = pd.concat([fotos[fotos.defecto == 0].iloc[28:], fotos[fotos.defecto == 1].iloc[28:]])  # el examen del M04-01
print(f"carcasas que llegan al puesto: {len(llegan)} ({int(llegan.defecto.sum())} con rayón, que el puesto no sabe)")

# --- PASO 2: la probabilidad de cada carcasa -----------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: decidir con el umbral y la zona de duda ---------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: escribir el registro ----------------------------------------------
# (pega aquí el bloque del paso 4)
