"""Origen de la línea: escribe el estado y lo publica por MQTT."""
import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from linea.config import ESTACION, MQTT_HOST, MQTT_PORT, TOPIC_CICLO, TOPIC_CONSIGNA, TOPIC_EVENTO
from linea.estado import escribir
from linea.metricas import Metricas

# Cadencia de la estación: como en una máquina real, no es un reloj perfecto
CICLO_NOMINAL_S = 1.0          # tiempo de ciclo de diseño
VARIACION = 0.10               # ±10 % de una carcasa a otra (material, temperatura, colas)
PROB_MICROPARADA = 1 / 150     # de media, una microparada cada ~150 carcasas (unos 2,5 min)
MICROPARADA_S = (3.0, 8.0)     # duración de una microparada: entre 3 y 8 s sin producir
RAMPA_PIEZAS = 5               # al arrancar, las primeras carcasas van más lentas

# Térmica (M06-03). Sin evento, la deriva es 0 y la estación se comporta como siempre.
CALOR_FALLO = 0.05             # °C que gana el husillo por carcasa con la refrigeración fallando
ENFRIAMIENTO_NIVEL = 0.06      # °C por carcasa que quita cada nivel de refrigeración por encima del 1
RECUPERACION = 0.02            # °C por carcasa que se recupera solo cuando no hay fallo
NIVELES = (1, 3)               # la estación solo acepta niveles 1 a 3: el límite está en la máquina
TERMICA = {"fallo": False, "refrigeracion": 1, "deriva": 0.0}


def on_control(_client, _userdata, msg):
    """Evento simulado (fallo de refrigeración) o consigna de refrigeración, por MQTT."""
    try:
        datos = json.loads(msg.payload.decode())
    except ValueError:
        return
    if msg.topic == TOPIC_EVENTO:
        TERMICA["fallo"] = datos.get("tipo") == "fallo_refrigeracion"
        print(f"sensor: evento {datos.get('tipo')}", flush=True)
    elif msg.topic == TOPIC_CONSIGNA:
        pedido = int(datos.get("refrigeracion", 1))
        TERMICA["refrigeracion"] = min(max(pedido, NIVELES[0]), NIVELES[1])   # se recorta al rango permitido
        print(f"sensor: consigna refrigeración pedida={pedido} aplicada={TERMICA['refrigeracion']}", flush=True)


def actualizar_termica() -> float:
    if TERMICA["fallo"]:
        TERMICA["deriva"] += CALOR_FALLO
    elif TERMICA["deriva"] > 0:
        TERMICA["deriva"] -= RECUPERACION
    TERMICA["deriva"] -= ENFRIAMIENTO_NIVEL * (TERMICA["refrigeracion"] - 1)
    TERMICA["deriva"] = min(max(TERMICA["deriva"], 0.0), 20.0)
    return TERMICA["deriva"]


def espera_ciclo(n: int, azar: random.Random) -> float:
    """Segundos hasta terminar la carcasa n: ciclo variable, rampa de arranque y microparadas."""
    ciclo = CICLO_NOMINAL_S * (1 + azar.uniform(-VARIACION, VARIACION))
    if n <= RAMPA_PIEZAS:
        ciclo *= 1.3                                   # arranque en frío
    if n > RAMPA_PIEZAS and azar.random() < PROB_MICROPARADA:
        ciclo += azar.uniform(*MICROPARADA_S)          # microparada: atasco, sensor de presencia…
    return ciclo


def lectura(n: int) -> dict:
    rng = random.Random(1000 + n)
    temperatura = 61.0 + (n % 7) * 0.35 + rng.uniform(-0.15, 0.15)
    vibracion = 0.22 + (n % 5) * 0.015
    corriente = 4.05 + rng.uniform(-0.08, 0.08)
    return {
        "estacion": ESTACION,
        "pieza_id": f"P{n:04d}",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "temperatura_c": round(temperatura, 2),
        "vibracion_mm_s": round(vibracion, 3),
        "corriente_a": round(corriente, 2),
        "secuencia": n,
    }


def conectar():
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sensor-est01")
    while True:
        try:
            cliente.on_message = on_control
            cliente.on_connect = lambda c, *_: c.subscribe([(TOPIC_EVENTO, 0), (TOPIC_CONSIGNA, 0)])
            cliente.connect(MQTT_HOST, MQTT_PORT, 30)
            cliente.loop_start()
            return cliente
        except Exception as exc:
            print(f"sensor: esperando al broker ({exc})", flush=True)
            time.sleep(1)


def main() -> None:
    # Métricas para Prometheus en http://sensor:9102/metrics
    metricas = Metricas()
    metricas.definir("estacion_piezas_fabricadas_total", "counter", "Carcasas fabricadas desde que arrancó la estación")
    metricas.definir("estacion_temperatura_husillo_celsius", "gauge", "Temperatura del husillo en la última carcasa")
    metricas.definir("estacion_vibracion_mm_s", "gauge", "Vibración en la última carcasa")
    metricas.definir("estacion_corriente_amperios", "gauge", "Corriente del motor en la última carcasa")
    metricas.definir("estacion_tiempo_ciclo_segundos", "gauge", "Tiempo que tardó la última carcasa, desde la anterior")
    metricas.definir("estacion_microparadas_total", "counter", "Microparadas desde que arrancó la estación")
    metricas.definir("estacion_refrigeracion_nivel", "gauge", "Nivel de refrigeración aplicado (1 a 3)")
    metricas.definir("estacion_fallo_refrigeracion", "gauge", "1 si la refrigeración está fallando (evento simulado)")
    metricas.servir(9102)

    cliente = conectar()
    azar = random.Random()               # el ritmo cambia en cada arranque; las medidas, no
    n = 1
    anterior = time.monotonic()
    while True:
        espera = espera_ciclo(n, azar)
        if espera > CICLO_NOMINAL_S * 2:
            metricas.sumar("estacion_microparadas_total")
        time.sleep(espera)               # la carcasa se está mecanizando
        ahora = time.monotonic()
        estado = lectura(n)
        deriva = actualizar_termica()
        if deriva:
            estado["temperatura_c"] = round(estado["temperatura_c"] + deriva, 2)
        estado["tiempo_ciclo_s"] = round(ahora - anterior, 2)
        anterior = ahora
        escribir(estado)
        cliente.publish(TOPIC_CICLO, json.dumps(estado), qos=0)
        metricas.sumar("estacion_piezas_fabricadas_total")
        metricas.poner("estacion_temperatura_husillo_celsius", estado["temperatura_c"])
        metricas.poner("estacion_vibracion_mm_s", estado["vibracion_mm_s"])
        metricas.poner("estacion_corriente_amperios", estado["corriente_a"])
        metricas.poner("estacion_tiempo_ciclo_segundos", estado["tiempo_ciclo_s"])
        metricas.poner("estacion_refrigeracion_nivel", TERMICA["refrigeracion"])
        metricas.poner("estacion_fallo_refrigeracion", int(TERMICA["fallo"]))
        print(f"sensor: {estado['pieza_id']} {estado['temperatura_c']} C", flush=True)
        n += 1


if __name__ == "__main__":
    main()
