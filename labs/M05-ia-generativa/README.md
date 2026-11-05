# M05 — Inteligencia artificial generativa en entornos industriales

[← Página anterior](../M04-vision-control-calidad/M04-04-red-neuronal.md) · [Siguiente página →](M05-01-modelo-local.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Arrancar un modelo generativo en local y conocer qué pide la máquina.
- Llamarlo desde una aplicación.
- Consultar documentación técnica con recuperación.
- Dejar que un agente use una herramienta externa acotada.

## Teoría

Un modelo generativo completa texto (o imagen) a partir de un contexto. No consulta solo la planta: consulta lo que tú le pones delante. Si no le das el procedimiento, se lo inventa con fluidez.

### Piezas

| Pieza | Qué es aquí |
|-------|-------------|
| Modelo fundacional | Red grande ya entrenada, que tú no reentrenas en este curso |
| LLM | Modelo de lenguaje con el que escribes y lees instrucciones |
| Inferencia | Pasar una pregunta y obtener una respuesta, sin volver a entrenar |
| Recuperación | Buscar fragmentos de tus documentos y adjuntarlos a la pregunta |
| Agente | Un bucle que puede llamar una herramienta (por ejemplo, leer una señal) y seguir |

### Por qué en local

En una planta, el procedimiento y la telemetría no deben salir a un servicio externo por defecto. Ejecutar en el puesto enseña el coste: memoria, disco y tiempo de respuesta. Un modelo pequeño cabe en un portátil; uno grande, no.

### Límite

La respuesta puede sonar correcta y estar mal. En operación, el asistente propone y la persona contrasta con el procedimiento oficial. El agente solo llama herramientas que tú has definido, no «hace lo que quiera» en la red.

## Demostración guiada

Se arranca un modelo ya descargado, se le pregunta desde una aplicación, se le da un procedimiento para que conteste citándolo y se cierra con un agente que solo lee.

Todo se lanza desde `infra/`.

**1. Arrancar el modelo local y ver lo que ocupa.**

```bash
docker compose stop panel          # libera memoria
docker compose up -d llm
curl -s http://localhost:8088/salud
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}'
```

```json
{"estado":"ok","modelo":"qwen2.5-0.5b-instruct-q4_k_m.gguf"}
```

**2. Preguntar como lo haría una aplicación.**

```bash
curl -s http://localhost:8088/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "Explica en una frase qué es un PLC."}], "max_tokens": 60}'
```

La respuesta llega en algo más de un segundo, en CPU y sin salir del puesto.

**3. Asistente sobre el procedimiento.**

```bash
cat linea/docs/procedimiento-est01.md
docker compose --profile lab run --rm --no-deps lab m05-03
```

📋 Ficha del comando [`m05-03`](../comandos-lab.md#m05-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
fragmento:
El tornillo de la brida se aprieta a 12 N·m. Si el par queda por debajo, la pieza se manda a revisión y no se acepta en línea.
respuesta='12 N·m.'
OK m05-03: responde 12 a partir del procedimiento
```

**4. Agente que lee y no escribe.**

```bash
docker compose --profile lab run --rm --no-deps lab m05-04
```

📋 Ficha del comando [`m05-04`](../comandos-lab.md#m05-04): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
agente: La temperatura en la estación era de 61.49 °C.
escritura: No puedo modificar el automatismo: no existe una herramienta de escritura.
OK m05-04: usó leer_estacion=61.49 y rechazó escribir
```

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M05-01 | [Ejecución local de modelos generativos](M05-01-modelo-local.md) | Poner en marcha un modelo en el puesto. |
| M05-02 | [Integración desde aplicaciones](M05-02-integracion-aplicacion.md) | Llamar al modelo desde un programa. |
| M05-03 | [Asistente técnico basado en documentación](M05-03-asistente-documentacion.md) | Responder citando procedimientos, no de memoria. |
| M05-04 | [Automatización mediante agentes](M05-04-agentes.md) | Dejar que un agente llame una herramienta acotada. |

→ Empieza por **[M05-01 — Ejecución local de modelos generativos](M05-01-modelo-local.md)**.

## Conclusiones del módulo

Al terminar los laboratorios de este módulo deberías tener claro que:

- Un modelo de lenguaje puede ejecutarse en el puesto, sin sacar datos de la fábrica.
- Las respuestas sobre la planta tienen que salir de sus documentos, no de la memoria del modelo.
- A un agente se le limita con las herramientas que tiene: si no puede escribir, no escribe.
