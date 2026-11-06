"""Constrúyelo tú (M03-01): tu propio modelo de predicción de defectos.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_01_mi_modelo.py
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
# Señales que usará el modelo. Las cuatro las mide la estación durante el ciclo.
SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]

COSTE_ESCAPADO = 500   # € por defecto que llega al cliente
COSTE_REVISION = 5     # € por revisar a mano una pieza buena

# --- PASO 1: cargar los datos (ya está hecho) --------------------------------
df = pd.read_csv("/data/limpio.csv")   # en tu equipo: infra/data/limpio.csv
print(f"piezas={len(df)} defectuosas={int(df['defecto'].sum())} señales={SENALES}")

# --- PASO 2: partir en pasado y futuro ---------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: entrenar --------------------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: ver qué probabilidad da a cada pieza ----------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: decidir con un umbral y contar los aciertos y errores -----------
# (pega aquí el bloque del paso 5)

# --- PASO 6: elegir el umbral por lo que cuesta -------------------------------
# (pega aquí el bloque del paso 6)
