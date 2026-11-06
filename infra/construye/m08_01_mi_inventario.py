"""Constrúyelo tú (M08-01): tu propio inventario de riesgos.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m08_01_mi_inventario.py

Este programa SOLO LEE: no escribe en el autómata ni publica órdenes.
"""
import asyncio
import socket

import paho.mqtt.client as mqtt
from asyncua import Client
from pymodbus.client import ModbusTcpClient

# --- PASO 1: los servicios de la línea (ya está hecho) -----------------------
SERVICIOS = {"broker MQTT": ("mosquitto", 1883), "autómata Modbus": ("modbus", 1502), "servidor OPC-UA": ("opcua", 4840),
             "modelo de lenguaje": ("llm", 8088), "API de inferencia": ("api", 8000), "Prometheus": ("prometheus", 9090),
             "panel": ("panel", 8501)}
hallazgos = []                                       # (servicio, qué se ha visto, riesgo, medida)
print(f"servicios a revisar: {len(SERVICIOS)}")

# --- PASO 2: ¿quién contesta? --------------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: ¿el broker acepta a cualquiera? -----------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: ¿el autómata se deja leer sin credenciales? -----------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: ¿las variables opc-ua se pueden escribir? -------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: la tabla de riesgos -----------------------------------------------
# (pega aquí el bloque del paso 6)
