"""Constrúyelo tú (M07-03): tu propio agente de incidencias.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_03_mi_agente_incidencias.py
"""
import json
import re
import time

import httpx

# --- PASO 1: preguntar a Prometheus (ya está hecho) --------------------------
def promql(consulta):
    r = httpx.get("http://prometheus:9090/api/v1/query", params={"query": consulta}, timeout=10)
    return r.json()["data"]["result"]

alertas = httpx.get("http://prometheus:9090/api/v1/alerts", timeout=10).json()["data"]["alerts"]
activas = [a["labels"]["alertname"] for a in alertas if a["state"] == "firing"]
print("alertas activas:", activas or "ninguna")

# --- PASO 2: las herramientas de lectura ---------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: el plan: qué herramientas para cada alerta ------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: la sección del runbook --------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: el diagnóstico y su comprobación ----------------------------------
# (pega aquí el bloque del paso 5)
