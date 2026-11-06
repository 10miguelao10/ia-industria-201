"""Constrúyelo tú (M03-01): tu propio modelo de predicción de defectos.

Ejecútalo desde infra/ con:
    docker compose --profile lab run --rm --no-deps lab construye m03_01_mi_modelo.py

Cada paso marcado con «TU PARTE» lanza NotImplementedError hasta que lo completes.
Borra esa línea `raise` y escribe tu código en su lugar.
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix

# --- Decisiones tuyas -------------------------------------------------------
# Señales que usará el modelo. Disponibles antes de la inspección:
#   "temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"
SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]

COSTE_ESCAPADO = 500   # € por defecto que llega al cliente
COSTE_REVISION = 5     # € por revisar a mano una pieza buena

# --- 1. Cargar los datos (hecho) ---------------------------------------------
df = pd.read_csv("/data/limpio.csv")   # en tu equipo: infra/data/limpio.csv
print(f"piezas={len(df)} defectuosas={int(df['defecto'].sum())} señales={SENALES}")

# --- 2. Partir en pasado y futuro (TU PARTE) ---------------------------------
# Ordena por pieza_id y corta en el 70 %: entrenar = las antiguas, examen = las recientes.
raise NotImplementedError("paso 2: crea las tablas «entrenar» y «examen»")
print(f"entrenar={len(entrenar)} examen={len(examen)} defectos_en_examen={int(examen['defecto'].sum())}")

# --- 3. Entrenar (TU PARTE) --------------------------------------------------
# Crea una LogisticRegression con class_weight="balanced" y max_iter=400,
# y entrénala con las SENALES de «entrenar» para predecir la columna "defecto".
raise NotImplementedError("paso 3: crea y entrena «modelo»")

# --- 4. Evaluar con un umbral (TU PARTE) -------------------------------------
# Escribe la función: recibe un umbral y devuelve (tp, fp, fn, tn) sobre «examen».
# Pista: modelo.predict_proba(...)[:, 1] da la probabilidad de defecto de cada pieza.
def evaluar(umbral):
    raise NotImplementedError("paso 4: completa la función evaluar(umbral)")

tp, fp, fn, tn = evaluar(0.5)
print(f"umbral 0.5 -> encontrados={tp} escapados={fn} falsas_alarmas={fp} correctas={tn}")

# --- 5. Elegir el umbral por lo que cuesta (TU PARTE) -------------------------
# Recorre los umbrales de 0.05 a 0.95 (de 0.05 en 0.05), calcula el coste de cada uno
# con COSTE_ESCAPADO y COSTE_REVISION, imprime una fila por umbral y quédate con el más barato.
# Calcula también lo que costaría NO tener modelo: revisar todas las piezas buenas a mano.
raise NotImplementedError("paso 5: busca el umbral más barato y compáralo con revisar todo")
