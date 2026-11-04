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

📋 Ficha del comando [`m01-01`](../comandos-lab.md#m01-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

<details>
<summary>Ver solución</summary>

```text
FALLO: no llega ningún ciclo por MQTT
```

La estación ya no fabrica, así que no hay registros nuevos que repartir. El histórico conserva todos los que ya guardó. Para volver a fabricar:

```bash
docker compose start sensor
```

Al volver, la numeración empieza otra vez en `P0001`: la estación simulada no recuerda por dónde iba. Por eso cada registro lleva también la hora (`ts`), que distingue las piezas de antes y de después de la parada.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el archivador no tiene ciclos` | la estación o el broker no han arrancado | `docker compose ps` y `docker compose logs sensor` |
| `no such service: lab` | falta `--profile lab` | copia el comando del paso 2 tal cual |
| `no configuration file provided` | no estás en `infra/` | `cd infra` |
