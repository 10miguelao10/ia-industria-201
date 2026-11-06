"""Constrúyelo tú (M06-03): tu propio vigilante predictivo.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m06_03_mi_vigilante_predictivo.py
"""
import time

import httpx
import numpy as np

METRICA = "estacion_temperatura_husillo_celsius"
LIMITE_ALERTA = 70.0           # la alerta TemperaturaHusilloAlta de Prometheus

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
APRENDER_MIN = 10              # minutos de histórico sano con los que se aprende lo normal
VIGILAR_S = 30                 # cuánto vigila en el paso 5
VENTANA_S = 120                # con cuántos segundos recientes se calcula la subida

# --- PASO 1: pedir a Prometheus un tramo de la serie (ya está hecho) ---------
def serie(minutos, metrica=METRICA):
    """Devuelve (segundos, valores) de los últimos `minutos`, una muestra cada 5 s."""
    fin = time.time()
    r = httpx.get("http://prometheus:9090/api/v1/query_range",
                  params={"query": metrica, "start": fin - minutos * 60, "end": fin, "step": 5}, timeout=10)
    puntos = r.json()["data"]["result"][0]["values"]
    return np.array([float(t) for t, _ in puntos]), np.array([float(v) for _, v in puntos])

t, temp = serie(APRENDER_MIN)
print(f"{len(temp)} muestras de los últimos {APRENDER_MIN} min: mínima={temp.min():.2f} media={temp.mean():.2f} máxima={temp.max():.2f} °C")

# --- PASO 2: hasta dónde llega lo normal ---------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: cuánto sube normalmente -------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: prever cuánto falta para la alerta --------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: vigilar en modo asistido ------------------------------------------
# (pega aquí el bloque del paso 5)
