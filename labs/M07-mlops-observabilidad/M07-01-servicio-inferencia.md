# M07-01 — Publicación de servicios de inferencia

[← Página anterior](README.md) · [Siguiente página →](M07-02-monitorizacion.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Publicas el clasificador como servicio y cada respuesta dice qué versión del modelo contestó.

### Prerrequisitos

- M03-03 hecho (`data/modelo_defecto.joblib` y `data/VERSION`).
- Puerto 8000 libre. Techo del contenedor: 768 MB.

### Qué está pasando

El dictamen ya no lo quiere solo la línea. El **MES** lo quiere para la trazabilidad, **calidad** para su panel y **mantenimiento** para su tablet. Copiar el fichero del modelo en cada aplicación sería un caos: cada una acabaría con una versión distinta.

La solución es publicar el modelo como un **servicio**: un único proceso que recibe las señales de una pieza y devuelve el dictamen. Todas las aplicaciones le preguntan a él.

Cada respuesta dice **qué versión del modelo contestó**, y cada consulta queda apuntada en un registro con su entrada y su salida. Si una pieza llega sin señales, el servicio la rechaza: no se inventa los datos que faltan.

### 1 — Arrancar el servicio

Vas a levantar el servicio de inferencia y preguntarle si está listo y qué versión sirve.

```bash
docker compose up -d api

curl -s http://localhost:8000/salud
```

**Resultado esperado:**

```json
{"estado":"ok","version":"defecto-0.1"}
```

El servicio documenta su propio contrato en <http://localhost:8000/docs>:

![Documentación del servicio con GET /salud y POST /predecir](../img/M07-01-api-docs.png)

### 2 — Pedir un dictamen

Vas a mandar las señales de una pieza como lo haría una aplicación de planta. Las aplicaciones llaman al servicio; no abren el fichero del modelo.

```bash
# Pieza con temperatura normal
curl -s -X POST http://localhost:8000/predecir \
  -H 'Content-Type: application/json' \
  -d '{"pieza_id": "DEMO1", "temperatura_c": 61.4, "vibracion_mm_s": 0.25, "corriente_a": 4.1, "presion_bar": 6.0}'

# La misma pieza, 8 °C más caliente
curl -s -X POST http://localhost:8000/predecir \
  -H 'Content-Type: application/json' \
  -d '{"pieza_id": "DEMO2", "temperatura_c": 69.4, "vibracion_mm_s": 0.25, "corriente_a": 4.1, "presion_bar": 6.0}'
```

**Resultado esperado:**

```json
{"pieza_id":"DEMO1","version":"defecto-0.1","entrada":{…},"dictamen":"seguir","probabilidad":0.0798,"ts":"…"}
{"pieza_id":"DEMO2","version":"defecto-0.1","entrada":{…},"dictamen":"revisar","probabilidad":1.0,"ts":"…"}
```

Cada respuesta lleva la versión del modelo que la dio.

### 3 — Comprobar el contrato completo

Vas a ejecutar la comprobación del laboratorio: una pieza correcta tiene que dar dictamen con la versión de `/salud`, y una pieza sin señales tiene que rechazarse.

```bash
docker compose --profile lab run --rm --no-deps lab m07-01
```

📋 Ficha del comando [`m07-01`](../comandos-lab.md#m07-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
{"pieza_id": "SRV0001", "version": "defecto-0.1", "entrada": {"pieza_id": "SRV0001", "temperatura_c": 61.39, "vibracion_mm_s": 0.286, "corriente_a": 4.07, "presion_bar": 5.96}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}
OK m07-01: version=defecto-0.1 dictamen=seguir
```

## Comprueba tu entendimiento

**La versión viaja**

Lee la versión de la última línea del registro de predicciones.

```bash
tail -1 data/predicciones.jsonl
```

→ `"version": "defecto-0.1"`, la misma que `/salud`.

## Reto

### 1 — Pieza incompleta

Manda una pieza solo con `pieza_id`. ¿Qué devuelve el servicio?

```bash
curl -s -w '\nHTTP %{http_code}\n' -X POST http://localhost:8000/predecir \
  -H 'Content-Type: application/json' -d '{"pieza_id": "X"}'
```

<details>
<summary>Ver solución</summary>

Un error `HTTP 422` con la lista de campos que faltan (`temperatura_c`, `vibracion_mm_s`…). No hay dictamen: el servicio no se inventa las señales.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `curl: (7) Failed to connect` | `api` no arrancó, normalmente porque faltaba el `.joblib` | `docker compose logs api`; si falta el modelo, `m03-03` y `docker compose up -d api` |
| responde otra versión | el contenedor arrancó con un `VERSION` viejo | `docker compose up -d --force-recreate api` |

## Conclusiones

- **Publicar un modelo como servicio** evita que cada aplicación tenga su copia y su versión.
- **Cada respuesta dice qué versión contestó**, y cada consulta queda registrada con su entrada y su salida.
- **El servicio no se inventa datos:** una pieza sin señales se rechaza con un error.
- **El servicio documenta su propio contrato** (`/docs`): qué recibe y qué devuelve.

> 🔑 Si no sabes qué versión del modelo dio un dictamen, no puedes explicarlo ni corregirlo.
