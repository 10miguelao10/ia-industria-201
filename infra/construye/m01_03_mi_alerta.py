"""Constrúyelo tú (M01-03): tu propia alerta.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m01_03_mi_alerta.py
"""
import time

import httpx

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
LIMITE_S = 15          # segundos sin guardar a partir de los que algo va mal
FOR_S = 5              # cuánto tiempo seguido tiene que cumplirse para disparar
VIGILAR_S = 30         # cuánto tiempo vigila tu alerta
CADA_S = 5             # cada cuánto pregunta (lo mismo que tarda Prometheus en recoger)

# --- PASO 1: preguntar a Prometheus (ya está hecho) --------------------------
def consultar(promql):
    """Hace una consulta PromQL instantánea y devuelve [(etiquetas, valor), ...]."""
    r = httpx.get("http://prometheus:9090/api/v1/query", params={"query": promql}, timeout=5)
    return [(s["metric"], float(s["value"][1])) for s in r.json()["data"]["result"]]

print("servicios que vigila Prometheus:", consultar("count(up)"))

# --- PASO 2: ¿está vivo cada servicio? -----------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: ¿hace su trabajo el archivador? -----------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: ¿se pierden carcasas? ---------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: una alerta con su tiempo for --------------------------------------
# (pega aquí el bloque del paso 5)
