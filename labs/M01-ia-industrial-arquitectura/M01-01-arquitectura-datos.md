# M01-01 — Arquitectura básica de datos

[← Página anterior](README.md) · [Siguiente página →](M01-02-visualizacion-supervision.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es una **arquitectura de datos industrial**: qué piezas la forman y cómo viaja el dato por ellas, cómo debe ser para que sirva a la IA, cómo se detectan sus debilidades y cómo se perfecciona.

Para eso trabajas con una arquitectura mínima, la de la estación EST-01: primero la entiendes, y después la pones a prueba hasta encontrar dónde se rompe.

### Prerrequisitos

- Docker en marcha y el puesto comprobado (`./comprobar-puesto.sh` dio `PUESTO_OK`).
- RAM: unos 0,5 GB para mosquitto, sensor y archivador.
- [Qué es cada contenedor](../../infra/README.md).

### Qué está pasando en la línea

**EST-01 es una estación de mecanizado de [carcasas](../glosario/01-datos-arquitectura.md#pieza).** Sale una carcasa terminada **aproximadamente cada segundo**: la primera es `P0001`, la segunda `P0002`, y así sucesivamente. Como en una máquina real, no es un reloj: cada carcasa tarda un poco más o un poco menos, las primeras tras arrancar van más lentas y, de vez en cuando, la estación se detiene unos segundos (una **[microparada](../glosario/01-datos-arquitectura.md#tiempo-ciclo)**: un atasco, un sensor de presencia, el operario retirando una pieza).

Mientras la máquina trabaja cada carcasa, tres sensores la vigilan:

| Sensor | Qué mide | Valor habitual |
|--------|----------|----------------|
| Temperatura del husillo | Lo caliente que está el eje que gira la herramienta | 61–63 °C |
| Vibración | Cuánto tiembla la máquina | 0,22–0,28 mm/s |
| Corriente del motor | Cuánto esfuerzo hace | ~4 A |

Al terminar cada carcasa, la estación emite su **registro**: qué pieza es, a qué hora terminó, cuánto tardó y cuánto marcaron los tres sensores. El registro sale **cuando la carcasa termina**, no a intervalos fijos: es un **[evento](../glosario/01-datos-arquitectura.md#evento)**. Ese registro tiene que llegar al **[histórico](../glosario/01-datos-arquitectura.md#historico) de la planta** para que, más adelante, alguien pueda consultarlo, entrenar un modelo con él o explicar una reclamación.

El camino del registro tiene tres tramos:

```
 ORIGEN                            TRANSPORTE                ALMACÉN
 la estación emite el registro ──▶ el broker lo reparte ──▶ el archivador lo guarda
 (sensor)                          (mosquitto)               (archivador → historial.sqlite)
```

- **El [broker](../glosario/01-datos-arquitectura.md#broker) no guarda nada.** Recibe el registro y entrega una copia a todos los que estén suscritos. Si nadie lo escucha en ese momento, se pierde.
- **El archivador es quien registra.** Está suscrito a los registros de EST-01 y escribe cada uno como una fila en la base de datos del histórico.

| En planta | En este laboratorio |
|-----------|---------------------|
| Máquina, sensores, PLC y una [pasarela](../glosario/01-datos-arquitectura.md#pasarela) que publica | Un solo contenedor, `sensor`, que simula todo eso |
| Broker [MQTT](../glosario/01-datos-arquitectura.md#mqtt) en un servidor de planta | Contenedor `mosquitto` |
| Histórico (historian, base de datos de MES) | Contenedor `archivador` y el fichero `infra/data/historial.sqlite` |

**Cómo es el histórico por dentro.** El archivador guarda cada registro como una fila de la tabla `lecturas` de `historial.sqlite`:

```sql
CREATE TABLE lecturas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,  -- número de fila; lo pone la base de datos y nunca se repite
    pieza_id       TEXT,   -- identificador que puso la estación (P0001…)
    ts             TEXT,   -- hora en que terminó la carcasa
    temperatura_c  REAL,   -- las tres medidas del ciclo
    vibracion_mm_s REAL,
    corriente_a    REAL,
    payload        TEXT    -- el mensaje MQTT original, tal cual llegó
)
```

Por cada registro que recibe, el archivador añade una fila. No comprueba si ese `pieza_id` ya existía: guarda todo lo que llega.

Esta arquitectura es **la mínima para que el dato se mueva**. Los pasos te enseñan cómo funciona; los retos, dónde se rompe. Todavía no hay ningún modelo de IA.

### 1 — Arrancar la estación y el camino de los registros

**Qué ocurre:** enciendes la estación (empieza a fabricar y a emitir un registro por carcasa), el broker que los reparte y el archivador que los guarda. Desde ese momento el histórico empieza a llenarse.

```bash
cd infra

# Arranca en segundo plano (-d) la estación, el broker y el archivador
docker compose up -d mosquitto sensor archivador

# Comprueba que los tres están en marcha
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
```

**Resultado esperado:**

```text
SERVICE      STATUS
archivador   Up 3 seconds
mosquitto    Up 3 seconds
sensor       Up 3 seconds
```

Si alguno no aparece, ese tramo no existe y los registros no llegan al histórico.

### 2 — Mirar las tres fuentes por separado

**Qué ocurre:** antes de usar ninguna comprobación automática, miras con tus ojos lo que guarda cada tramo. Son tres sitios distintos.

**El origen: lo último que fabricó la estación.** Abre en VS Code el fichero `infra/data/estado.json`.

**Resultado esperado** (cambia con cada carcasa; si lo tienes abierto, VS Code lo recarga solo):

```json
{"estacion": "EST-01", "pieza_id": "P0056", "ts": "2026-11-06T02:12:34+00:00", "temperatura_c": 60.88, "vibracion_mm_s": 0.235, "corriente_a": 4.11, "secuencia": 56, "tiempo_ciclo_s": 0.9}
```

**Qué es:** la estación reescribe este fichero con cada carcasa que termina. Solo guarda **la última**: es su «pantalla», no su memoria.

**El transporte: lo que pasa por el broker.** El broker no guarda nada en disco, así que no hay fichero que abrir: para verlo hay que escuchar. `mosquitto_sub` es el cliente de Mosquitto que se suscribe a un tema y enseña lo que llega:

```bash
# Escucha el tema de la estación; -C 3 sale tras 3 mensajes
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/ciclo' -C 3
```

**Resultado esperado:** tres registros, uno por carcasa, con el mismo formato que `estado.json`. Mira `ts` y `tiempo_ciclo_s`: no llegan exactamente cada segundo.

**El almacén: el histórico.** Abre en VS Code el fichero `infra/data/historial.sqlite`.

**Qué ves:** caracteres extraños, o un aviso de que es un fichero binario. Empieza por `SQLite format 3`. No es texto: es una **base de datos SQLite** guardada en un fichero, y para leerla hace falta un programa que entienda SQL.

Para eso el curso trae un comando de ayuda: **`lab sql`** lanza una consulta SQL contra el histórico, en solo lectura, y enseña el resultado como tabla. Cuenta cuántos registros hay:

```bash
docker compose --profile lab run --rm --no-deps lab sql "SELECT COUNT(*) AS registros FROM lecturas"
```

**Resultado esperado** (cambia el número):

```text
 registros
        27
```

> La primera vez que lanzas `lab`, Docker prepara su imagen y verás líneas `#1 … DONE` antes de la salida. Es normal y no se repite.

📋 Ficha del comando [`sql`](../comandos-lab.md#sql). La usarás mucho en el curso.

### 3 — Comprobarlo todo de una vez

**Qué ocurre:** ahora que has visto las tres fuentes, usas un comando de ayuda que hace la comprobación completa de una vez, como haría un técnico: cuenta los registros del histórico, escucha el siguiente registro en el broker y lo compara con el estado de la estación, para confirmar que es de EST-01 y de la pieza que toca.

Esta comprobación solo lee: no fabrica piezas ni cambia nada. Puedes repetirla tantas veces como quieras.

```bash
# m01-01: cuenta los registros del histórico, escucha uno en MQTT y comprueba que cuadran
docker compose --profile lab run --rm --no-deps lab m01-01
```

📋 Ficha del comando [`m01-01`](../comandos-lab.md#m01-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambian la pieza y el total):

```text
{"mqtt": {"estacion": "EST-01", "pieza_id": "P0056", "ts": "2026-11-06T02:12:34+00:00", "temperatura_c": 60.88, "vibracion_mm_s": 0.235, "corriente_a": 4.11, "secuencia": 56, "tiempo_ciclo_s": 0.9}, "archivadas": 470}
OK m01-01: ciclo P0056 archivado; total=470
```

Cómo se lee:

- `"mqtt": {…}` es el registro que acaba de pasar por el broker: la carcasa `P0056`, la número 56 desde que arrancó la estación, terminada a las 02:12:34 (UTC) con el husillo a 60,88 °C, 0,9 s después de la anterior.
- `"archivadas": 470` son los registros que había en el histórico al empezar la comprobación.
- **El total y el número de pieza no coinciden**, y puede pasar en los dos sentidos. Si el histórico es de antes de este arranque, el total es **mayor** (aquí, 470 frente a 56): guarda carcasas de tandas anteriores. Si el histórico está recién vaciado, el total es algo **menor**: los registros que la estación emitió antes de que el archivador terminara de conectarse nadie los escuchó y se perdieron, que es el comportamiento normal de un broker sin persistencia.

**Si lo repites** unos segundos después, verás una pieza posterior (`P0020`, por ejemplo) y un total mayor: la estación sigue fabricando y el archivador sigue guardando.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m01_01</code>)</summary>

```python
n = esperar_filas(1)                  # ALMACÉN: SELECT COUNT(*) en historial.sqlite
payload = consumir(TOPIC_CICLO, 15)   # TRANSPORTE: se suscribe a linea/est01/ciclo y espera un registro
ciclo = json.loads(payload)
estado = leer_estado()                # ORIGEN: lo último que la estación dice haber fabricado
# el registro y el estado tienen que ser de la misma estación y de piezas cercanas
...
return ok("m01-01", f"ciclo {ciclo['pieza_id']} archivado; total={n}")
```

</details>

### 4 — Ver la conversación entre la estación y el archivador

**Qué ocurre:** el `OK` del paso 3 es un resumen que da un script del curso. Ahora lo ves contado por los propios protagonistas. Cada contenedor escribe una línea, su **log**, cada vez que hace algo; es su diario de trabajo. Vas a ver los diarios de la estación y del archivador a la vez, en directo.

```bash
# Diario en directo de la estación y del archivador (Ctrl+C para salir)
docker compose logs -f --tail=0 sensor archivador
```

**Resultado esperado** (cambian las piezas y las temperaturas; una línea nueva por carcasa):

```text
sensor-1      | sensor: P2818 62.28 C
archivador-1  | archivador: P2818
sensor-1      | sensor: P2819 62.72 C
archivador-1  | archivador: P2819
sensor-1      | sensor: P2820 62.96 C
archivador-1  | archivador: P2820
```

**Cómo se lee:**

| Línea | Quién la escribe | Qué significa |
|-------|------------------|---------------|
| `sensor: P2818 62.28 C` | La estación | «He terminado la carcasa P2818, el husillo estaba a 62,28 °C, y he enviado su registro al broker» |
| `archivador: P2818` | El archivador | «Me ha llegado el registro de P2818 y lo he guardado en el histórico» |

Se lee como una conversación: la estación anuncia cada carcasa y el archivador confirma que la ha guardado. Si cada anuncio tiene su confirmación, entre medias no se pierde nada. Alguna vez dos líneas salen en orden cruzado porque los dos diarios llegan a la pantalla por separado; no significa nada.

Déjalo abierto en una terminal aparte: en el reto 2 lo usarás para ver cómo se pierden registros.

## Comprueba tu entendimiento

**La misma pieza**

Si el archivador dejara de confirmar las carcasas, ¿dónde se habrían perdido los registros: en la estación, en el broker o en el archivador?

→ No en la estación, que sigue anunciándolas. Se pierden porque el broker los reparte y nadie los recoge: el broker no guarda nada.

## Investiga el histórico

Ahora haces tú las preguntas, con `lab sql` (paso 2). Funciona en **solo lectura**: puedes probar lo que quieras sin estropear nada.

📋 Ficha del comando [`sql`](../comandos-lab.md#sql).

### 1 — Qué columnas tiene la tabla

**Qué ocurre:** sin consulta, `lab sql` enseña la estructura de la tabla `lecturas`.

```bash
docker compose --profile lab run --rm --no-deps lab sql
```

**Resultado esperado:**

```text
 cid           name    type  notnull dflt_value  pk
   0             id INTEGER        0       None   1
   1       pieza_id    TEXT        0       None   0
   2             ts    TEXT        0       None   0
   3  temperatura_c    REAL        0       None   0
   4 vibracion_mm_s    REAL        0       None   0
   5    corriente_a    REAL        0       None   0
   6        payload    TEXT        0       None   0
   7 tiempo_ciclo_s    REAL        0       None   0
```

`pk = 1` marca la clave primaria: solo `id`. Ninguna columna obliga a que `pieza_id` sea único.

### 2 — ¿Cuántas carcasas tiene el histórico y cuántos nombres distintos?

**Qué ocurre:** cuentas las filas y los identificadores distintos. Si cada carcasa tuviera un nombre único, los dos números serían iguales.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS registros, COUNT(DISTINCT pieza_id) AS identificadores FROM lecturas"
```

**Resultado esperado** (con un histórico recién vaciado; los números cambian):

```text
 registros  identificadores
       136              136
```

Antes de seguir, **predice**: ¿qué pasará con estos dos números después del reto 3, cuando reinicies la estación?

### 3 — ¿Está completo? Carcasas por minuto

**Qué ocurre:** la estación fabrica unas 60 carcasas por minuto. Agrupas el histórico por minuto y cuentas. La pregunta es: si un minuto tiene menos de 60, ¿se han perdido carcasas?

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT substr(ts, 12, 5) AS minuto, COUNT(*) AS registros
   FROM lecturas GROUP BY substr(ts, 1, 16) ORDER BY substr(ts, 1, 16)"
```

**Resultado esperado** (cambian las horas y los números):

```text
minuto  registros
 02:04         48
 02:05         60
 02:06         60
 02:07         60
 02:08         54
 02:09         54
 02:10         35
```

**Cómo se lee:** el primer y el último minuto están incompletos porque el histórico empieza y termina a mitad de minuto. Pero en medio hay minutos con 54. **No se ha perdido nada**: en esos minutos la estación tuvo una microparada y **fabricó menos**. Contar por reloj no distingue «se fabricó menos» de «se guardó menos». Para eso hace falta la secuencia de la estación, que usarás en «Mejora la arquitectura».

### 4 — Tiempo de ciclo y microparadas

**Qué ocurre:** cada registro trae `tiempo_ciclo_s`, los segundos desde la carcasa anterior. Calculas cómo trabaja la estación y localizas las microparadas: carcasas que tardaron más de 2 segundos.

```bash
# Tiempo de ciclo medio, mínimo y máximo
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS carcasas, ROUND(AVG(tiempo_ciclo_s), 2) AS ciclo_medio,
          MIN(tiempo_ciclo_s) AS minimo, MAX(tiempo_ciclo_s) AS maximo FROM lecturas"

# Las carcasas que llegaron tras una microparada
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, ts, tiempo_ciclo_s FROM lecturas WHERE tiempo_ciclo_s > 2 ORDER BY id"
```

**Resultado esperado:**

```text
 carcasas  ciclo_medio  minimo  maximo
      371         1.03     0.9    6.89
```

```text
pieza_id                        ts  tiempo_ciclo_s
   P0251 2026-11-06T02:08:28+00:00            6.89
   P0318 2026-11-06T02:09:41+00:00            6.73
```

**Cómo se lee:** la estación trabaja a algo más de un segundo por carcasa, entre 0,9 y 1,1 en condiciones normales. Las dos microparadas, de unos 7 segundos, explican los minutos con 54 del punto anterior: están a las 02:08 y a las 02:09. El tiempo de ciclo es la base de un indicador de planta muy usado, el **rendimiento** del [OEE](../glosario/02-observabilidad.md#kpi): cuánto se fabrica frente a lo que se podría fabricar.

### 5 — ¿Cómo trabaja la estación?

**Qué ocurre:** calculas las medidas de referencia del proceso. Es lo primero que se mira para saber qué es «normal».

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT ROUND(AVG(temperatura_c), 2) AS media, MIN(temperatura_c) AS minima, MAX(temperatura_c) AS maxima,
          ROUND(AVG(vibracion_mm_s), 3) AS vib_media, ROUND(AVG(corriente_a), 2) AS corriente_media
   FROM lecturas"
```

**Resultado esperado:**

```text
 media  minima  maxima  vib_media  corriente_media
 62.03   60.87   63.24       0.25             4.05
```

El husillo trabaja entre 61 y 63 °C, lejos del margen de 70 °C del procedimiento.

## Reto

### 1 — Para la estación

Para la estación y repite la comprobación. ¿Qué pasa con los registros y con el histórico?

```bash
docker compose stop sensor
docker compose --profile lab run --rm --no-deps lab m01-01
```

<details>
<summary>Ver solución</summary>

```text
FALLO: no llega ningún ciclo por MQTT
```

En el laboratorio, `sensor` es la estación entera (máquina, sensores y pasarela). Al pararlo **no se fabrica ninguna carcasa**, así que no se pierde nada: no hay producción. El histórico conserva todo lo que ya guardó. Vuelve a arrancarla antes del reto siguiente:

```bash
docker compose start sensor
```

</details>

### 2 — Para el archivador con la estación fabricando

Ahora la estación sigue fabricando, pero nadie guarda. Si tienes abierto el diario del paso 4, verás que la estación sigue anunciando carcasas y nadie las confirma. Para el archivador 10 segundos, vuelve a arrancarlo y busca huecos en la numeración del histórico.

```bash
# La estación sigue fabricando
docker compose stop archivador
sleep 10
docker compose start archivador
sleep 3

# Recorre el histórico en orden y enseña dónde salta la numeración:
#   LAG(...) OVER (ORDER BY id) toma el valor de la fila anterior
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT anterior AS ultima_antes, pieza_id AS siguiente, numero - anterior_n - 1 AS faltan
   FROM (SELECT id, pieza_id, CAST(substr(pieza_id, 2) AS INTEGER) AS numero,
                LAG(pieza_id) OVER (ORDER BY id) AS anterior,
                LAG(CAST(substr(pieza_id, 2) AS INTEGER)) OVER (ORDER BY id) AS anterior_n
         FROM lecturas)
   WHERE numero > anterior_n + 1 ORDER BY id DESC LIMIT 3"
```

<details>
<summary>Ver solución</summary>

```text
ultima_antes siguiente  faltan
       P0037     P0049      11
```

Esas carcasas **se fabricaron**, y la estación publicó su registro, pero el broker no las guarda y el archivador no estaba escuchando. No están en el histórico y nada dio error. En planta pasa igual cuando se cae el servidor del histórico o se corta la red: hay piezas reales sin registro.

Repite la consulta de carcasas por minuto (Investiga, punto 3): el minuto en que paraste el archivador tiene menos registros. Pero, como viste, un minuto con microparada también. El hueco en la **numeración** de esta consulta es lo que demuestra que hubo pérdida: en una microparada la numeración sigue sin saltos.

</details>

### 3 — Reinicia la estación y busca piezas repetidas

Reinicia la estación y mira si hay identificadores que aparecen más de una vez en el histórico.

```bash
docker compose stop sensor
docker compose start sensor
sleep 5

# Piezas que aparecen más de una vez en el histórico
#   GROUP BY junta las filas con el mismo identificador; HAVING se queda con las que salen más de una vez
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, COUNT(*) AS veces FROM lecturas
   GROUP BY pieza_id HAVING COUNT(*) > 1 ORDER BY pieza_id LIMIT 5"
```

Si calidad dice que la `P0003` salió mala, ¿cuál de ellas es?

<details>
<summary>Ver solución</summary>

```text
pieza_id  veces
   P0001      2
   P0002      2
   P0003      2
   P0004      2
   P0005      2
```

Al reiniciar, la estación simulada vuelve a numerar desde `P0001`. En el histórico hay ahora **dos carcasas distintas** con el mismo identificador. Solo la hora las distingue:

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT id, pieza_id, ts, temperatura_c FROM lecturas WHERE pieza_id = 'P0003' ORDER BY id"
```

```text
 id pieza_id                        ts  temperatura_c
  3    P0003 2026-11-06T01:53:45+00:00          62.05
 56    P0003 2026-11-06T01:54:49+00:00          62.05
```

Dos filas distintas (`id` 3 y 56), un minuto aparte.

(La temperatura coincide porque la simulación repite la misma secuencia de valores en cada arranque; en una máquina real no pasaría.)

Con el identificador solo, no se puede saber cuál es la mala. Por eso cada registro lleva la hora y, en planta, el identificador no lo pone un [contador](../glosario/02-observabilidad.md#metrica) de la máquina sino el MES o un código grabado en la pieza.

</details>

### Empezar con el histórico vacío

Los ficheros de `infra/data/` los crea el contenedor como administrador, así que se borran también desde un contenedor:

```bash
docker compose stop sensor archivador mosquitto
docker compose --profile lab run --rm --no-deps --entrypoint rm lab -f /data/historial.sqlite /data/estado.json
docker compose up -d mosquitto sensor archivador
```

## Mejora la arquitectura

Has visto dónde se rompe. Ahora compruebas dos mejoras que no necesitan cambiar nada de la arquitectura: elegir una clave mejor y conciliar lo fabricado con lo registrado.

### 1 — Buscar una clave que sí identifique la carcasa

**Qué ocurre:** `pieza_id` se repite. Compruebas si la combinación de **identificador + hora** es única en el histórico. Si lo es, sirve como clave de pieza.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, ts, COUNT(*) AS veces FROM lecturas GROUP BY pieza_id, ts HAVING COUNT(*) > 1"
```

**Resultado esperado:**

```text
(ninguna fila)
```

Ninguna combinación se repite: `pieza_id` + `ts` identifica cada carcasa aunque la estación se reinicie. En una base de datos de planta se declara como clave única para que el histórico rechace un duplicado.

### 2 — Conciliar lo fabricado con lo registrado

**Qué ocurre:** comparas cuántas carcasas ha fabricado la estación desde su último arranque (lo dice la `secuencia` que viaja en cada registro) con cuántas hay en el histórico. A diferencia de contar por minuto, esto no se confunde con las microparadas: la secuencia solo cuenta carcasas fabricadas. Es la comprobación que una planta hace a diario entre el MES y el histórico.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "WITH inicio AS (SELECT MAX(id) AS id FROM lecturas WHERE json_extract(payload, '$.secuencia') <= 3)
   SELECT MAX(json_extract(payload, '$.secuencia')) AS fabricadas,
          COUNT(*) AS registradas,
          MAX(json_extract(payload, '$.secuencia')) - COUNT(*) AS sin_registro
   FROM lecturas, inicio WHERE lecturas.id >= inicio.id"
```

**Resultado esperado** (después del reto 2, sin el reto 3):

```text
 fabricadas  registradas  sin_registro
        155          142            13
```

**Cómo se lee:** desde que arrancó, la estación ha fabricado 155 carcasas y el histórico tiene 142. Faltan 13: las 10 del reto 2 y unas pocas del arranque, emitidas antes de que el archivador estuviera escuchando. Esta consulta detecta la pérdida **sin saber de antemano que la hubo**; por eso la conciliación es la mejor alarma contra la pérdida silenciosa.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el archivador no tiene ciclos` | la estación o el broker no han arrancado | `docker compose ps` y `docker compose logs sensor` |
| `no such service: lab` | falta `--profile lab` | copia el comando del paso 2 tal cual |
| `no configuration file provided` | no estás en `infra/` | `cd infra` |

## Conclusiones

### Qué es una arquitectura de datos industrial

Es la cadena de componentes que lleva el dato de proceso desde la máquina hasta donde se usa. En este laboratorio tiene tres:

```
 ORIGEN                      TRANSPORTE               ALMACÉN
 la estación emite ────────▶ el broker reparte ─────▶ el archivador guarda
 un registro por carcasa     a quien escuche          una fila por registro
```

Cada componente tiene **una sola función** y es un proceso separado que puede fallar por su cuenta. Lo que permite seguir un dato de punta a punta es que cada registro lleva **estación, pieza y hora**.

### Cómo debe ser para que sirva a la IA

Un modelo aprende del histórico y decide sobre piezas reales. Por eso la arquitectura tiene que garantizar tres cosas:

| Requisito | Qué significa | Por qué le importa a la IA |
|-----------|---------------|----------------------------|
| **Completa** | Cada carcasa fabricada tiene su registro | Si faltan piezas, el modelo aprende de una línea que no es la real |
| **Identificable** | Cada registro es de una sola carcasa, y se sabe de cuál | Para entrenar hay que unir las señales de una pieza con su resultado de calidad |
| **Comprobable** | Se puede verificar que lo anterior se cumple | Si nadie lo mira, los fallos no dan error y pasan al modelo |

### Dónde se rompe esta arquitectura y cómo lo has detectado

| Debilidad | Cómo la has detectado | Qué provoca |
|-----------|-----------------------|-------------|
| El broker no guarda: lo que se publica cuando nadie escucha se pierde | Reto 2: paras el archivador y aparece un hueco de unas 10 carcasas | Producción real sin registro, **sin ningún error** |
| Un único archivador, sin respaldo | Reto 2 | Si se cae, no hay histórico de ese tramo |
| El identificador lo pone un contador de la máquina, que se reinicia | Reto 3: tras reiniciar, cada `pieza_id` aparece varias veces | Varias carcasas distintas con el mismo nombre |
| La tabla no tiene una clave de pieza única | Reto 3: el histórico acepta los repetidos | No se sabe a cuál pertenece un resultado de calidad |
| Nadie compara lo fabricado con lo registrado | El total del paso 3 no cuadra con el número de pieza, y nada avisa | Los fallos anteriores pasan inadvertidos |
| Contar por reloj confunde producción con pérdida | Minutos con 54 registros por microparadas, sin pérdida | Se buscan pérdidas que no existen, o se dan por buenas pérdidas reales |

La forma de detectar debilidades es siempre la misma: **provocar un fallo de un componente y comprobar qué le pasa al dato**.

### Cómo se perfecciona

| Debilidad | Cómo se resuelve en una arquitectura de planta |
|-----------|-----------------------------------------------|
| Pérdida si nadie escucha | Sesiones persistentes con [QoS](../glosario/01-datos-arquitectura.md#qos) 1, o un bus con persistencia (Kafka) delante del histórico |
| Caída del almacén o de la red | *Store-and-forward* en el equipo [edge](../glosario/01-datos-arquitectura.md#edge): guarda localmente y reenvía al volver |
| Identificador que se repite | Identificador que no depende de la máquina (MES, DataMatrix grabado en la pieza), siempre con su hora |
| Histórico que acepta duplicados | Clave única en la tabla (pieza + hora, o el identificador del MES) |
| Fallos que nadie ve | Conciliación periódica entre las piezas producidas según el MES y los registros del histórico, **por secuencia, no por reloj** |

En los módulos siguientes irás viendo piezas de esa arquitectura completa: calidad del dato (M02), edge (M06), servicio con versión (M07) y [trazabilidad](../glosario/05-operacion-gobierno.md#trazabilidad) (M08).

### En una frase

> 🔑 Montar el camino del dato es fácil. Que el dato llegue completo y sea de la pieza que crees hay que diseñarlo y comprobarlo, porque todo lo que haga después la IA depende de ello.
