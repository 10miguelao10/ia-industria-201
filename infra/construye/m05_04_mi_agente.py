"""Constrúyelo tú (M05-04): tu propio agente con herramientas.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_04_mi_agente.py
"""
import json
from datetime import datetime, timezone

import httpx

from linea.estado import leer                      # el último estado que publicó la estación

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
PETICION = "¿Cómo está la estación EST-01 ahora?"

# --- PASO 1: la caja de herramientas (ya está hecho) -------------------------
def leer_estacion():
    """Lee la última carcasa de EST-01: pieza, temperatura, vibración y corriente. Solo lectura."""
    e = leer()
    return {"pieza": e["pieza_id"], "temperatura_c": e["temperatura_c"],
            "vibracion_mm_s": e["vibracion_mm_s"], "corriente_a": e["corriente_a"]}

HERRAMIENTAS = {"leer_estacion": leer_estacion}     # TODAS de lectura: no hay ninguna que escriba
print("herramientas del agente:", list(HERRAMIENTAS))

# --- PASO 2: decidir qué herramienta hace falta --------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: usar la herramienta y dejar traza ---------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: redactar la respuesta con el dato ---------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: comprobar que ha copiado bien el dato -----------------------------
# (pega aquí el bloque del paso 5)
