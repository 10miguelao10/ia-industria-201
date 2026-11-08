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

Un técnico pregunta: **«¿A qué par se aprieta el tornillo de la brida?»**. El modelo no sabe nada de EST-01, y si contesta de memoria puede inventarse un número que suene bien. En planta, un par de apriete [inventado](../glosario/04-ia-generativa.md#alucinacion) es una pieza mal montada.

La respuesta tiene que salir del **procedimiento de la estación**. Así que antes de preguntar al modelo se busca el párrafo del procedimiento que habla de eso, y se le da junto con la pregunta y la instrucción de usar solo ese texto. Es lo que se conoce como recuperar y luego generar ([RAG](../glosario/04-ia-generativa.md#rag)).

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

## Investiga: cómo elige el párrafo

**Qué ocurre:** el asistente funciona si la búsqueda trae el párrafo correcto. El comando de ayuda `lab buscar` enseña cómo puntúa cada párrafo para una pregunta: cuenta las palabras que comparten.

```bash
docker compose --profile lab run --rm --no-deps lab buscar "¿A qué par se aprieta el tornillo de la brida?"
```

📋 Ficha del comando [`buscar`](../comandos-lab.md#buscar).

**Resultado esperado:**

```text
puntos  palabras en común                párrafo
     9  a, aprieta, brida, de, el, la,   El tornillo de la brida se aprieta a 12 N·m. Si el par queda…
     3  de, el, se                       Antes de medir el husillo, bloquear el husillo con el cerroj…
     3  de, la, se                       La temperatura de trabajo habitual del husillo está entre 58…
...
OK buscar: elegido el párrafo con 9 palabras en común
```

**Cómo se lee:** el párrafo correcto gana con claridad: 9 palabras en común. Pero fíjate en cuáles: «a», «de», «el», «la» cuentan igual que «brida» o «aprieta».

Prueba ahora otra pregunta:

```bash
docker compose --profile lab run --rm --no-deps lab buscar "¿A qué temperatura hay que avisar?"
```

**Resultado esperado:**

```text
puntos  palabras en común                párrafo
     1  a                                El tornillo de la brida se aprieta a 12 N·m. Si el par queda…
     1  temperatura                      ## Temperatura
     1  temperatura                      La temperatura de trabajo habitual del husillo está entre 58…
...
```

**Cómo se lee:** empate a 1 entre tres párrafos, y **gana el del par de apriete**, porque contiene la palabra «a». El asistente respondería sobre la temperatura leyendo el párrafo del tornillo. Compruébalo:

```bash
docker compose --profile lab run --rm --no-deps lab preguntar "¿A qué temperatura hay que avisar?" procedimiento
```

```text
fragmento recuperado: El tornillo de la brida se aprieta a 12 N·m. …
respuesta: Sin más contexto, no puedo determinar exactamente la respuesta. …
```

Con el párrafo equivocado, el modelo al menos dice que no lo sabe. Pero el dato estaba en el procedimiento.

## Mejora: buscar solo con las palabras que importan

**Qué ocurre:** quitas de la búsqueda las **[palabras vacías](../glosario/04-ia-generativa.md#palabras-vacias)** («a», «de», «la», «qué»…) y los títulos, que no dicen de qué trata un párrafo. La opción `filtrar` lo hace.

```bash
docker compose --profile lab run --rm --no-deps lab buscar "¿A qué temperatura hay que avisar?" filtrar
```

**Resultado esperado:**

```text
palabras que cuentan: avisar, temperatura
puntos  palabras en común                párrafo
     1  temperatura                      La temperatura de trabajo habitual del husillo está entre 58…
     0                                   Estación de mecanizado de carcasas. Este texto es ficticio y…
...
```

**Cómo se lee:** ahora gana el párrafo correcto. Pero solo con 1 punto: «avisar» no coincide con «avisa», la palabra que usa el procedimiento. Contar palabras exactas es frágil ante sinónimos y conjugaciones. Los asistentes reales buscan **por significado** (con *[embeddings](../glosario/06-modelos-abiertos.md#comparacion-tipos)*, que convierten cada texto en números de forma que textos parecidos quedan cerca), y por eso encuentran el párrafo aunque la pregunta use otras palabras.

## Constrúyelo tú: tu propio asistente con el procedimiento

**Qué está pasando:** `lab m05-03` busca el párrafo del procedimiento y se lo da al modelo, todo por dentro. Ahora construyes tú el asistente entero, que es lo que se llama RAG: partes el documento en párrafos, eliges el que habla de la pregunta, se lo das al modelo con la orden de usar solo ese texto y **compruebas** que la respuesta sale de ahí. Al final le preguntas algo que el procedimiento no dice, y haces que conteste «no está» sin llegar a preguntar al modelo.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** tener el documento troceado, que es lo que el asistente va a buscar.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m05_03_mi_asistente.py`](../../infra/construye/m05_03_mi_asistente.py). Arriba están las **decisiones** (`PREGUNTA`, la lista de palabras vacías `VACIAS` y `MINIMO_PALABRAS`); debajo, el paso 1 ya escrito: lee `infra/linea/docs/procedimiento-est01.md` y lo parte en párrafos, sin los títulos. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_03_mi_asistente.py
```

**Resultado esperado:**

```text
el procedimiento tiene 5 párrafos (sin contar los títulos)
```

**Cómo se lee:** cada párrafo es un trozo que el asistente puede elegir para dárselo al modelo. Trocear es la primera decisión de un RAG: trozos demasiado largos meten texto que no importa; demasiado cortos, cortan la información. Aquí, un párrafo por apartado. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Las palabras que importan

**Para qué:** comparar textos por su contenido, sin que cuenten palabras que salen en cualquier frase.

**Qué ocurre:** escribes una función que pasa un texto a minúsculas, se queda con sus palabras y quita las vacías. La pruebas con la pregunta.

Pega debajo de `# --- PASO 2`:

```python
def palabras(texto):
    todas = set(re.findall(r"[a-záéíóúñ0-9]+", texto.lower()))    # solo letras y números
    return todas - VACIAS

print("palabras de la pregunta:", sorted(palabras(PREGUNTA)))
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
palabras de la pregunta: ['aprieta', 'brida', 'par', 'tornillo']
```

**Cómo se lee:** de la pregunta solo quedan cuatro palabras: las que dicen de qué trata. «A», «qué», «se», «el» y «de» se han ido: salen en cualquier párrafo y harían ganar a uno equivocado, como viste en «Investiga».

### 3 — Elegir el párrafo

**Para qué:** encontrar el trozo del procedimiento que contesta a la pregunta.

**Qué ocurre:** cuentas, para cada párrafo, cuántas palabras tiene en común con la pregunta, y te quedas con el que más tiene.

Pega debajo de `# --- PASO 3`:

```python
def puntos(parrafo, pregunta):
    return len(palabras(parrafo) & palabras(pregunta))      # palabras en común

def elegir(pregunta):
    mejor = max(parrafos, key=lambda p: puntos(p, pregunta))
    return mejor, puntos(mejor, pregunta)

parrafo, en_comun = elegir(PREGUNTA)
print(f"párrafo elegido ({en_comun} palabras en común): {parrafo}")
```

**Resultado esperado** (líneas nuevas):

```text
párrafo elegido (4 palabras en común): El tornillo de la brida se aprieta a 12 N·m. Si el par queda por debajo, la pieza se manda a revisión y no se acepta en línea.
```

**Cómo se lee:** gana el párrafo del par de apriete, con el 12 N·m dentro. Es la «R» de RAG: **recuperar** el texto antes de generar. Esta búsqueda por palabras es la más sencilla; en el glosario tienes sus hermanos, como la búsqueda por significado, que encuentra «apretar» aunque el texto diga «par».

### 4 — Preguntar con el párrafo delante

**Para qué:** que el modelo conteste con el procedimiento, no de memoria.

**Qué ocurre:** mandas al modelo el párrafo elegido y la pregunta, con unas instrucciones de sistema que le piden usar solo ese texto.

Pega debajo de `# --- PASO 4`:

```python
def generar(pregunta, parrafo):
    mensajes = [{"role": "system", "content": "Responde solo con el texto que se te da. Copia los números tal cual."},
                {"role": "user", "content": f"Texto: {parrafo}\n\nPregunta: {pregunta}"}]
    r = httpx.post("http://llm:8088/v1/chat/completions", json={"messages": mensajes, "max_tokens": 40}, timeout=60)
    return r.json()["choices"][0]["message"]["content"].strip()

respuesta = generar(PREGUNTA, parrafo)
print("respuesta:", respuesta)
```

**Resultado esperado** (línea nueva; la frase cambia):

```text
respuesta: El tornillo de la brida se aprieta a 12 N·m.
```

**Cómo se lee:** ahora contesta 12 N·m, el dato del procedimiento, y no algo inventado como en el M05-01. El modelo es el mismo; lo que ha cambiado es que tiene el dato delante. Es la «G» de RAG: **generar** a partir de lo recuperado.

### 5 — Comprobar que no se ha inventado nada

**Para qué:** no fiarte de la respuesta solo porque suena bien.

**Qué ocurre:** sacas los números de la respuesta y compruebas que **todos** están en el párrafo. Si alguno no está, el modelo se lo ha inventado y no se enseña.

Pega debajo de `# --- PASO 5`:

```python
numeros_respuesta = set(re.findall(r"\d+", respuesta))
numeros_parrafo = set(re.findall(r"\d+", parrafo))
inventados = numeros_respuesta - numeros_parrafo
print("comprobación:", "OK, todos los números salen del procedimiento" if not inventados else f"NO: inventa {inventados}")
```

**Resultado esperado** (líneas nuevas):

```text
comprobación: OK, todos los números salen del procedimiento
```

**Cómo se lee:** el 12 de la respuesta está en el párrafo: la respuesta se puede enseñar. Es una comprobación sencilla, pero detecta lo más peligroso en planta: un número inventado. Un asistente bien hecho no solo pregunta al modelo; **verifica** lo que contesta.

### 6 — Decide tú: una pregunta que el procedimiento no contesta

**Para qué:** conseguir que el asistente diga «no está» en lugar de inventar.

**Qué ocurre:** cambias `PREGUNTA` por `"¿De qué color es el tornillo de recambio?"` y añades al final este bloque, que decide qué enseñar según cuántas palabras tiene en común el párrafo elegido. Ejecuta con `MINIMO_PALABRAS = 1` y después con `MINIMO_PALABRAS = 2`:

```python
# Si ningún párrafo habla de la pregunta, no se pregunta al modelo
if en_comun < MINIMO_PALABRAS:
    print("asistente: el procedimiento no dice nada sobre eso. Consulta al responsable de la estación.")
else:
    print("asistente:", respuesta)
```

**Resultado esperado** (las líneas que importan):

```text
# MINIMO_PALABRAS = 1 (dos ejecuciones)
párrafo elegido (1 palabras en común): El tornillo de la brida se aprieta a 12 N·m. ...
respuesta: No se proporciona el texto para responder esta pregunta.
asistente: No se proporciona el texto para responder esta pregunta.

respuesta: Blanco
comprobación: OK, todos los números salen del procedimiento
asistente: Blanco

# MINIMO_PALABRAS = 2
asistente: el procedimiento no dice nada sobre eso. Consulta al responsable de la estación.
```

**Cómo se lee:** con 1, el asistente elige el párrafo del par porque comparte la palabra «tornillo». Unas veces el modelo dice que no tiene el dato; otras **se inventa «Blanco»**, y tu comprobación del paso 5 lo deja pasar, porque solo busca números inventados. Con 2, ningún párrafo llega al mínimo y **el asistente dice que no está**, sin enseñar lo que contestó el modelo. No es el modelo el que decide que no sabe: lo decide tu código, con una regla que se puede comprobar. En una versión final, la condición iría antes del paso 4, para no preguntar al modelo en balde. Vuelve a dejar la pregunta del par, `MINIMO_PALABRAS = 1`, y quita el bloque.
## Reto

### 1 — Un párrafo nuevo en el procedimiento

**La situación:** mantenimiento añade al procedimiento de EST-01 un apartado nuevo: «El husillo se lubrica cada 500 horas de trabajo con grasa G-2». Alguien pregunta si hay que reentrenar el modelo para que el asistente lo sepa.

**Qué haces:** en tu asistente de «Constrúyelo tú», añades al final un bloque que mete ese párrafo en la lista `parrafos` y pregunta «¿Cada cuántas horas se lubrica el husillo?», usando tus funciones `elegir` y `generar`. No toques el modelo ni el servicio `llm`.

**Pistas:** `parrafos.append("…")` añade un párrafo a la lista; después, `elegir(pregunta)` y `generar(pregunta, parrafo)` como en los pasos 3 y 4.

**Lo que buscas:** si el asistente contesta bien sin reentrenar nada.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: un párrafo nuevo en el procedimiento, sin tocar el modelo
parrafos.append("El husillo se lubrica cada 500 horas de trabajo con grasa G-2. Anotar la fecha en la hoja de la estación.")
pregunta = "¿Cada cuántas horas se lubrica el husillo?"
nuevo, comun = elegir(pregunta)
r = generar(pregunta, nuevo)
print(f"párrafo elegido ({comun} en común): {nuevo}")
print("respuesta:", r)
```

```text
párrafo elegido (4 en común): El husillo se lubrica cada 500 horas de trabajo con grasa G-2. Anotar la fecha en la hoja de la estación.
respuesta: 500 horas
```

**Contesta bien, y el modelo no ha cambiado en nada.** Lo que sabe el asistente está en el documento, no en el modelo: basta con actualizar el documento. Si lo añadieras de verdad a `infra/linea/docs/procedimiento-est01.md`, también lo usarían `lab m05-03` y `lab preguntar`. **La regla:** para documentación que cambia (procedimientos, fichas técnicas, avisos de calidad), RAG es mucho más práctico que reentrenar: se actualiza editando un texto, y cada respuesta se puede rastrear hasta el párrafo del que salió. Quita el bloque del reto cuando acabes.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la respuesta no contiene el 12` | el modelo pequeño no copió el número | repite. Si el fragmento impreso no tiene el 12, falló la recuperación |
| `FALLO` con error de conexión | `llm` parado | `docker compose ps` y `docker compose up -d llm` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `httpx.ConnectError` en el paso 4 | el contenedor `llm` está parado o cargando | `docker compose up -d llm` y espera a que `/salud` conteste |

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
