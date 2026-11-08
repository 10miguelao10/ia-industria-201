# M05-04 — Automatización mediante agentes

[← Página anterior](M05-03-asistente-documentacion.md) · [Siguiente página →](M05-05-modelos-abiertos.md)

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

## Constrúyelo tú: tu propio agente

**Qué está pasando:** `lab m05-04` responde con un dato vivo de la estación usando una herramienta, y se niega a escribir. Ahora construyes tú el agente: le das una caja de herramientas **solo de lectura**, escribes el código que decide qué herramienta usar para cada petición, dejas una traza de lo que se leyó y pides al modelo que redacte la respuesta con ese dato. Al final le pides algo que no puede hacer, y ves por qué la negativa no depende del modelo.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** conocer lo único que el agente podrá hacer: sus herramientas.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m05_04_mi_agente.py`](../../infra/construye/m05_04_mi_agente.py). Arriba está la **decisión** (`PETICION`); debajo, el paso 1 ya escrito: una sola herramienta, `leer_estacion`, que lee el último estado de la estación, y el diccionario `HERRAMIENTAS`, que es todo lo que el agente tendrá a mano. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_04_mi_agente.py
```

**Resultado esperado:**

```text
herramientas del agente: ['leer_estacion']
```

**Cómo se lee:** una herramienta es una función normal de Python con un nombre y una descripción. El agente no puede hacer nada que no esté en `HERRAMIENTAS`: esa lista es su frontera. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Decidir qué herramienta hace falta

**Para qué:** que la elección de la herramienta la haga tu código, de forma predecible, y no el modelo.

**Qué ocurre:** escribes un plan sencillo: según las palabras de la petición, qué herramienta hay que usar. Si la petición pide **cambiar** algo, el plan no elige ninguna.

Pega debajo de `# --- PASO 2`:

```python
PLAN = {"leer_estacion": ["cómo está", "temperatura", "estado", "vibración", "corriente"]}
CAMBIOS = ["para ", "sube", "baja", "cambia", "escribe", "apaga"]

def elegir_herramienta(peticion):
    texto = peticion.lower()
    if any(palabra in texto for palabra in CAMBIOS):
        return None                                   # pedir un cambio: no hay herramienta para eso
    for herramienta, claves in PLAN.items():
        if any(clave in texto for clave in claves):
            return herramienta
    return None

herramienta = elegir_herramienta(PETICION)
print(f"petición: {PETICION}  ->  herramienta: {herramienta}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
petición: ¿Cómo está la estación EST-01 ahora?  ->  herramienta: leer_estacion
```

**Cómo se lee:** para «¿Cómo está la estación?», el plan elige `leer_estacion`. Este agente decide por **reglas de tu código**; hay agentes en los que lo decide el propio modelo (el glosario los sitúa), más flexibles y más difíciles de controlar. En planta, que lo decida el código es lo prudente: siempre se sabe qué va a hacer.

### 3 — Usar la herramienta y dejar traza

**Para qué:** tener el dato real y poder demostrar después de dónde salió.

**Qué ocurre:** ejecutas la herramienta elegida y escribes una línea en `mi_traza_agente.jsonl` con la hora, la petición, la herramienta y lo que devolvió.

Pega debajo de `# --- PASO 3`:

```python
dato = HERRAMIENTAS[herramienta]() if herramienta else None
with open("/data/mi_traza_agente.jsonl", "a") as traza:
    traza.write(json.dumps({"hora": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "peticion": PETICION, "herramienta": herramienta, "dato": dato}, ensure_ascii=False) + "\n")
print("dato de la herramienta:", dato)
```

**Resultado esperado** (línea nueva; cambian los valores):

```text
dato de la herramienta: {'pieza': 'P2249', 'temperatura_c': 61.83, 'vibracion_mm_s': 0.28, 'corriente_a': 4.06}
```

