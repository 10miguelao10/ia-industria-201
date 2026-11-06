"""Constrúyelo tú (M07-02): tu propio vigilante de deriva.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_02_mi_vigilante_deriva.py
"""
import sqlite3

import joblib
import pandas as pd

SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
GRADOS = 8.0           # cuánto más caliente trabaja la línea en la simulación del paso 3
TOLERANCIA = 0.10      # cuánto puede cambiar la tasa de «revisar» antes de avisar
DESVIACIONES = 3       # cuántas desviaciones puede moverse la media de una señal antes de avisar

# --- PASO 1: el modelo y los datos con los que se entrenó (ya está hecho) ----
modelo = joblib.load("/data/modelo_defecto.joblib")
df = pd.read_csv("/data/limpio.csv").sort_values("pieza_id")
corte = int(len(df) * 0.7)
entrenamiento, base = df.iloc[:corte], df.iloc[corte:]            # base: el examen, cuando todo iba bien
print(f"entrenamiento={len(entrenamiento)} piezas  base de comparación={len(base)} piezas")

# --- PASO 2: la tasa de revisar de la base -------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: simular que la línea se calienta ----------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: vigilar también los datos de entrada ------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: las dos comprobaciones sobre la línea de ahora --------------------
# (pega aquí el bloque del paso 5)
