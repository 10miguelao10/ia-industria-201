"""Constrúyelo tú (M02-01): tu propio consumidor de telemetría.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_01_mi_consumidor.py
"""
import json
import time
from collections import Counter

import paho.mqtt.client as mqtt

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
DURACION_S = 30                              # cuánto tiempo escucha
TEMA_ESTADO = "linea/est01/consumidor/estado"   # donde tu consumidor anuncia si está vivo
DESPEDIRSE = False                           # False = se cae sin avisar; True = se desconecta bien

# --- PASO 1: conectar con el broker (ya está hecho) --------------------------
recibidos = []                               # (tema, hora de llegada, contenido) de cada mensaje

def al_recibir(cliente, datos, mensaje):
    recibidos.append((mensaje.topic, time.time(), mensaje.payload.decode()))

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_message = al_recibir
cliente.connect("mosquitto", 1883)
print("conectado al broker mosquitto:1883")

# --- PASO 2: escuchar todos los temas de la estación ---------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: medir los silencios entre carcasas --------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: anunciarse con un testamento --------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: caerse sin despedirse ---------------------------------------------
# (pega aquí el bloque del paso 5)