**Cómo se lee:** el dato es de **ahora**: la última carcasa de la estación. Ábrelo en VS Code, `infra/data/mi_traza_agente.jsonl`: cada ejecución añade una línea. Si alguien pregunta mañana de dónde sacó el agente una temperatura, la traza lo dice.

### 4 — Redactar la respuesta con el dato

**Para qué:** que el modelo haga lo que sabe hacer, redactar, con un dato que no se inventa él.

**Qué ocurre:** si hay dato, das al modelo el resultado de la herramienta y le pides una frase para el supervisor, copiando los números. Si no hay herramienta para la petición, el agente responde sin preguntar al modelo.

Pega debajo de `# --- PASO 4`:

```python
if dato is None:
    respuesta = "No puedo hacer eso: no tengo ninguna herramienta que cambie la estación. Avisa al responsable de turno."
else:
    mensajes = [{"role": "system", "content": "Redacta una frase para el supervisor. Copia los números exactamente."},
                {"role": "user", "content": f"Petición: {PETICION}\nDato de {herramienta}: {json.dumps(dato)}"}]
    r = httpx.post("http://llm:8088/v1/chat/completions", json={"messages": mensajes, "max_tokens": 60}, timeout=60)
    respuesta = r.json()["choices"][0]["message"]["content"].strip()
print("agente:", respuesta)
```

**Resultado esperado** (línea nueva; la frase cambia):

```text
agente: La estación EST-01 se encuentra en un estado de 61.83°C con una vibración de 0.28 mm/s y una corriente de 4.06 a.
```

**Cómo se lee:** una frase con la temperatura de la última carcasa. El modelo **no ha leído la estación**: ha redactado con lo que leyó tu código. Es el reparto de un agente bien hecho: el código obtiene los datos; el modelo los cuenta.

### 5 — Comprobar que ha copiado bien el dato

**Para qué:** no enseñar una respuesta en la que el modelo ha cambiado el número.

**Qué ocurre:** compruebas que **cada número** que devolvió la herramienta aparece tal cual en la frase del modelo.

Pega debajo de `# --- PASO 5`:

```python
if dato is not None:
    numeros = [str(v) for v in dato.values() if isinstance(v, (int, float))]   # los números que dio la herramienta
    faltan = [n for n in numeros if n not in respuesta]
    print("comprobación:", "OK, todos los números son los de la herramienta" if not faltan else f"NO: faltan o cambian {faltan}; no enseñar")
```

**Resultado esperado** (líneas nuevas):

```text
comprobación: OK, todos los números son los de la herramienta
```

**Cómo se lee:** esta vez los ha copiado todos, porque se los has dado delante y le has pedido que los copie. Pero un modelo pequeño a veces redondea, cambia un dígito o se deja uno, y en planta un número cambiado es peor que ninguno. Si la comprobación falla, la aplicación enseñaría el dato de la herramienta sin la frase.

### 6 — Decide tú: pedirle que cambie algo

**Para qué:** comprobar que el agente no puede actuar sobre la planta, se lo pida quien se lo pida.

**Qué ocurre:** cambias `PETICION` por `"Para la estación EST-01 ahora mismo."` y ejecutas.

**Resultado esperado** (líneas que cambian):

```text
petición: Para la estación EST-01 ahora mismo.  ->  herramienta: None
dato de la herramienta: None
agente: No puedo hacer eso: no tengo ninguna herramienta que cambie la estación. Avisa al responsable de turno.
```

**Cómo se lee:** el plan no elige ninguna herramienta, la traza lo registra (`"herramienta": null`) y el agente contesta que no puede, **sin preguntar al modelo**. La negativa no depende de que el modelo «entienda» que no debe: no hay ninguna herramienta que escriba, así que aunque el modelo quisiera, no tendría con qué. La forma más segura de que un agente no toque el proceso es no darle con qué hacerlo. Vuelve a dejar la petición de antes.
## Reto

### 1 — Una segunda herramienta, también de lectura

