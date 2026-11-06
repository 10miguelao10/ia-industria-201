"""Constrúyelo tú (M02-02): tu propia pasarela Modbus → MQTT.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_02_mi_pasarela.py
"""
import json
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pymodbus.client import ModbusTcpClient

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
# El mapa de registros: qué hay en cada uno y por cuánto hay que dividir
MAPA = {0: ("temperatura_c", 10), 1: ("vibracion_mm_s", 1000), 2: ("corriente_a", 100), 3: ("secuencia", 1)}
PERIODO_S = 1.0        # cada cuánto pregunta la pasarela al autómata
LECTURAS = 10          # cuántas veces pregunta en el bucle del paso 6

# --- PASO 1: conectar con el autómata por Modbus (ya está hecho) -------------
plc = ModbusTcpClient("modbus", port=1502)
print("Modbus conectado:", plc.connect())

# --- PASO 2: leer los registros en crudo ---------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: aplicar el mapa de registros --------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: comprobar contra el MQTT de la estación ---------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: publicar en mqtt con nombres y unidades ---------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: el bucle de la pasarela -------------------------------------------
# (pega aquí el bloque del paso 6)
