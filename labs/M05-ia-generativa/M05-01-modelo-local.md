# M05-01 — Ejecución local de modelos generativos

[← Página anterior](README.md) · [Siguiente página →](M05-02-integracion-aplicacion.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Arrancas un modelo generativo en el puesto y compruebas que responde en local, sin salir a internet.

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

- **Un modelo de lenguaje puede ejecutarse en el propio puesto**, sin enviar nada fuera de la fábrica.
- **Un modelo local es un fichero** (aquí, unos 470 MB) más un proceso que lo carga en memoria.
- **El tamaño se elige por el puesto**: este modelo de 0,5B cabe en 2 GB y responde en menos de un segundo en CPU, a cambio de ser más limitado que uno grande.
- **Lo que decide si es usable es el tiempo de respuesta** en el equipo real.

> 🔑 «Local» significa que la pregunta y la respuesta no salen del puesto. Eso se comprueba mirando a qué dirección se llama.
