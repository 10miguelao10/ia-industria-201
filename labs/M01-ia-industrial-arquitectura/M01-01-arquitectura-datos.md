# M01-01 — Arquitectura básica de datos

[← Página anterior](README.md) · [Siguiente página →](M01-02-visualizacion-supervision.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Pones en marcha una estación que fabrica piezas, sigues el registro de una pieza desde la máquina hasta el histórico y compruebas que no se pierde por el camino.

### Prerrequisitos

- Docker en marcha y el puesto comprobado (`./comprobar-puesto.sh` dio `PUESTO_OK`).
- RAM: unos 0,5 GB para mosquitto, sensor y archivador.
- [Qué es cada contenedor](../../infra/README.md).

### Qué está pasando en la línea

**EST-01 es una estación de mecanizado de carcasas.** En el laboratorio sale una carcasa terminada cada segundo: la primera es `P0001`, la segunda `P0002`, y así sucesivamente.

Mientras la máquina trabaja cada carcasa, tres sensores la vigilan:

| Sensor | Qué mide | Valor habitual |
|--------|----------|----------------|
| Temperatura del husillo | Lo caliente que está el eje que gira la herramienta | 61–63 °C |
| Vibración | Cuánto tiembla la máquina | 0,22–0,28 mm/s |
| Corriente del motor | Cuánto esfuerzo hace | ~4 A |

Al terminar cada carcasa, la estación emite su **registro**: qué pieza es, a qué hora terminó y cuánto marcaron los tres sensores. Ese registro tiene que llegar al **histórico de la planta** para que, más adelante, alguien pueda consultarlo, entrenar un modelo con él o explicar una reclamación.

El camino del registro tiene tres tramos:

```
 ORIGEN                            TRANSPORTE                ALMACÉN
 la estación emite el registro ──▶ el broker lo reparte ──▶ el archivador lo guarda
 (sensor)                          (mosquitto)               (archivador → historial.sqlite)
```

- **El broker no guarda nada.** Recibe el registro y entrega una copia a todos los que estén suscritos. Si nadie lo escucha en ese momento, se pierde.
- **El archivador es quien registra.** Está suscrito a los registros de EST-01 y escribe cada uno como una fila en la base de datos del histórico.

| En planta | En este laboratorio |
|-----------|---------------------|
| Máquina, sensores, PLC y una pasarela que publica | Un solo contenedor, `sensor`, que simula todo eso |
| Broker MQTT en un servidor de planta | Contenedor `mosquitto` |
| Histórico (historian, base de datos de MES) | Contenedor `archivador` y el fichero `infra/data/historial.sqlite` |

Todavía no hay ningún modelo de IA. Este lab solo comprueba que los registros llegan.

### 1 — Arrancar la estación y el camino de los registros

**Qué ocurre:** enciendes la estación (empieza a fabricar y a emitir un registro por segundo), el broker que los reparte y el archivador que los guarda. Desde ese momento el histórico empieza a llenarse.

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

### 2 — Ver el dato cruzar

**Qué ocurre:** haces lo que haría un técnico para comprobar que la línea de datos funciona. Primero cuenta cuántos registros hay ya en el histórico. Después se pone a escuchar en el broker hasta que la estación emite la siguiente registro. Por último, la compara con lo que la estación dice haber fabricado, para confirmar que es de EST-01 y de la pieza que toca.

Esta comprobación solo lee: no fabrica piezas ni cambia nada. Puedes repetirla tantas veces como quieras.

```bash
# m01-01: cuenta los registros del histórico, escucha uno en MQTT y comprueba que cuadran
docker compose --profile lab run --rm --no-deps lab m01-01
```

📋 Ficha del comando [`m01-01`](../comandos-lab.md#m01-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

> La primera vez que lanzas `lab`, Docker prepara su imagen y verás líneas `#1 … DONE` antes de la salida. Es normal y no se repite.

**Resultado esperado** (cambian la pieza y el total):

```text
{"mqtt": {"estacion": "EST-01", "pieza_id": "P0010", "ts": "2026-11-04T17:12:46+00:00", "temperatura_c": 62.1, "vibracion_mm_s": 0.22, "corriente_a": 4.11, "secuencia": 10}, "archivadas": 7}
OK m01-01: ciclo P0010 archivado; total=7
```

Cómo se lee:

- `"mqtt": {…}` es el registro que acaba de pasar por el broker: la carcasa `P0010`, la décima desde que arrancó la estación, terminada a las 17:12:46 con el husillo a 62,1 °C.
- `"archivadas": 7` son los registros que había en el histórico al empezar la comprobación.
- El total puede ser algo menor que el número de pieza. Los registros que la estación emitió en el primer segundo, antes de que el archivador terminara de conectarse, nadie los escuchó y se perdieron. Es el comportamiento normal de un broker sin persistencia, y por eso el archivador tiene que estar siempre en marcha.

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

### 3 — Mirar la estación y el archivador

**Qué ocurre:** el `OK` es un resumen. Ahora miras directamente qué dice cada parte: la estación anuncia cada carcasa que termina con su temperatura, y el archivador anuncia cada registro que guarda.

```bash
# Las 5 últimas carcasas que terminó la estación
docker compose logs --tail=5 sensor

# Los 5 últimos registros que guardó el archivador
docker compose logs --tail=5 archivador
```

**Resultado esperado:**

```text
sensor-1  | sensor: P0006 63.05 C
sensor-1  | sensor: P0007 61.11 C
sensor-1  | sensor: P0008 61.36 C
sensor-1  | sensor: P0009 61.6 C
sensor-1  | sensor: P0010 62.1 C
```

```text
archivador-1  | archivador: P0006
archivador-1  | archivador: P0007
archivador-1  | archivador: P0008
archivador-1  | archivador: P0009
archivador-1  | archivador: P0010
```

Las mismas carcasas en los dos lados: todo lo que la estación fabrica queda en el histórico.

## Comprueba tu entendimiento

**La misma pieza**

Toma el `pieza_id` de la salida del paso 2 y búscalo en los mensajes de log del paso 3.

→ Aparece en la estación (la fabricó) y en el archivador (la guardó).

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

Ahora la estación sigue fabricando, pero nadie guarda. Para el archivador 10 segundos, vuelve a arrancarlo y busca huecos en la numeración del histórico.

```bash
# La estación sigue: una carcasa por segundo
docker compose stop archivador
sleep 10
docker compose start archivador
sleep 3

# Recorre el histórico en orden y avisa cuando falten números de pieza
docker compose --profile lab run --rm --no-deps --entrypoint python lab -c "
import sqlite3
con = sqlite3.connect('/data/historial.sqlite')
anterior = None
for (pieza,) in con.execute('SELECT pieza_id FROM lecturas ORDER BY id'):
    n = int(pieza[1:])
    if anterior is not None and n > anterior + 1:
        print(f'hueco: después de P{anterior:04d} viene {pieza}; faltan {n - anterior - 1} carcasas')
    anterior = n
"
```

<details>
<summary>Ver solución</summary>

```text
hueco: después de P0022 viene P0033; faltan 10 carcasas
```

Esas 10 carcasas **se fabricaron**, y la estación publicó su registro, pero el broker no las guarda y el archivador no estaba escuchando. No están en el histórico y nada dio error. En planta pasa igual cuando se cae el servidor del histórico o se corta la red: hay piezas reales sin registro.

</details>

### 3 — Reinicia la estación y busca piezas repetidas

Reinicia la estación y mira si hay identificadores que aparecen más de una vez en el histórico.

```bash
docker compose stop sensor
docker compose start sensor
sleep 5

# Piezas que aparecen más de una vez en el histórico
docker compose --profile lab run --rm --no-deps --entrypoint python lab -c "
import sqlite3
con = sqlite3.connect('/data/historial.sqlite')
for pieza, veces in con.execute(
        'SELECT pieza_id, COUNT(*) FROM lecturas GROUP BY pieza_id HAVING COUNT(*) > 1 ORDER BY pieza_id LIMIT 5'):
    print(pieza, veces)
"
```

Si calidad dice que la `P0003` salió mala, ¿cuál de ellas es?

<details>
<summary>Ver solución</summary>

```text
P0002 2
P0003 2
P0004 2
P0005 2
P0006 2
```

Al reiniciar, la estación simulada vuelve a numerar desde `P0001`. En el histórico hay ahora **dos carcasas distintas** con el mismo identificador. Solo la hora las distingue:

```bash
docker compose --profile lab run --rm --no-deps --entrypoint python lab -c "
import sqlite3
con = sqlite3.connect('/data/historial.sqlite')
for fila in con.execute(\"SELECT pieza_id, ts, temperatura_c FROM lecturas WHERE pieza_id = 'P0003'\"):
    print(*fila)
"
```

```text
P0003 2026-11-05T09:51:57+00:00 62.05
P0003 2026-11-05T09:52:44+00:00 62.05
```

(La temperatura coincide porque la simulación repite la misma secuencia de valores en cada arranque; en una máquina real no pasaría.)

Con el identificador solo, no se puede saber cuál es la mala. Por eso cada registro lleva la hora y, en planta, el identificador no lo pone un contador de la máquina sino el MES o un código grabado en la pieza.

</details>

### Empezar con el histórico vacío

Los ficheros de `infra/data/` los crea el contenedor como administrador, así que se borran también desde un contenedor:

```bash
docker compose stop sensor archivador mosquitto
docker compose --profile lab run --rm --no-deps --entrypoint rm lab -f /data/historial.sqlite /data/estado.json
docker compose up -d mosquitto sensor archivador
```

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el archivador no tiene ciclos` | la estación o el broker no han arrancado | `docker compose ps` y `docker compose logs sensor` |
| `no such service: lab` | falta `--profile lab` | copia el comando del paso 2 tal cual |
| `no configuration file provided` | no estás en `infra/` | `cd infra` |

## Conclusiones

- **Una solución de datos en planta son piezas separadas.** Origen (la estación), transporte (el broker) y almacén (el archivador). Si una falta, el dato no llega.
- **El broker reparte, no guarda.** Lo que se publica cuando nadie escucha se pierde.
- **El histórico no es la realidad.** Puede faltar producción (reto 2) y puede haber identificadores repetidos (reto 3), sin que nada dé error.
- **El identificador de pieza y la hora son lo que permite seguir un dato** desde la máquina hasta el histórico. Sin ellos no se puede unir una lectura con su resultado de calidad.

> 🔑 Antes de pensar en modelos, el dato tiene que llegar completo y cada registro tiene que ser de la pieza que crees.
