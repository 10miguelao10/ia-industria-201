"""Constrúyelo tú (M07-01): tu propio servicio de inferencia.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_01_mi_servicio.py
"""
import hashlib
from datetime import datetime, timezone

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# --- PASO 1: el modelo que va a servir (ya está hecho) -----------------------
RUTA = "/data/modelo_defecto.joblib"
MODELO = joblib.load(RUTA)
VERSION = open("/data/VERSION").read().strip()                       # la etiqueta que alguien escribió
HUELLA = hashlib.sha256(open(RUTA, "rb").read()).hexdigest()[:12]     # calculada del propio fichero
print(f"servirá el modelo {VERSION} con huella {HUELLA}")

# --- PASO 2: el contrato de entrada --------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: la salud del servicio ---------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: el dictamen -------------------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: llamarlo como un cliente ------------------------------------------
# (pega aquí el bloque del paso 5)
