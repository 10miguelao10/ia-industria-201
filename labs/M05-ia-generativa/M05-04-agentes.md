# M05-04 — Automatización mediante agentes

[← Página anterior](M05-03-asistente-documentacion.md) · [Siguiente página →](../M06-edge-integracion-ot/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

El agente lee la temperatura con una herramienta y se niega a escribir en el automatismo.

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

**La cifra no es inventada**

Compara el número de la frase del agente con el de `traza_agente.jsonl`.

→ Son el mismo.

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
