"""Constrúyelo tú (M01-02): tus propios indicadores.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m01_02_mis_indicadores.py
"""
import sqlite3
from datetime import datetime, timezone

import pandas as pd

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
VENTANA = 120              # cuántas lecturas recientes miran los indicadores (las mismas que el panel)
MARGEN_C = 70.0            # temperatura a partir de la cual una lectura está fuera de margen
MAX_ANTIGUEDAD_S = 10      # a partir de cuántos segundos sin datos nuevos el dato ya no es actual
CICLO_NOMINAL_S = 1.0      # lo que debería tardar la estación en hacer una carcasa

# --- PASO 1: leer el histórico (ya está hecho) -------------------------------
con = sqlite3.connect("file:/data/historial.sqlite?mode=ro", uri=True)   # solo lectura, como el panel
df = pd.read_sql_query(
    "SELECT pieza_id, ts, temperatura_c, tiempo_ciclo_s FROM lecturas ORDER BY id DESC LIMIT ?",
    con, params=(VENTANA,))
df = df.iloc[::-1]                     # de la más antigua a la más reciente
print(f"lecturas leídas del histórico: {len(df)}")

# --- PASO 2: la última carcasa y cuánto hace que llegó -------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: decidir si el dato está vivo --------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: lecturas fuera de margen ------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: el ritmo de la estación -------------------------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: un informe de una línea -------------------------------------------
# (pega aquí el bloque del paso 6)
