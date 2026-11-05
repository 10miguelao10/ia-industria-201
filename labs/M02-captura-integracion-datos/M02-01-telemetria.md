# M02-01 — Captura de telemetría industrial

[← Página anterior](README.md) · [Siguiente página →](M02-02-protocolos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **telemetría basada en eventos**: cómo se entera un sistema de cada pieza en el momento en que ocurre, cómo debe comportarse un consumidor ante una parada, qué se pierde y cómo se diseña para no perderlo.

### Prerrequisitos

- `mosquitto` y `sensor` en marcha. El panel puede estar parado: aquí no hace falta.
- RAM de este paso: ~0,3 GB.

### Qué está pasando

Hay sistemas que no pueden esperar a consultar el histórico: quieren enterarse de **cada carcasa en el momento en que termina**. Por ejemplo, un modelo que tiene que dar su dictamen antes de que salga la siguiente. Para eso se **suscriben** al broker y reciben cada registro como un evento, sin tener que preguntar a la máquina.

También hay que saber qué pasa cuando la máquina **para** (cambio de herramienta, avería, fin de turno). La estación deja de emitir y llega **silencio**. Un buen consumidor tiene que distinguir «no llega nada» de «llega una temperatura de 0 °C»: un hueco no se rellena con lecturas inventadas.

En este lab te suscribes a los registros, paras la estación para ver el hueco y la vuelves a arrancar.

### 1 — Consumir un ciclo

Vas a suscribirte al tema y quedarte con el primer evento que llegue. Suscribirse es enterarse del evento cuando ocurre, no leer un fichero después.

```bash
# Escucha linea/est01/ciclo hasta recibir un evento y comprueba sus campos
docker compose --profile lab run --rm --no-deps lab m02-01
```

📋 Ficha del comando [`m02-01`](../comandos-lab.md#m02-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

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

📋 Ficha del comando [`m02-01-pausa`](../comandos-lab.md#m02-01-pausa): qué hace, qué lee, qué escribe y cuándo da `OK`.

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

📋 Ficha del comando [`m02-01`](../comandos-lab.md#m02-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

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

## Conclusiones

### Qué es la telemetría basada en eventos

La estación no espera a que le pregunten: publica un registro cada vez que termina una carcasa. Quien necesite enterarse se suscribe al tema y lo recibe en el momento. Es la base para cualquier sistema que tenga que reaccionar pieza a pieza, como un modelo que da su dictamen antes de que salga la siguiente.

### Cómo debe comportarse un consumidor

| Situación | Comportamiento correcto |
|-----------|-------------------------|
| Llega un registro | Comprobar que trae los campos que necesita (pieza, hora, señales) |
| La máquina para | Tratar el silencio como silencio: no inventar lecturas ni confundirlo con un valor 0 |
| La máquina vuelve | Seguir con los registros nuevos, ordenados por su hora |

### Sus límites y cómo los has visto

| Límite | Cómo lo has visto | Qué provoca |
|--------|-------------------|-------------|
| Solo se recibe lo que se publica mientras escuchas | Paso 3: los registros de la parada no reaparecen | Quien se conecta tarde no recibe lo anterior |
| La secuencia de la estación se reinicia | Paso 3: tras arrancar de nuevo, la numeración vuelve a empezar | La secuencia sola no ordena ni identifica |
| Silencio ambiguo | Paso 2: tres segundos sin datos | Sin más contexto, no se sabe si la máquina está parada o si se ha cortado la comunicación |

### Cómo se mejora

- Ordenar y distinguir siempre por la **hora** del registro, no por un contador de la máquina.
- Publicar el **estado de la máquina** (en marcha, parada, avería) además de las medidas, para que el silencio tenga explicación.
- Usar un **latido** o un aviso de desconexión (en MQTT, el mensaje de última voluntad) para distinguir «máquina parada» de «comunicación caída».

### En una frase

> 🔑 Un evento que no llega también es información, y hay que poder saber por qué no llegó.
