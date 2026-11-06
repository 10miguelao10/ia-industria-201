"""Constrúyelo tú (M06-02): tu propio publicador de dictámenes.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m06_02_mi_dictamen.py
"""
import hashlib
import json
import time
from datetime import datetime, timezone

import joblib
import pandas as pd
import paho.mqtt.client as mqtt
from pymodbus.client import ModbusTcpClient

from linea.estado import leer                      # la última carcasa que publicó la estación

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
UMBRAL = 0.5            # probabilidad a partir de la cual el dictamen es «revisar»
PRESION_BAR = 6.0       # la presión no viaja en el registro de la estación: se supone la nominal
CARCASAS = 5            # cuántas carcasas seguidas dictamina en el paso 6

# --- PASO 1: el modelo y sus credenciales (ya está hecho) --------------------
RUTA = "/data/modelo_defecto.joblib"
modelo = joblib.load(RUTA)
VERSION = open("/data/VERSION").read().strip()
HUELLA = hashlib.sha256(open(RUTA, "rb").read()).hexdigest()[:12]
print(f"modelo {VERSION}, huella {HUELLA}")

# --- PASO 2: decidir sobre la carcasa actual -----------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: publicarlo para el automatismo ------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: comprobar que el paro no se ha tocado -----------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: dictaminar carcasas seguidas --------------------------------------
# (pega aquí el bloque del paso 5)
