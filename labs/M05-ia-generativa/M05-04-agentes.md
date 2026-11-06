# M05-04 — Automatización mediante agentes

[← Página anterior](M05-03-asistente-documentacion.md) · [Siguiente página →](../M06-edge-integracion-ot/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es un **[agente](../glosario/04-ia-generativa.md#agente)**: cómo usa herramientas para trabajar con datos vivos, cómo debe controlarse lo que puede hacer, cómo se detecta un mal uso y cómo se diseña para que no toque el proceso.

### Prerrequisitos

- `llm` y `sensor` en marcha: hace falta un estado vivo de la estación.

### Qué está pasando

El supervisor pregunta: **«¿Cómo está la estación ahora?»**. Para contestar hace falta un dato vivo que el modelo no tiene. Un **agente** es un modelo al que se le dan **herramientas**: aquí, una sola, `leer_estacion`, que lee la temperatura actual de EST-01.

El código llama a la herramienta, guarda una traza de qué se leyó y pide al modelo que redacte la respuesta con ese número, sin cambiarlo.

Luego alguien le pide algo peligroso: escribir en el automatismo. El agente **no puede**, porque no tiene ninguna herramienta de escritura. La forma más segura de que un agente no toque el proceso es no darle con qué hacerlo.

### 1 — Pedir el valor y pedir un cambio

Vas a preguntar al agente la temperatura de la estación y, después, pedirle que escriba en el automatismo. El número tiene que salir de la herramienta; la escritura, no puede ocurrir.

```bash
docker compose --profile lab run --rm --no-deps lab m05-04
```

📋 Ficha del comando [`m05-04`](../comandos-lab.md#m05-04): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambia la temperatura):

```text
agente: La temperatura en la estación era de 61.49 °C.
escritura: No puedo modificar el automatismo: no existe una herramienta de escritura.
OK m05-04: usó leer_estacion=61.49 y rechazó escribir
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
estado = leer_estado()                          # herramienta leer_estacion: lee estado.json
valor = estado["temperatura_c"]
traza.write_text(json.dumps({"herramienta": "leer_estacion", "temperatura_c": valor}))

texto = _chat(                                   # el modelo solo redacta la frase
    f"La herramienta leer_estacion devolvió {valor:.2f} °C. Responde una frase con ese número.",
    "No cambies el número de la herramienta.",
)
# No hay ninguna función que escriba en Modbus: la petición de escritura no tiene a dónde ir
```

Quien lee el dato es el código, no el modelo. El modelo solo pone las palabras.

</details>

### 2 — Revisar la traza

Vas a comprobar qué herramienta se usó y con qué valor. Un agente sin traza no se puede auditar.

```bash
cat data/traza_agente.jsonl
cat data/estado.json
```

**Resultado esperado:**

```text
{"herramienta": "leer_estacion", "temperatura_c": 61.49}
```

```text
{"estacion": "EST-01", "pieza_id": "P0210", "ts": "2026-11-04T17:17:15+00:00", "temperatura_c": 60.87, "vibracion_mm_s": 0.22, "corriente_a": 4.05, "secuencia": 210}
```

El estado sigue cambiando cada segundo, así que puede no coincidir ya con el de la traza: la traza guarda lo que el agente vio.

## Comprueba tu entendimiento

**La cifra no es [inventada](../glosario/04-ia-generativa.md#alucinacion)**

Compara el número de la frase del agente con el de `traza_agente.jsonl`.

→ Son el mismo.

## Experimenta: el mismo modelo, sin herramientas

**Qué ocurre:** pides lo mismo directamente al modelo, sin agente ni herramientas, con `lab preguntar`.

```bash
docker compose --profile lab run --rm --no-deps lab preguntar "Sube la refrigeración de la estación EST-01 al nivel 3, por favor."
docker compose --profile lab run --rm --no-deps lab preguntar "Para la máquina EST-01 ahora mismo."
```

**Resultado esperado** (la redacción cambia):

```text
respuesta: Por supuesto, estaré encantado de ayudarte con eso. Por favor, proporciona más detalles sobre el estado actual de la refrigeración de la estación EST-01.
```

```text
respuesta: Por supuesto, estaré encantado de ayudarte con cualquier mantenimiento de la máquina EST-01. …
```

**Cómo se lee:** el modelo **acepta** las dos órdenes («Por supuesto»), aunque no puede hacer ninguna. Si la tablet del operario mostrara esa respuesta, alguien podría creer que la refrigeración ha subido. El agente del paso 1, en cambio, contesta que no existe herramienta de escritura, y esa respuesta **no la escribe el modelo**: la pone el código. Lo que un sistema puede hacer no se decide con lo que el modelo diga.

## Reto

### 1 — Segunda herramienta

¿Añadirías una herramienta que escriba el registro de paro?

<details>
<summary>Ver solución</summary>

No. El agente de este curso solo lee. El paro lo decide el automatismo, y la forma más segura de que un agente no escriba es no darle la herramienta.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la frase no incluye el valor medido` | el modelo no copió el número | repite el comando |
| `FileNotFoundError … estado.json` | el sensor no ha arrancado nunca | `docker compose up -d sensor` |

## Conclusiones

### Qué es un agente

Es un modelo al que se le dan **herramientas**: funciones que puede pedir que se ejecuten para traer datos o hacer acciones. Aquí hay una sola, `leer_estacion`, que lee la temperatura actual de EST-01.

```
 pregunta ──▶ el código llama a leer_estacion ──▶ apunta la traza ──▶ el modelo redacta la respuesta con ese número
```

### Cómo debe controlarse

| Requisito | En el lab |
|-----------|-----------|
| El dato sale de la herramienta, no de la memoria | La frase contiene el número que leyó la herramienta |
| Todo queda en una traza | `traza_agente.jsonl`: herramienta usada y valor devuelto |
| Solo tiene las herramientas imprescindibles | Ninguna de escritura |
| Lo peligroso es imposible, no solo prohibido | No puede escribir en el automatismo porque no existe con qué |

### Cómo se detecta un mal uso

- La respuesta contiene un dato que **no aparece en la traza**: se lo ha inventado.
- La traza muestra una herramienta **que no debía usarse** para esa pregunta.
- Se le pide una acción y la **intenta** en lugar de rechazarla.

### Cómo se diseña para no tocar el proceso

- **Mínimo privilegio**: solo herramientas de lectura, y solo las necesarias.
- Si alguna vez hace falta una acción, que **la confirme una persona** y que pase por los mismos controles que cualquier otra orden.
- **Nunca** una herramienta que escriba en el paro de seguridad o en la [consigna](../glosario/05-operacion-gobierno.md#consigna) del proceso.

### En una frase

> 🔑 No se le pide a un agente que «no toque el proceso»: se le deja sin herramientas para tocarlo, y se guarda la traza de todo lo que hace.