**La situación:** el supervisor quiere preguntar al agente «¿Cuántas carcasas se han fabricado en el último minuto?». Con `leer_estacion` no se puede contestar: solo da la última carcasa. Hace falta otra herramienta. Alguien propone, de paso, añadir una que escriba el registro de paro, «por si acaso».

**Qué haces:** en tu agente de «Constrúyelo tú», añades una herramienta `carcasas_ultimo_minuto` que cuente en el [histórico](../glosario/01-datos-arquitectura.md#historico), en solo lectura, las carcasas del último minuto; la registras en `HERRAMIENTAS` y en el `PLAN` con sus palabras clave, y cambias la `PETICION`. La de escribir el paro, no la añades.

**Pistas:**

- La herramienta abre `historial.sqlite` con `mode=ro`, como el M01-02, y cuenta las filas de `lecturas` de los últimos 60 s: `WHERE ts >= strftime('%Y-%m-%dT%H:%M:%S', 'now', '-60 seconds')`.
- Va debajo de `leer_estacion`, en el paso 1, con `HERRAMIENTAS["carcasas_ultimo_minuto"] = carcasas_ultimo_minuto`.
- En el `PLAN` del paso 2, añade `"carcasas_ultimo_minuto": ["cuántas carcasas", "producción", "fabricado"]`.

**Lo que buscas:** que el agente conteste con el número real, y que la comprobación del paso 5 siga funcionando con la herramienta nueva.

<details>
<summary>Ver solución</summary>

Debajo de `leer_estacion`, en el paso 1:

```python
def carcasas_ultimo_minuto():
    """Cuenta las carcasas guardadas en el histórico en el último minuto. Solo lectura."""
    import sqlite3
    with sqlite3.connect("file:/data/historial.sqlite?mode=ro", uri=True) as con:
        n = con.execute("SELECT COUNT(*) FROM lecturas WHERE ts >= strftime('%Y-%m-%dT%H:%M:%S', 'now', '-60 seconds')").fetchone()[0]
    return {"carcasas_ultimo_minuto": n}

HERRAMIENTAS["carcasas_ultimo_minuto"] = carcasas_ultimo_minuto
```

Y el `PLAN` del paso 2:

```python
PLAN = {"leer_estacion": ["cómo está", "temperatura", "estado", "vibración", "corriente"],
        "carcasas_ultimo_minuto": ["cuántas carcasas", "producción", "fabricado"]}
```

```text
herramientas del agente: ['leer_estacion', 'carcasas_ultimo_minuto']
petición: ¿Cuántas carcasas se han fabricado en el último minuto?  ->  herramienta: carcasas_ultimo_minuto
dato de la herramienta: {'carcasas_ultimo_minuto': 61}
agente: "Petición: ¿Cuántas carcasas se han fabricado en el último minuto? Dato de carcasas_ultimo_minuto: 61"
comprobación: OK, todos los números son los de la herramienta
```

**El número es el real**, 61 carcasas, y la comprobación lo confirma. La redacción, en cambio, es mala: esta vez el modelo ha repetido lo que le diste en lugar de escribir una frase. Pasa a menudo con un modelo de 0,5 B; por eso lo que se comprueba es el dato, y la frase es secundaria.

**La herramienta de paro no se añade.** Cada herramienta nueva amplía lo que el agente puede hacer, y una que escriba en el proceso convierte cualquier malentendido en una acción sobre la línea. **La regla:** a un agente se le dan solo herramientas de lectura, una por cada dato que necesita; las acciones sobre la planta las decide y las ejecuta una persona o el automatismo, como verás en el M06-03 y el M07-03.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la frase no incluye el valor medido` | el modelo no copió el número | repite el comando |
| `FileNotFoundError … estado.json` | el sensor no ha arrancado nunca | `docker compose up -d sensor` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/estado.json` | la estación no ha publicado ninguna carcasa todavía | `docker compose up -d sensor` y espera unos segundos |

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
