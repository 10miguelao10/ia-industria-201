"""Constrúyelo tú (M03-03): tu propia comparación de modelos.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_03_mi_comparacion.py
"""
import json

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]
VERSION = "defecto-0.2"     # el nombre con el que quedará el elegido

# --- PASO 1: los datos y el corte de siempre (ya está hecho) -----------------
df = pd.read_csv("/data/limpio.csv").sort_values("pieza_id")
corte = int(len(df) * 0.7)
entrenar, examen = df.iloc[:corte], df.iloc[corte:]     # el mismo corte del M03-01

def examinar(modelo):
    """Entrena con el pasado, examina con el futuro y devuelve encontrados, escapados y falsas alarmas."""
    modelo.fit(entrenar[SENALES], entrenar["defecto"])
    tn, fp, fn, tp = confusion_matrix(examen["defecto"], modelo.predict(examen[SENALES]), labels=[0, 1]).ravel()
    return {"recall": tp / (tp + fn), "fpr": fp / (fp + tn), "encontrados": int(tp), "falsas": int(fp)}

print(f"entrenar={len(entrenar)} examen={len(examen)} defectos_en_examen={int(examen['defecto'].sum())}")

# --- PASO 2: escribir la regla antes de mirar ----------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: los candidatos ----------------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: examinarlos con la misma vara -------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: elegir con la regla y guardar -------------------------------------
# (pega aquí el bloque del paso 5)
