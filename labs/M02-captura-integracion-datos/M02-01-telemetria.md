# M02-01 — Captura de telemetría industrial

[← Página anterior](README.md) · [Siguiente página →](M02-02-protocolos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Consumes la telemetría de EST-01 como eventos y ves el hueco cuando el origen se detiene.

### Prerrequisitos

- `mosquitto` y `sensor` en marcha. El panel puede estar parado: aquí no hace falta.
- RAM de este paso: ~0,3 GB.

### En qué consiste

El sensor publica un JSON por segundo en el tema `linea/est01/ciclo`: pieza, hora, temperatura, vibración y corriente. Tú te suscribes. No se entrena nada.

### 1 — Consumir un ciclo

Vas a suscribirte al tema y quedarte con el primer evento que llegue. Suscribirse es enterarse del evento cuando ocurre, no leer un fichero después.

```bash
# Escucha linea/est01/ciclo hasta recibir un evento y comprueba sus campos
docker compose --profile lab run --rm --no-deps lab m02-01
```

**Resultado esperado** (cambian la pieza, la hora y los valores):

```text
{"estacion": "EST-01", "pieza_id": "P0014", "ts": "2026-11-04T17:13:29+00:00", "temperatura_c": 61.0, "vibracion_mm_s": 0.28, "corriente_a": 4.01, "secuencia": 14}
OK m02-01: evento P0014 en linea/est01/ciclo
```

Puedes ver el mismo flujo con el cliente de Mosquitto, sin pasar por el laboratorio:

```bash
# -v enseña el tema; -C 3 sale tras 3 mensajes
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/#' -v -C 3
```

### 2 — Abrir el hueco

Vas a parar el origen y escuchar 3 segundos. Una parada no debe inventar lecturas: el hueco se ve porque no llega nada.

```bash
# Para el sensor
docker compose stop sensor

# Escucha 3 s; el paso cuadra si NO llega ningún ciclo
docker compose --profile lab run --rm --no-deps lab m02-01-pausa
```

**Resultado esperado:**

```text
OK m02-01-pausa: hueco: ningún ciclo en 3 s
```

### 3 — Reanudar

Vas a devolver el origen y comprobar que vuelven los eventos. Los ciclos perdidos durante la pausa no reaparecen.

```bash
docker compose start sensor
docker compose --profile lab run --rm --no-deps lab m02-01
```

**Resultado esperado:**

```text
{"estacion": "EST-01", "pieza_id": "P0006", "ts": "2026-11-04T17:13:51+00:00", "temperatura_c": 63.05, "vibracion_mm_s": 0.235, "corriente_a": 4.01, "secuencia": 6}
OK m02-01: evento P0006 en linea/est01/ciclo
```

Fíjate en `secuencia`: el sensor simulado reinicia su contador al arrancar. Por eso cada evento lleva también `ts`, la hora, para ordenar sin ambigüedad.

## Comprueba tu entendimiento

**Tema**

¿De qué tema sale el JSON?

→ `linea/est01/ciclo`.

## Reto

### 1 — Dos orígenes

Si lanzaras un segundo publicador contra el mismo tema, ¿qué vería el consumidor?

<details>
<summary>Ver solución</summary>

Dos voces en el mismo tema, sin saber cuál es cuál. Por eso el ciclo lleva `estacion` y `pieza_id`.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| siguen llegando ciclos con el sensor parado | no llegaste a pararlo, o hay otro sensor | `docker compose ps` y deja un solo sensor |
| `FALLO: no hay telemetría` | mosquitto o sensor caídos | `docker compose up -d mosquitto sensor` |
