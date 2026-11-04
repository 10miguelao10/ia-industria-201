# M01-01 — Arquitectura básica de datos

[← Página anterior](README.md) · [Siguiente página →](M01-02-visualizacion-supervision.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Sigues una lectura de EST-01 por el origen, el transporte y el almacén, y compruebas que es la misma pieza en los tres sitios.

### Prerrequisitos

- Docker en marcha y el puesto comprobado (`./comprobar-puesto.sh` dio `PUESTO_OK`).
- RAM: unos 0,5 GB para mosquitto, sensor y archivador.
- [Qué es cada contenedor](../../infra/README.md).

### En qué consiste

EST-01 es una estación de mecanizado simulada. `sensor` inventa un ciclo por segundo y lo publica por MQTT. `mosquitto` lo transporta. `archivador` lo guarda en una base SQLite. Todavía no hay ningún modelo.

### 1 — Levantar origen, transporte y almacén

Vas a arrancar las tres piezas del camino del dato y a comprobar que están vivas. Cada contenedor es un tramo: si no aparece en la lista, ese tramo no existe.

```bash
cd infra

# Arranca en segundo plano (-d) el origen, el transporte y el almacén
docker compose up -d mosquitto sensor archivador

# Lista los servicios y su estado
docker compose ps --format 'table {{.Service}}\t{{.Status}}'
```

**Resultado esperado:**

```text
SERVICE      STATUS
archivador   Up 3 seconds
mosquitto    Up 3 seconds
sensor       Up 3 seconds
```

`sensor` es el origen, `mosquitto` el transporte y `archivador` el almacén.

### 2 — Ver una pieza cruzar

Vas a leer un mensaje del tema MQTT `linea/est01/ciclo` y a contar las filas que ya hay en el almacén. Así compruebas que la pieza que viaja es la misma que se guarda.

```bash
# Ejecuta el paso m01-01 en un contenedor de un solo uso (--rm)
docker compose --profile lab run --rm --no-deps lab m01-01
```

> La primera vez que lanzas `lab`, Docker prepara su imagen y verás líneas `#1 … DONE` antes de la salida. Es normal y no se repite.

**Resultado esperado** (cambian el número de pieza y el total):

```text
{"mqtt": {"estacion": "EST-01", "pieza_id": "P0010", "ts": "2026-11-04T17:12:46+00:00", "temperatura_c": 62.1, "vibracion_mm_s": 0.22, "corriente_a": 4.11, "secuencia": 10}, "archivadas": 7}
OK m01-01: ciclo P0010 archivado; total=7
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
def cmd_m01_01(_args):
    n = esperar_filas(1)                  # cuenta filas en historial.sqlite (almacén)
    payload = consumir(TOPIC_CICLO, 15)   # se suscribe a linea/est01/ciclo y espera un mensaje
    ciclo = json.loads(payload)           # el ciclo es un JSON: pieza, hora y señales
    estado = leer_estado()                # lo último que escribió el sensor en disco
    # el mensaje y el estado tienen que ser de la misma estación y de piezas cercanas
    ...
    return ok("m01-01", f"ciclo {ciclo['pieza_id']} archivado; total={n}")
```

</details>

### 3 — Mirar el proceso, no solo el OK

El `OK` es un resumen. Vas a mirar los registros de cada contenedor para ver quién publicó y quién guardó.

```bash
# Últimas 5 líneas del origen: publica pieza y temperatura
docker compose logs --tail=5 sensor

# Últimas 5 líneas del almacén: guarda las mismas piezas
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

Son las mismas piezas en los dos lados.

## Comprueba tu entendimiento

**La misma pieza**

En la salida de `m01-01`, quédate con el `pieza_id` del JSON y búscalo en los registros del paso 3.

→ Aparece en el sensor (origen) y en el archivador (almacén).

## Reto

### 1 — Para el origen

Para el sensor y vuelve a lanzar el paso. ¿Qué pasa?

```bash
docker compose stop sensor
docker compose --profile lab run --rm --no-deps lab m01-01
```

<details>
<summary>Ver solución</summary>

```text
FALLO: no llega ningún ciclo por MQTT
```

Sin `sensor` no hay ciclos nuevos. El almacén conserva lo que ya guardó. Para recuperar el flujo:

```bash
docker compose start sensor
```

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el archivador no tiene ciclos` | sensor o mosquitto no han arrancado | `docker compose ps` y `docker compose logs sensor` |
| `no such service: lab` | falta `--profile lab` | copia el comando del paso 2 tal cual |
| `no configuration file provided` | no estás en `infra/` | `cd infra` |
