"""Constrúyelo tú (M02-04): tu propio dataset de la línea.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_04_mi_dataset.py
"""
import sqlite3

import pandas as pd

# --- PASO 1: leer las dos bases (ya está hecho) ------------------------------
def leer(base, consulta):
    with sqlite3.connect(f"file:/data/{base}?mode=ro", uri=True) as con:   # solo lectura
        return pd.read_sql_query(consulta, con)

lecturas = leer("historial.sqlite", "SELECT pieza_id, ts, temperatura_c, vibracion_mm_s, corriente_a FROM lecturas")
inspecciones = leer("calidad.sqlite", "SELECT pieza_id, ts_pieza, defecto FROM inspecciones")
print(f"histórico: {len(lecturas)} registros   calidad: {len(inspecciones)} inspecciones")

# --- PASO 2: unir solo por identificador ---------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: ver una carcasa mal unida -----------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: unir por identificador y hora -------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: guardar el dataset ------------------------------------------------
# (pega aquí el bloque del paso 5)
