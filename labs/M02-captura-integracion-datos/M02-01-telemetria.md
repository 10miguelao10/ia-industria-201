# M02-01 — Captura de telemetría industrial

[← Página anterior](README.md) · [Siguiente página →](M02-02-protocolos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **telemetría basada en [eventos](../glosario/01-datos-arquitectura.md#evento)**: cómo se entera un sistema de cada pieza en el momento en que ocurre, cómo debe comportarse un consumidor ante el silencio, cómo se distingue con datos una [microparada](../glosario/01-datos-arquitectura.md#tiempo-ciclo) de una parada, y cómo se consigue que quien llegue tarde sepa en qué estado está la máquina.

### Prerrequisitos

- `mosquitto`, `sensor` y `archivador` en marcha.
- Dos terminales abiertas en `infra/` (en VS Code: **Terminal → Split Terminal**).

### Qué está pasando

Hay sistemas que no pueden esperar a consultar el [histórico](../glosario/01-datos-arquitectura.md#historico): quieren enterarse de **cada carcasa en el momento en que termina**. Por ejemplo, un modelo que tiene que dar su [dictamen](../glosario/05-operacion-gobierno.md#dictamen) antes de que salga la siguiente. Para eso se **suscriben** al [broker](../glosario/01-datos-arquitectura.md#broker) y reciben cada registro como un **evento**, sin preguntar a la máquina.

El consumidor también tiene que saber qué hacer cuando **no llega nada**. La estación de EST-01, como una máquina real, tiene **microparadas** de unos segundos (un atasco, un sensor de presencia) y, a veces, **paradas** largas (avería, cambio de herramienta, fin de turno). En los dos casos, lo que el consumidor ve es lo mismo: silencio.

| Situación | Qué ve el consumidor | Qué debería hacer |
|-----------|----------------------|-------------------|
| Producción normal | Un registro cada ~1 s | Procesarlo |
| Microparada | Unos segundos sin registros | Esperar: es normal |
| Parada | Silencio prolongado | Avisar de que la estación está parada |
| Comunicación caída | Silencio prolongado | Avisar de que **no se sabe** cómo está la estación |

El silencio **no es un cero**: no se rellena con lecturas [inventadas](../glosario/04-ia-generativa.md#alucinacion).

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Máquina que publica al terminar cada pieza | `sensor`, [tema](../glosario/01-datos-arquitectura.md#tema) `linea/est01/ciclo` |
| Sistema que consume eventos (modelo, MES, panel) | Tú, con `mosquitto_sub` y los comandos `lab` |
| Estado de la máquina publicado para todos | Un mensaje **[retenido](../glosario/01-datos-arquitectura.md#retenido)** en `linea/est01/estado` (en la mejora) |

### 1 — Escuchar los eventos en crudo

**Qué ocurre:** te suscribes al tema de la estación con el cliente de Mosquitto y ves llegar cinco registros. Es la fuente en crudo: lo mismo que recibe cualquier consumidor.

```bash
# -t: tema   -v: enseña el tema delante   -C 5: sale tras 5 mensajes
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/ciclo' -v -C 5
```

**Resultado esperado** (cambian las piezas, las horas y los valores):

```text
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0051", "ts": "2026-11-06T02:12:29+00:00", "temperatura_c": 61.56, "vibracion_mm_s": 0.235, "corriente_a": 3.99, "secuencia": 51, "tiempo_ciclo_s": 0.99}
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0052", "ts": "2026-11-06T02:12:30+00:00", "temperatura_c": 62.18, "vibracion_mm_s": 0.25, "corriente_a": 4.07, "secuencia": 52, "tiempo_ciclo_s": 0.92}
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0053", "ts": "2026-11-06T02:12:31+00:00", "temperatura_c": 62.48, "vibracion_mm_s": 0.265, "corriente_a": 4.03, "secuencia": 53, "tiempo_ciclo_s": 1.03}
...
```

**Cómo se lee:** cada línea es un evento, «ha terminado una carcasa». Mira `tiempo_ciclo_s`: no es exactamente 1. Los eventos llegan **cuando ocurren**, no a intervalos fijos.

### 2 — Comprobar el evento

**Qué ocurre:** ahora que has visto el flujo, usas un comando de ayuda que se suscribe, se queda con el siguiente registro y comprueba que trae los campos que un consumidor necesita: pieza, hora y medidas.

```bash
# m02-01: espera un registro (hasta 15 s) y comprueba sus campos
docker compose --profile lab run --rm --no-deps lab m02-01
```

📋 Ficha del comando [`m02-01`](../comandos-lab.md#m02-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambian los valores):

```text
{"estacion": "EST-01", "pieza_id": "P0405", "ts": "2026-11-06T02:10:49+00:00", …, "secuencia": 405, "tiempo_ciclo_s": 1.01}
OK m02-01: evento P0405 en linea/est01/ciclo
```

### 3 — Abrir el hueco

**Qué ocurre:** paras la estación y escuchas 3 segundos. Una parada no debe inventar lecturas: el hueco se ve porque no llega nada.

En la **terminal 2**, deja una suscripción abierta para ver el silencio en directo:

```bash
# Terminal 2: escucha sin fin (Ctrl+C para salir)
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/ciclo' -v
```

En la **terminal 1**:

```bash
# Para la estación
docker compose stop sensor

# m02-01-pausa: escucha 3 s; cuadra si NO llega ningún registro
docker compose --profile lab run --rm --no-deps lab m02-01-pausa
```

📋 Ficha del comando [`m02-01-pausa`](../comandos-lab.md#m02-01-pausa).

**Resultado esperado:**

```text
OK m02-01-pausa: hueco: ningún ciclo en 3 s
```

En la terminal 2 las líneas se han detenido. Ni un error ni un cero: nada. **Espera unos 20 segundos** antes del paso siguiente, para que la parada quede en el histórico.

### 4 — Reanudar

**Qué ocurre:** devuelves la estación y compruebas que vuelven los eventos. Los ciclos de la parada no reaparecen: no se fabricaron.

```bash
docker compose start sensor
docker compose --profile lab run --rm --no-deps lab m02-01
```

**Resultado esperado** (la numeración ha vuelto a empezar):

```text
{"estacion": "EST-01", "pieza_id": "P0006", …, "secuencia": 6, "tiempo_ciclo_s": 1.29}
OK m02-01: evento P0006 en linea/est01/ciclo
```

**Cómo se lee:** la estación simulada reinicia su [contador](../glosario/02-observabilidad.md#metrica) al arrancar, y las primeras carcasas tardan más (`tiempo_ciclo_s` por encima de 1,2: la rampa de arranque). Por eso cada evento lleva `ts`: la hora es lo que ordena los registros sin ambigüedad.

## Comprueba tu entendimiento

**Silencio y cero**

Durante el paso 3, ¿qué temperatura «tenía» la estación?

→ Ninguna conocida. No llegó ningún dato. Decir 0 °C, o repetir la última, sería inventar.

## Investiga: ¿cuánto duran los silencios normales?

**Qué ocurre:** para que un consumidor avise de una parada sin dar falsas alarmas en cada microparada, necesita un **umbral de silencio**. No se elige a ojo: se mide en el histórico.

📋 Ficha del comando [`sql`](../comandos-lab.md#sql).

### 1 — Clasificar los tiempos de ciclo

```bash
# Cuántas carcasas tardaron cuánto desde la anterior
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT CASE WHEN tiempo_ciclo_s < 1.2 THEN '1. normal (< 1,2 s)'
              WHEN tiempo_ciclo_s < 2   THEN '2. lento (1,2 - 2 s)'
              WHEN tiempo_ciclo_s < 10  THEN '3. microparada (2 - 10 s)'
              ELSE '4. parada (10 s o más)' END AS tipo,
          COUNT(*) AS carcasas, MIN(tiempo_ciclo_s) AS minimo, MAX(tiempo_ciclo_s) AS maximo
   FROM lecturas WHERE tiempo_ciclo_s IS NOT NULL GROUP BY 1 ORDER BY 1"
```

**Resultado esperado** (cambian los números):

```text
                     tipo  carcasas  minimo  maximo
      1. normal (< 1,2 s)      1699    0.90    1.19
     2. lento (1,2 - 2 s)        23    1.20    1.42
3. microparada (2 - 10 s)        14    4.93    8.76
```

**Cómo se lee:** casi todas las carcasas tardan entre 0,9 y 1,2 s. Las «lentas» son las de la rampa de arranque. Las microparadas duran entre 5 y 9 segundos. **No hay paradas en esta tabla**, aunque paraste la estación en el paso 3: al arrancar, la estación vuelve a contar desde cero, y el `tiempo_ciclo_s` de su primera carcasa no incluye el rato que estuvo parada.

### 2 — Encontrar la parada en el histórico

**Qué ocurre:** la parada no está en el tiempo de ciclo, pero sí en la **hora**: hay un salto entre el último registro antes de parar y el primero después. Lo buscas comparando cada registro con el anterior.

```bash
#   LAG(...) OVER (ORDER BY id): el valor de la fila anterior
#   julianday(): convierte la hora en días, para poder restar
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT anterior AS ultima_antes, pieza_id AS primera_despues, ts,
          ROUND((julianday(ts) - julianday(ts_anterior)) * 86400) AS segundos_sin_datos
   FROM (SELECT id, pieza_id, ts, LAG(pieza_id) OVER (ORDER BY id) AS anterior,
                LAG(ts) OVER (ORDER BY id) AS ts_anterior FROM lecturas)
   WHERE (julianday(ts) - julianday(ts_anterior)) * 86400 > 10 ORDER BY id DESC LIMIT 4"
```

**Resultado esperado:** al menos una fila, la de tu parada del paso 3, con más de 10 segundos sin datos.

**Cómo se lee:** con estas dos consultas puedes poner el umbral con criterio. Las microparadas más largas no pasan de unos 9 segundos, así que un umbral de **15 segundos** no da falsas alarmas en una microparada y avisa de una parada real. Es el mismo valor que usa la [alerta](../glosario/02-observabilidad.md#alerta) `HistoricoSinDatos` del M01-03.

## Experimenta: el suscriptor que llega tarde

**Qué ocurre:** el broker reparte lo que pasa en el momento. ¿Qué recibe alguien que se conecta **después** de que se publique un mensaje? Lo pruebas con un tema de prueba.

```bash
# Publica un aviso normal y, después, se suscribe alguien
docker compose exec mosquitto mosquitto_pub -t 'linea/est01/aviso' -m 'hola'
# -W 3: si en 3 s no llega nada, se rinde
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/aviso' -C 1 -W 3
```

**Resultado esperado:**

```text
Timed out
```

**Cómo se lee:** el aviso se publicó cuando nadie escuchaba y se perdió. Es lo que le pasa a un panel, un modelo o un técnico que se conecta a mitad de turno: no sabe en qué estado está la estación hasta que llegue el siguiente evento. Y si la estación está parada, no llegará ninguno.

## Reto

### 1 — Dos orígenes

Si lanzaras un segundo publicador contra el mismo tema, ¿qué vería el consumidor?

<details>
<summary>Ver solución</summary>

Dos voces en el mismo tema, sin saber cuál es cuál, a menos que cada registro diga de quién es. Por eso el registro lleva `estacion` y `pieza_id`. En planta, cada estación publica en su propio tema (`linea/est01/…`, `linea/est02/…`) y el comodín `linea/#` permite escuchar todas.

</details>

### 2 — ¿Por qué no basta la secuencia?

La secuencia de la estación ya numera los eventos. ¿Por qué no sirve para ordenarlos?

<details>
<summary>Ver solución</summary>

Porque se reinicia con cada arranque (paso 4). Dos eventos de tandas distintas pueden tener la misma secuencia. La hora (`ts`) sigue creciendo pase lo que pase.

</details>

## Mejora: que quien llegue tarde sepa cómo está la estación

**Qué ocurre:** [MQTT](../glosario/01-datos-arquitectura.md#mqtt) tiene una solución para el suscriptor tardío: el mensaje **retenido**. El broker guarda **el último** mensaje retenido de cada tema y se lo entrega al momento a quien se suscriba después. Es la forma habitual de publicar el **estado** de una máquina: no el histórico, solo «cómo está ahora».

```bash
# -r: publica el estado como mensaje RETENIDO
docker compose exec mosquitto mosquitto_pub -r -t 'linea/est01/estado' \
  -m '{"estado": "parada", "motivo": "cambio de herramienta", "desde": "10:15"}'

# Alguien se conecta después… y lo recibe al momento
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/estado' -v -C 1 -W 3
```

**Resultado esperado:**

```text
linea/est01/estado {"estado": "parada", "motivo": "cambio de herramienta", "desde": "10:15"}
```

**Cómo se lee:** aunque te conectaste después, has recibido el estado. Cuando la estación vuelva a producir, publicaría `{"estado": "produciendo"}`, también retenido, y sustituiría al anterior.

Para borrar el mensaje retenido, se publica un mensaje vacío retenido:

```bash
# -n: mensaje vacío; con -r, borra el retenido del tema
docker compose exec mosquitto mosquitto_pub -r -n -t 'linea/est01/estado'
```

En planta se combina con el **mensaje de última voluntad** (*Last Will*): el broker publica un estado como `{"estado": "desconectada"}` en nombre de la máquina si esta se desconecta sin avisar. Así, el silencio deja de ser ambiguo: o la máquina dice que está parada, o el broker dice que se ha perdido la comunicación.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| Siguen llegando ciclos con el sensor parado | No llegaste a pararlo, o hay otro sensor | `docker compose ps` y deja un solo sensor |
| `FALLO: no hay telemetría` | mosquitto o sensor caídos | `docker compose up -d mosquitto sensor` |
| La consulta de paradas no devuelve filas | La parada del paso 3 duró menos de 10 s | Repite el paso 3 esperando unos 20 s antes de reanudar |
| `mosquitto_sub` no sale nunca | Sin `-C` ni `-W`, escucha sin fin | Ctrl+C |

## Conclusiones

### Qué es la telemetría basada en eventos

La máquina publica un registro **cuando pasa algo** (termina una carcasa) y quien lo necesita se suscribe. Es distinto de preguntar periódicamente: el consumidor se entera en el momento, sin cargar a la máquina con consultas.

### Cómo debe comportarse un consumidor

| Requisito | Por qué |
|-----------|---------|
| Comprobar que el evento trae lo necesario | Un registro sin hora o sin pieza no sirve |
| Tratar el silencio como silencio | Rellenar o repetir valores es inventar |
| Ordenar por hora, no por secuencia | La secuencia se reinicia |
| Avisar de parada con un umbral medido | Ni falsas alarmas en microparadas, ni paradas sin avisar |

### Lo que has visto y cómo lo has detectado

| Situación | Cómo la has visto | Qué enseña |
|-----------|-------------------|------------|
| Microparadas de 5–9 s | Investiga 1, tiempo de ciclo | Son normales: el umbral de parada tiene que estar por encima |
| Una parada no está en el tiempo de ciclo | Investiga 1 frente a 2 | Se ve en el salto de la hora entre registros |
| El suscriptor tardío no recibe nada | Experimenta | Sin estado retenido, quien llega no sabe cómo está la máquina |

### Cómo se mejora

| Límite | Mejora |
|--------|--------|
| Silencio ambiguo | Estado de la máquina como mensaje **retenido**, y **última voluntad** para la desconexión |
| Umbral a ojo | Umbral de parada medido en el histórico (15 s aquí) |
| Ordenar por secuencia | Ordenar siempre por `ts` |

### En una frase

> 🔑 Un evento que no llega también es información, y hay que poder saber por qué no llegó: la máquina tiene que decir cómo está, y el consumidor tiene que medir cuánto silencio es normal.
