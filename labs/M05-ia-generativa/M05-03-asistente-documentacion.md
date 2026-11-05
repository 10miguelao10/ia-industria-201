# M05-03 — Asistente técnico basado en documentación

[← Página anterior](M05-02-integracion-aplicacion.md) · [Siguiente página →](M05-04-agentes.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es un **asistente basado en documentación**: por qué un modelo no debe contestar de memoria sobre la planta, cómo debe apoyarse en los documentos, cómo se detecta que inventa y cómo se mejora.

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

### Qué es un asistente basado en documentación

Es un modelo que contesta **a partir de los documentos de la planta**, no de su memoria. Funciona en dos pasos:

```
 pregunta ──▶ RECUPERAR: buscar el párrafo del procedimiento ──▶ GENERAR: el modelo contesta usando solo ese párrafo
```

### Cómo debe ser

| Requisito | En el lab |
|-----------|-----------|
| La respuesta sale del documento | El fragmento impreso contiene el 12 N·m y la respuesta también |
| Se puede ver de dónde sale | El paso enseña el párrafo antes de la respuesta |
| Si el documento no lo dice, no hay respuesta | Para el color del tornillo no hay párrafo, y no se pregunta al modelo |
| Se actualiza cambiando el documento | No hace falta reentrenar el modelo |

### Cómo se detecta que inventa

- La respuesta contiene un dato que **no está en el fragmento**.
- El fragmento recuperado **no tiene relación** con la pregunta.
- Contesta con seguridad a algo que **ningún documento trata**.

En el lab, el paso repite hasta 3 veces si la respuesta no trae el 12: un modelo pequeño no siempre copia bien, aunque tenga el texto delante.

### Cómo se mejora

- **Mejor recuperación**: buscar por significado (embeddings) en lugar de contar palabras comunes, que falla con sinónimos.
- **Citar la fuente** en cada respuesta, para que el técnico la compruebe.
- **Mantener los documentos al día**: el asistente vale lo que valen sus fuentes.

### En una frase

> 🔑 En planta, un asistente vale lo que valen sus documentos. Si no puede señalar de dónde sale la respuesta, no sirve.
