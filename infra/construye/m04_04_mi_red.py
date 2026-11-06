"""Constrúyelo tú (M04-04): tu propia red neuronal, vuelta a vuelta.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_04_mi_red.py
"""
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.neural_network import MLPClassifier

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
NEURONAS = 64          # neuronas de la capa oculta
VUELTAS = 300          # cuántas pasadas por las fotos de entrenamiento
PARTE = 1.0            # qué parte de las fotos de entrenamiento se usa (1.0 = todas)

# --- PASO 1: las fotos en números y el corte de siempre (ya está hecho) ------
fotos = pd.read_csv("/data/imagenes/manifiesto.csv")
X = np.stack([np.asarray(Image.open(r).convert("L").resize((16, 16)), dtype=np.float32).reshape(-1) / 255.0
              for r in fotos["ruta"]])
y = fotos["defecto"].to_numpy()
buenas, malas = np.where(y == 0)[0], np.where(y == 1)[0]
k = max(1, round(28 * PARTE))                                         # fotos de cada clase para aprender
ent = np.concatenate([buenas[:k], malas[:k]])
exa = np.concatenate([buenas[28:], malas[28:]])                       # el examen del M04-01
print(f"fotos para aprender={len(ent)}  fotos de examen={len(exa)}  números por foto={X.shape[1]}")

# --- PASO 2: crear la red y darle una sola vuelta ------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: entrenar vuelta a vuelta ------------------------------------------
# (pega aquí el bloque del paso 3)
