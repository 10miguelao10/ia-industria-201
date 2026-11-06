# M05-01 — Ejecución local de modelos generativos

[← Página anterior](README.md) · [Siguiente página →](M05-02-integracion-aplicacion.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **ejecutar un modelo generativo en local**: qué hace falta para que funcione en el puesto, cómo debe dimensionarse, qué se gana y qué se pierde frente a un servicio externo, y cómo se decide el tamaño.

### Prerrequisitos

- El fichero `infra/modelos/qwen2.5-0.5b-instruct-q4_k_m.gguf` (~470 MB). Lo deja la prueba del puesto; si falta, paso 1.
- RAM: el contenedor `llm` tiene un techo de 2 GB. CPU, sin GPU.

### Qué está pasando

Los **técnicos de mantenimiento** quieren un asistente al que preguntar cosas de la estación en lenguaje normal. La condición de la planta es clara: **ningún dato sale de la fábrica**. Nada de enviar preguntas ni procedimientos a un servicio de internet.

La solución es un **modelo de lenguaje que se ejecuta en el propio puesto**. Es pequeño (Qwen2.5 de 0,5B, 500 millones de parámetros, comprimido a 4 bits), funciona en CPU y no necesita GPU. En este lab lo arrancas y mides lo que tarda en responder, que es lo que decide si el asistente es usable en planta.

### 1 — Tener el modelo en disco

Vas a comprobar que el fichero del modelo está en el puesto. Un modelo local es, ante todo, un fichero.

```bash
# ¿Está el modelo?
ls -lh modelos/

# Solo si no está: descarga única (~470 MB)
curl -L -o modelos/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

**Resultado esperado:** un fichero `qwen2.5-0.5b-instruct-q4_k_m.gguf` de unos 470 MB.

### 2 — Arrancar el modelo y esperar a que cargue

Vas a liberar memoria parando el panel, arrancar el servicio del modelo y esperar a que diga que está listo. Hasta que el proceso no tiene el modelo en memoria, no hay respuesta.

```bash
# El panel no hace falta en M05 y ocupa memoria
docker compose stop panel

# Arranca el servicio del modelo
docker compose up -d llm

# Pregunta si está listo (repite hasta que conteste)
curl -s http://localhost:8088/salud
```

También puedes abrir <http://localhost:8088/salud> en Chrome, y <http://localhost:8088/docs> para ver la documentación del servicio.

**Resultado esperado:**

```json
{"estado":"ok","modelo":"qwen2.5-0.5b-instruct-q4_k_m.gguf"}
```

Si `curl` da `Connection refused` o no contesta, el modelo sigue cargando: espera unos segundos y repite.

### 3 — Una pregunta corta

Vas a pedir una respuesta corta y medir cuánto tarda. Es la medida que importa del puesto: segundos por respuesta.

```bash
# Pide "hola" al servicio local y cronometra
docker compose --profile lab run --rm --no-deps lab m05-01
```

📋 Ficha del comando [`m05-01`](../comandos-lab.md#m05-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (el tiempo depende del puesto):

```text
respuesta='¡Hola! ¿Cómo puedo ayudarte hoy?' segundos=0.5 url=http://llm:8088
OK m05-01: inferencia local en 0.5s via http://llm:8088
```

`http://llm:8088` es el contenedor `llm` dentro de la red de Docker del puesto, no un dominio de internet.

## Comprueba tu entendimiento

**Sigue en local**

La URL del `OK`, ¿sale del puesto o va a un proveedor externo?

→ Es `http://llm:8088`, el contenedor del puesto.

## Investiga: cuánto ocupa y cuánto tarda

**Qué ocurre:** mides lo que cuesta tener el modelo en el puesto: memoria y tiempo para una respuesta larga.

```bash
# Memoria que usa el contenedor del modelo
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}' | grep -E "NAME|llm"

# Tiempo para una respuesta de hasta 200 tokens (trozos de palabra)
time curl -s http://localhost:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "Escribe un párrafo sobre el mantenimiento preventivo."}], "max_tokens": 200}' > /dev/null
```

**Resultado esperado** (depende del puesto):

```text
NAME                  MEM USAGE / LIMIT
ia-linea-llm-1        192MiB / 2GiB
```

```text
real	0m2,759s
```

**Cómo se lee:** el contenedor marca unos 200 MB porque el modelo se lee del fichero según lo necesita (el sistema lo mantiene en memoria caché, que `docker stats` no cuenta entera). El tiempo es lo que importa: aquí, menos de 3 segundos para 200 tokens; en un portátil más modesto, varias veces más. Ese número decide si el asistente es usable en el puesto: un técnico no espera un minuto por una respuesta.

## Experimenta: la misma pregunta, tres veces

**Qué ocurre:** haces la misma pregunta tres veces con el comando de ayuda `lab preguntar`.

```bash
for i in 1 2 3; do
  docker compose --profile lab run --rm --no-deps lab preguntar "¿A qué par se aprieta el tornillo de la brida de EST-01?" | grep respuesta
done
```

📋 Ficha del comando [`preguntar`](../comandos-lab.md#preguntar).

**Resultado esperado** (cada vez una cosa distinta):

```text
respuesta: El tornillo de la brida de EST-01 se aprieta con el pincho de la brida.
respuesta: El tornillo de la brida de EST-01 se aprieta con el pincho de la estación.
respuesta: El tornillo de la brida de EST-01 se aprieta con el pinza de la estación.
```

**Cómo se lee:** **tres respuestas distintas e inventadas**. El modelo elige cada palabra con algo de azar, así que no es determinista; y como no conoce el procedimiento, se inventa algo que suene a respuesta. Las dos cosas juntas dicen cómo **no** usar un modelo de lenguaje: como fuente de datos de la planta. En el M05-03 verás cómo se corrige.

## Reto

### 1 — Modelo más grande

¿Por qué este curso no usa un modelo de varios GB?

<details>
<summary>Ver solución</summary>

Sin GPU y con 2 GB para el contenedor no respondería a tiempo. El de 0,5B cabe y basta para ver inferencia, recuperación de documentos y los límites de un modelo pequeño.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el servicio local no responde` | sigue cargando o falta el `.gguf` | `docker compose logs llm` y `ls -lh modelos/` |
| `Falta el modelo en /modelos/…` en los logs | el fichero no está o tiene otro nombre | paso 1 |
| tarda mucho | es la primera carga en CPU | espera a que `/salud` conteste antes de repetir |

## Conclusiones

### Qué es un modelo generativo local

Es un modelo de lenguaje que se ejecuta **en el propio equipo**, sin enviar nada fuera. Tiene dos partes: un **fichero** con el modelo (aquí, unos 470 MB) y un **proceso** que lo carga en memoria y responde por HTTP.

### Cómo debe dimensionarse

| Requisito | En el lab |
|-----------|-----------|
| Cabe en la memoria del puesto | Techo de 2 GB para el contenedor `llm` |
| Responde a tiempo | Una respuesta corta en menos de un segundo en CPU |
| No sale de la fábrica | La dirección es `http://llm:8088`, el propio puesto |

### Qué se gana y qué se pierde

| | Modelo local pequeño (este) | Servicio externo grande |
|--|------------------------------|-------------------------|
| Datos | No salen del puesto | Salen de la fábrica |
| Disponibilidad | No depende de internet | Depende de la conexión y del proveedor |
| Calidad de las respuestas | Limitada: se equivoca y no siempre obedece | Mucho mejor |
| Coste | El del equipo | Por uso |

### Cómo se decide el tamaño

- Se empieza por la **condición de la planta** (aquí: ningún dato sale de la fábrica, sin GPU).
- Se elige el **modelo más capaz que responda a tiempo** en el equipo real.
- Se compensa su tamaño dándole **buen contexto** (los documentos de la planta, en M05-03) en lugar de esperar que lo sepa todo.

### En una frase

> 🔑 «Local» significa que la pregunta y la respuesta no salen del puesto. El precio es un modelo más pequeño, y eso se compensa con buen contexto.
