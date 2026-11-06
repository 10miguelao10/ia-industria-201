"""Constrúyelo tú (M06-01): tu propio banco de pruebas de inferencia.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m06_01_mi_banco_pruebas.py
"""
import os
import time

import joblib
import numpy as np
import pandas as pd

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
MODELO = "modelo_defecto.joblib"     # el elegido en el M03-03
CICLO_S = 1.0                        # lo que tarda la estación en hacer una carcasa
PIEZAS = 1000                        # cuántas piezas se prueban

# --- PASO 1: el modelo y unas piezas de prueba (ya está hecho) ---------------
ruta = f"/data/{MODELO}"
modelo = joblib.load(ruta)
piezas = pd.read_csv("/data/limpio.csv")[["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]]
piezas = piezas.sample(PIEZAS, replace=True, random_state=0).reset_index(drop=True)
print(f"modelo={MODELO} tipo={type(modelo).__name__} tamaño={os.path.getsize(ruta) / 1024:.1f} KB  piezas de prueba={len(piezas)}")

# --- PASO 2: la primera inferencia y las siguientes ----------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: el peor caso en mil piezas ----------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: una a una o en lote -----------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: el margen frente al ciclo -----------------------------------------
# (pega aquí el bloque del paso 5)
