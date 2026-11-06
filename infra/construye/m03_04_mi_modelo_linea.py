"""Constrúyelo tú (M03-04): tu propio modelo con los datos de tu línea.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_04_mi_modelo_linea.py
"""
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.tree import DecisionTreeClassifier, export_text

SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a"]   # las que mide la estación en vivo

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
PROFUNDIDAD = 3        # cuántas preguntas seguidas puede hacer el árbol

# --- PASO 1: tu dataset y el corte en el tiempo (ya está hecho) --------------
df = pd.read_csv("/data/dataset_linea.csv").sort_values("ts")    # el de M02-04
corte = int(len(df) * 0.7)
entrenar, examen = df.iloc[:corte], df.iloc[corte:]
print(f"carcasas: entrenar={len(entrenar)} examen={len(examen)} defectuosas_en_examen={int(examen['defecto'].sum())}")

# --- PASO 2: entrenar un árbol y leer sus reglas -------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: examinar el modelo ------------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: ¿cuántos datos hacen falta? ---------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: ¿los fallos son del modelo o de la etiqueta? ----------------------
# (pega aquí el bloque del paso 5)
