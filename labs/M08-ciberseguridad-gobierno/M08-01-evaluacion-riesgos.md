# M08-01 — Evaluación de riesgos

[← Página anterior](README.md) · [Siguiente página →](M08-02-gobierno-trazabilidad.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Listas las superficies de la arquitectura y dejas una medida para el dato, otra para el modelo y otra para el acceso.

### Prerrequisitos

- `modbus` en marcha, para leer el registro de paro.
- El inventario es el de [infra/README.md](../../infra/README.md).

### Qué está pasando

Antes de llevar esta solución a la red de la planta, el responsable de **ciberseguridad** pregunta: ¿qué estáis exponiendo, qué puede salir mal y qué habéis hecho para evitarlo?

Cada servicio que escucha en un puerto es una **superficie**: algo a lo que se puede llegar desde la red. Los más delicados son los que tocan la parte OT, como el esclavo Modbus que tiene el registro del paro de seguridad.

En este lab haces el inventario de superficies y dejas escrita una medida para cada tipo de riesgo: el dato, el modelo y el acceso. Y compruebas si lo que está escrito se cumple de verdad.

### 1 — Ver qué está expuesto

Vas a listar qué contenedores están en marcha y qué puertos publican en el puesto. No se protege lo que no está escrito.

```bash
docker compose ps --format 'table {{.Service}}\t{{.Ports}}'
```

**Resultado esperado** (depende de lo que tengas arrancado):

```text
SERVICE      PORTS
api          0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
archivador
modbus       0.0.0.0:1502->1502/tcp, [::]:1502->1502/tcp
mosquitto    0.0.0.0:1883->1883/tcp, [::]:1883->1883/tcp
opcua        0.0.0.0:4840->4840/tcp, [::]:4840->4840/tcp
sensor
```

`0.0.0.0` (y `[::]` en IPv6) significa que el puerto escucha en todas las interfaces del equipo, no solo en `localhost`. En una red de planta, cualquiera que llegue a ese equipo llegaría a esos servicios.

### 2 — Inventariar y mirar el paro

Vas a generar el inventario de superficies con una medida para cada riesgo, y a comprobar que el paro de seguridad sigue en reposo.

```bash
docker compose --profile lab run --rm --no-deps lab m08-01
```

**Resultado esperado:**

```text
superficies:
  mosquitto puerto=1883 — transporte MQTT de los ciclos
  sensor puerto=- — origen: publica el estado de EST-01
  archivador puerto=- — almacén SQLite de ciclos
  opcua puerto=4840 — la misma señal, como servidor OPC-UA
  modbus puerto=1502 — la misma señal, como esclavo Modbus TCP
  panel puerto=8501 — indicadores del turno
  llm puerto=8088 — inferencia del modelo generativo, solo en M05
  api puerto=8000 — servicio de inferencia del clasificador, desde M07
medida_dato: el histórico y el procedimiento se quedan en el volumen local; no hay URL externa
medida_modelo: el fichero joblib y el GGUF están en disco y la respuesta lleva versión
medida_acceso: los puertos del laboratorio solo se publican en localhost del puesto
OK m08-01: inventario escrito; paro de seguridad en 0
```

## Comprueba tu entendimiento

**La medida de acceso**

Compara `medida_acceso` con lo que viste en el paso 1.

→ No cuadra: el paso 1 enseña `0.0.0.0`, no `127.0.0.1`. La medida escrita no se está cumpliendo. Eso es justo lo que busca una evaluación de riesgos: la diferencia entre lo que se dice y lo que hay.

## Reto

### 1 — Cumplir la medida

¿Qué cambiarías en `docker-compose.yml` para que la medida de acceso fuera cierta?

<details>
<summary>Ver solución</summary>

Publicar cada puerto solo en `localhost`, por ejemplo:

```yaml
    ports:
      - "127.0.0.1:1883:1883"
```

Con eso, `docker compose ps` enseña `127.0.0.1:1883->1883/tcp` y el servicio solo es accesible desde el propio puesto.

</details>

### 2 — El agente

¿Qué medida tomaste en M05-04 al no crear una herramienta de escritura?

<details>
<summary>Ver solución</summary>

Mínimo privilegio: el agente no puede escribir en el proceso porque no tiene con qué.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: modbus no disponible para el cruce OT` | el esclavo está parado | `docker compose up -d modbus` |
| `FALLO: el paro de seguridad no está en reposo` | alguien escribió el registro | `docker compose restart modbus` |
