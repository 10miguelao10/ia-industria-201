"""Constrúyelo tú (M08-02): tu propia auditoría del rastro de dictámenes.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m08_02_mi_auditoria.py
"""
import hashlib
import json
from collections import Counter

# --- PASO 1: leer el rastro (ya está hecho) ----------------------------------
lineas = open("/data/predicciones.jsonl", encoding="utf-8").read().splitlines()   # infra/data/predicciones.jsonl
rastro = [json.loads(l) for l in lineas]
print(f"dictámenes en el rastro: {len(rastro)}  primero: {rastro[0]['ts']}  último: {rastro[-1]['ts']}")

# --- PASO 2: resumir por modelo ------------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: comprobar contra el modelo instalado ------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: buscar líneas incompletas -----------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: sellar el rastro --------------------------------------------------
# (pega aquí el bloque del paso 5)
