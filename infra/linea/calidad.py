"""Inspección de calidad simulada: revisa cada carcasa y apunta si salió defectuosa.

Vive aparte del histórico, como el sistema de calidad de una planta: tiene su propia base
de datos (calidad.sqlite). El criterio real de defecto no lo conoce nadie de la línea: el
alumno tiene que descubrirlo con los datos.
"""
import json
import random
import sqlite3
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from linea.config import DATA, MQTT_HOST, MQTT_PORT, TOPIC_CICLO

ERROR_INSPECCION = 0.03   # 3 % de las inspecciones se equivocan: así es una inspección real


def conectar_db() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATA / "calidad.sqlite")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS inspecciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pieza_id TEXT,        -- la pieza inspeccionada
            ts_pieza TEXT,        -- la hora a la que la fabricó la estación
            defecto INTEGER,      -- 1 = defectuosa, 0 = buena
            ts_inspeccion TEXT    -- cuándo se inspeccionó
        )
        """
    )
    con.commit()
    return con


def dictamen(ciclo: dict) -> int:
    # Criterio oculto: la carcasa sale mala cuando vibra mucho y el motor hace más esfuerzo
    defecto = ciclo["vibracion_mm_s"] >= 0.265 and ciclo["corriente_a"] > 4.08
    # La inspección no es perfecta: a veces se equivoca
    rng = random.Random(f"{ciclo['pieza_id']}-{ciclo['ts']}")
    if rng.random() < ERROR_INSPECCION:
        defecto = not defecto
    return int(defecto)


def main() -> None:
    con = conectar_db()

    def on_message(_client, _userdata, msg):
        ciclo = json.loads(msg.payload.decode())
        con.execute(
            "INSERT INTO inspecciones (pieza_id, ts_pieza, defecto, ts_inspeccion) VALUES (?, ?, ?, ?)",
            (ciclo["pieza_id"], ciclo["ts"], dictamen(ciclo), datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        con.commit()

    def on_connect(client, _userdata, _flags, _reason, _properties):
        client.subscribe(TOPIC_CICLO)       # se vuelve a suscribir tras cada reconexión
        print("calidad: inspeccionando", TOPIC_CICLO, flush=True)

    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="calidad-est01")
    cliente.on_message = on_message
    cliente.on_connect = on_connect
    while True:
        try:
            cliente.connect(MQTT_HOST, MQTT_PORT, 30)
            break
        except Exception as exc:
            print(f"calidad: esperando al broker ({exc})", flush=True)
            time.sleep(1)
    cliente.loop_forever()


if __name__ == "__main__":
    main()
