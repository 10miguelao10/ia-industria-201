# M05-03 — Asistente técnico basado en documentación

[← Página anterior](M05-02-integracion-aplicacion.md) · [Siguiente página →](M05-04-agentes.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

El asistente contesta el par de apriete a partir del procedimiento, y no inventa cuando el documento no habla del tema.

### Prerrequisitos

- `llm` en marcha (M05-01).
- El procedimiento está en `infra/linea/docs/procedimiento-est01.md`.

### Qué está pasando

Un técnico pregunta: **«¿A qué par se aprieta el tornillo de la brida?»**. El modelo no sabe nada de EST-01, y si contesta de memoria puede inventarse un número que suene bien. En planta, un par de apriete inventado es una pieza mal montada.

La respuesta tiene que salir del **procedimiento de la estación**. Así que antes de preguntar al modelo se busca el párrafo del procedimiento que habla de eso, y se le da junto con la pregunta y la instrucción de usar solo ese texto. Es lo que se conoce como recuperar y luego generar (RAG).

Y si el procedimiento no dice nada del tema, lo correcto es decir que no está, no inventarlo.

### 1 — Leer el documento

Vas a leer el procedimiento que usará el asistente. El asistente solo puede saber lo que está aquí.

```bash
cat linea/docs/procedimiento-est01.md
```

**Resultado esperado** (extracto):

```text
## Par de apriete

El tornillo de la brida se aprieta a 12 N·m. Si el par queda por debajo, la pieza se manda a revisión y no se acepta en línea.

## Temperatura

La temperatura de trabajo habitual del husillo está entre 58 °C y 66 °C. Por encima de 70 °C se avisa al turno. Ese aviso es una regla, no un modelo.
```

### 2 — Preguntar lo que sí está

Vas a preguntar el par de apriete. Verás primero el párrafo recuperado y después la respuesta del modelo construida con ese párrafo.

```bash
docker compose --profile lab run --rm --no-deps lab m05-03
```

📋 Ficha del comando [`m05-03`](../comandos-lab.md#m05-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
fragmento:
El tornillo de la brida se aprieta a 12 N·m. Si el par queda por debajo, la pieza se manda a revisión y no se acepta en línea.
respuesta='12 N·m.'
OK m05-03: responde 12 a partir del procedimiento
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
# 1. Recuperar: el párrafo que más palabras comparte con la pregunta
partes = [p.strip() for p in texto.split("\n\n") if p.strip()]
palabras = set(pregunta.lower().split())
fragmento = max(partes, key=lambda p: len(palabras & set(p.lower().split())))

# 2. Generar: el párrafo va dentro del mensaje, con instrucciones de no inventar
_chat(
    f"Texto:\n{fragmento}\n\nPregunta: {pregunta}\nResponde solo con el valor.",
    "Usa únicamente el texto. No inventes otro número.",
)
```

Si la respuesta no contiene 12, el paso repite la pregunta hasta 3 veces: un modelo pequeño no siempre copia bien.

</details>

### 3 — Preguntar lo que no está

Vas a preguntar por el color del tornillo de recambio, que el procedimiento no menciona. El fallo grave sería inventarlo.

```bash
docker compose --profile lab run --rm --no-deps lab m05-03-ausente
```

📋 Ficha del comando [`m05-03-ausente`](../comandos-lab.md#m05-03-ausente): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
sin_dato: el procedimiento no habla del color del tornillo
OK m05-03-ausente: no hay fragmento; no se inventa el dato
```

## Comprueba tu entendimiento

**Cita**

Señala en el fragmento impreso la frase del par.

→ Está en el procedimiento, no en la memoria del modelo.

## Reto

### 1 — Documento nuevo

Si añades un párrafo al procedimiento, ¿hay que reentrenar el modelo?

<details>
<summary>Ver solución</summary>

No. La próxima pregunta recupera el párrafo nuevo. El modelo no se toca: por eso este enfoque sirve para documentación que cambia.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la respuesta no contiene el 12` | el modelo pequeño no copió el número | repite. Si el fragmento impreso no tiene el 12, falló la recuperación |
| `FALLO` con error de conexión | `llm` parado | `docker compose ps` y `docker compose up -d llm` |

## Conclusiones

- **El modelo no conoce tu planta.** Si contesta de memoria, puede inventarse un dato que suene bien.
- **La respuesta se apoya en el documento:** primero se busca el párrafo y después el modelo contesta usando solo ese texto (recuperar y generar).
- **Si el documento no trata el tema, no hay respuesta.** Es mejor «no está en el procedimiento» que un número inventado.
- **Actualizar el asistente es actualizar el documento**, no reentrenar el modelo.

> 🔑 En planta, un asistente vale lo que valen sus fuentes. Si no puede señalar de dónde sale la respuesta, no sirve.
