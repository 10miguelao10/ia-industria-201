"""Constrúyelo tú (M01-01): tu propio vigilante del flujo de datos.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m01_01_mi_vigilante.py
"""
import json
import time

import paho.mqtt.client as mqtt

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
DURACION_S = 20        # cuántos segundos escucha el vigilante
PARADA_S = 2.5         # segundos sin carcasa a partir de los que se considera una parada

# --- PASO 1: conectar con el broker (ya está hecho) --------------------------
recibidos = []                                   # cada registro que llegue, con la hora a la que llegó

def al_recibir(cliente, datos, mensaje):
    """La llama paho cada vez que llega un mensaje de un tema al que estás suscrito."""
    recibidos.append((time.time(), json.loads(mensaje.payload)))

cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_message = al_recibir
cliente.connect("mosquitto", 1883)               # el broker, por su nombre en la red de Docker
print("conectado al broker mosquitto:1883")

# --- PASO 2: suscribirse y escuchar --------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: leer los campos de cada registro ----------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: detectar carcasas que faltan y reinicios --------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: distinguir una parada de una pérdida ------------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: conciliar lo fabricado con lo recibido ----------------------------
# (pega aquí el bloque del paso 6)
