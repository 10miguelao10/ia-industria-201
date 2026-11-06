# M05-02 — Integración desde aplicaciones

[← Página anterior](M05-01-modelo-local.md) · [Siguiente página →](M05-03-asistente-documentacion.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **integra un modelo generativo en una aplicación**: qué contrato usa, cómo debe comportarse la aplicación cuando el modelo responde mal o no responde, y cómo se hace robusta esa integración.

### Prerrequisitos

- El contenedor `llm` en marcha y `/salud` en `ok` (M05-01).

### Qué está pasando

El técnico no va a abrir una terminal para hablar con el modelo: usará una **aplicación**, por ejemplo en la tablet del puesto o en la intranet de mantenimiento. Esa aplicación habla con el modelo por **HTTP**, mandando la pregunta y recibiendo la respuesta en JSON, igual que con cualquier otro servicio de la planta.

También tiene que saber **fallar bien**. Si el servicio del modelo está caído, la aplicación debe decir «no hay servicio» y no quedarse colgada ni enseñar un texto [inventado](../glosario/04-ia-generativa.md#alucinacion).

### 0 — Ver el contrato del servicio

**Qué ocurre:** antes de llamar al servicio, miras qué espera. Abre <http://localhost:8088/docs> y despliega `POST /v1/chat/completions`.

**Qué ves:** la petición lleva `messages` (la conversación, con `role` y `content`) y `max_tokens` (el máximo de trozos de palabra de la respuesta). Es todo lo que una aplicación necesita saber del modelo.

### 1 — Llamar al modelo como lo haría una aplicación

Vas a mandar una pregunta al servicio con `curl`, igual que lo haría cualquier programa. Lo que viaja es un JSON con los mensajes; lo que vuelve, un JSON con la respuesta.

```bash
curl -s http://localhost:8088/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
        "messages": [{"role": "user", "content": "Explica en una frase qué es un PLC."}],
        "max_tokens": 60
      }'
```

**Resultado esperado** (el texto varía):

```json
{"id":"chatcmpl-…","object":"chat.completion","model":"/modelos/qwen2.5-0.5b-instruct-q4_k_m.gguf","choices":[{"index":0,"message":{"role":"assistant","content":"Un PLC, o Programmable Logic Controller, es un sistema de control de procesos electrónicos diseñado para controlar procesos industriales…"},"finish_reason":"length"}],"usage":{"prompt_tokens":41,"completion_tokens":60,"total_tokens":101}}
```

- `content` es el texto generado.
- `finish_reason: "length"` indica que se cortó al llegar a `max_tokens`.
- `usage` cuenta los [tokens](../glosario/04-ia-generativa.md#token) (trozos de palabra) de entrada y de salida.

### 2 — Una aplicación que también sabe fallar

Vas a ejecutar una aplicación mínima: pide texto al servicio y después llama a un servicio que no existe. Tiene que fallar con un error de red claro, no con un texto inventado.

```bash
docker compose --profile lab run --rm --no-deps lab m05-02
```

📋 Ficha del comando [`m05-02`](../comandos-lab.md#m05-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (la frase del modelo varía):

```text
aplicacion: Mi nombre es Qwen, un modelo de lenguaje artificial creado por Alibaba Cloud. …
servicio caído: ConnectError
OK m05-02: la aplicación habla con el servicio local y avisa si no está
```

Le pidió «di solo la palabra estacion» y contestó otra cosa: un modelo de 0,5B no siempre obedece. Lo verás de nuevo en M05-03.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
respuesta = httpx.post(
    f"{LLM_URL}/v1/chat/completions",
    json={"messages": [{"role": "user", "content": "Di solo la palabra estacion"}], "max_tokens": 60},
    timeout=180,                     # sin límite de tiempo, la aplicación podría quedarse colgada
)
texto = respuesta.json()["choices"][0]["message"]["content"]

try:
    httpx.get("http://servicio-inexistente:9/salud", timeout=2)
except httpx.HTTPError as exc:
    print(f"servicio caído: {type(exc).__name__}")    # se informa, no se inventa
```

</details>

## Comprueba tu entendimiento

**Mismo servicio**

Compara el puerto de esta llamada con el de M05-01.

→ Los dos usan el 8088. Cambia quién pide, no el modelo.

## Experimenta: una respuesta cortada

**Qué ocurre:** limitas la respuesta a 10 tokens y comparas con 100. Una aplicación tiene que saber detectar que la respuesta no está completa.

```bash
for t in 10 100; do
  curl -s http://localhost:8088/v1/chat/completions -H 'Content-Type: application/json' \
    -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Explica qué es un PLC.\"}], \"max_tokens\": $t}"
  echo
done
```

**Resultado esperado** (extracto de cada respuesta):

```text
"content":"Un PLC (Programmable Logic Controller) es"  …  "finish_reason":"length"  …  "completion_tokens":10
"content":"Un PLC (Programmable Logic Controller) es un dispositivo de control …"  …  "finish_reason":"length"  …  "completion_tokens":100
```

**Cómo se lee:** con 10 tokens, la frase se queda a medias: «Un PLC (Programmable Logic Controller) es». `finish_reason: "length"` avisa de que se ha cortado por el límite, no porque terminara. Una aplicación que enseñe eso al técnico sin avisar le está dando media respuesta.

## Mejora: fallar rápido y avisar

**Qué ocurre:** el cliente de este laboratorio espera hasta 180 segundos. Pruebas qué ve una aplicación con un **tiempo máximo corto** cuando el servicio está caído.

```bash
# Para el modelo
docker compose stop llm

# Una aplicación con 3 s de paciencia
curl -s --max-time 3 http://localhost:8088/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "hola"}]}' || echo "AVISO al técnico: el asistente no está disponible"

# Vuelve a arrancarlo
docker compose start llm
```

**Resultado esperado:**

```text
AVISO al técnico: el asistente no está disponible
```

**Cómo se lee:** en menos de 3 segundos, la aplicación sabe que no hay servicio y lo dice. Es la diferencia entre una tablet que se queda «pensando» y una que dice «el asistente no está; usa el procedimiento en papel».

## Constrúyelo tú: tu propia aplicación que sabe fallar

**Qué está pasando:** en este lab has llamado al modelo como una aplicación y has visto qué pasa cuando el servicio no está. Ahora escribes tú la parte de la aplicación que habla con el modelo, y la haces **robusta**: que avise si la respuesta llega cortada, si el servicio no existe o si tarda demasiado, y que el técnico vea siempre un mensaje claro en lugar de una pantalla colgada o un error de Python.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** tener a la vista las tres decisiones que hacen robusta o frágil a una aplicación.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m05_02_mi_aplicacion.py`](../../infra/construye/m05_02_mi_aplicacion.py). Arriba están las **decisiones**: dónde está el servicio, cuánto puede escribir y cuánto se espera. El paso 1 ya escrito prepara la petición, con unas instrucciones de sistema que piden respuestas cortas. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_02_mi_aplicacion.py
```

**Resultado esperado:**

```text
la aplicación preguntará a http://llm:8088 con un máximo de 60 tokens y 20 s de espera
```

**Cómo se lee:** todavía no pregunta nada. Las tres decisiones de arriba son las que vas a poner a prueba: casi todos los fallos de una aplicación con un modelo vienen de una de ellas. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Preguntar y leer por qué terminó

**Para qué:** saber, además de la respuesta, si la respuesta está completa.

**Qué ocurre:** mandas la petición y guardas dos cosas: el texto y `finish_reason`, que dice por qué dejó de escribir el modelo: `stop` si terminó él, `length` si llegó al máximo de tokens.

Pega debajo de `# --- PASO 2`:

```python
def consultar(pregunta):
    r = httpx.post(f"{SERVICIO}/v1/chat/completions", json=peticion(pregunta), timeout=TIEMPO_MAX_S)
    r.raise_for_status()                                  # un error del servicio se convierte en excepción
    eleccion = r.json()["choices"][0]
    return eleccion["message"]["content"].strip(), eleccion["finish_reason"]

texto, motivo = consultar("¿Qué es un PLC?")
print(f"motivo={motivo}  respuesta={texto}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (línea nueva; cambia el texto):

```text
motivo=stop  respuesta=Un PLC (Programmable Logic Controller) es un sistema de control de procesamiento digital que permite la programación de logicos y la manipulación de datos.
```

**Cómo se lee:** con 60 tokens, a veces le da para terminar (`stop`) y a veces no (`length`). Una aplicación que solo mira el texto no distingue una respuesta completa de una cortada; con `finish_reason`, sí.

### 3 — Un mensaje claro para cada caso

**Para qué:** que el técnico vea siempre algo comprensible, pase lo que pase con el servicio.

**Qué ocurre:** escribes la función que usará la pantalla: llama a `consultar` y, en vez de dejar que un error pare la aplicación, convierte cada fallo en un aviso. Una respuesta cortada se enseña, pero avisando.

Pega debajo de `# --- PASO 3`:

```python
def responder(pregunta):
    try:
        texto, motivo = consultar(pregunta)
    except httpx.ConnectError:
        return "AVISO: el asistente no está disponible. Usa el procedimiento en papel."
    except httpx.TimeoutException:
        return f"AVISO: el asistente no ha respondido en {TIEMPO_MAX_S} s. Inténtalo más tarde."
    except httpx.HTTPStatusError as error:
        return f"AVISO: el asistente ha dado un error ({error.response.status_code})."
    if motivo == "length":
        return texto + "  [respuesta incompleta: pide una pregunta más concreta]"
    return texto

print("pantalla:", responder("¿Qué es un PLC?"))
```

**Resultado esperado** (línea nueva; cambia el texto):

```text
pantalla: Un PLC (Programmable Logic Controller) es un sistema de control de procesamiento digital que permite la programación de logicos y la manipulación de datos.
```

**Cómo se lee:** con el servicio funcionando, la pantalla enseña la respuesta, y si se cortó lo dice. El código de la pantalla ya no puede «colgarse» con un error: cada fallo tiene su mensaje. Los pondrás a prueba uno a uno en los pasos siguientes.

### 4 — Decide tú: una respuesta cortada

**Para qué:** comprobar que la aplicación avisa de que falta parte de la respuesta.

**Qué ocurre:** cambias `MAX_TOKENS = 60` por `MAX_TOKENS = 10` y ejecutas.

**Resultado esperado** (líneas que cambian; cambia el texto):

```text
motivo=length  respuesta=Un PLC (Programmable Logic Controller) es
pantalla: Un PLC (Programmable Logic Controller) es  [respuesta incompleta: pide una pregunta más concreta]
```

**Cómo se lee:** el modelo se queda a media frase y la pantalla lo dice. Sin el aviso, el técnico leería una frase incompleta como si fuera la respuesta. Vuelve a dejar `MAX_TOKENS = 60`.

### 5 — Decide tú: el servicio no está

**Para qué:** comprobar lo que ve el técnico cuando el modelo está caído.

**Qué ocurre:** cambias `SERVICIO = "http://llm:8088"` por `SERVICIO = "http://llm:9999"`, un puerto donde no escucha nadie, y ejecutas. Es lo mismo que ve la aplicación si el contenedor `llm` está parado.

**Resultado esperado** (última línea, con el paso 2 sin comentar):

```text
httpx.ConnectError: [Errno 111] Connection refused
```

**Cómo se lee:** el paso 2, que llama directamente a `consultar`, **para el programa con un error de Python**: es lo que vería una aplicación sin protección, una pantalla rota. Ahora comenta (pon `#` delante de) las dos últimas líneas del bloque del paso 2 y vuelve a ejecutar:

```text
pantalla: AVISO: el asistente no está disponible. Usa el procedimiento en papel.
```

La pantalla del paso 3 enseña el aviso al instante. Vuelve a dejar `SERVICIO = "http://llm:8088"`, pero deja comentadas las dos líneas del paso 2 para el paso siguiente.

### 6 — Decide tú: no esperar para siempre

**Para qué:** comprobar que la aplicación se rinde a tiempo cuando el modelo tarda.

**Qué ocurre:** cambias `TIEMPO_MAX_S = 20` por `TIEMPO_MAX_S = 0.3` y ejecutas, con las dos líneas del paso 2 todavía comentadas.

**Resultado esperado** (la línea del paso 3):

```text
pantalla: AVISO: el asistente no ha respondido en 0.3 s. Inténtalo más tarde.
```

**Cómo se lee:** el modelo necesita algo más de medio segundo para 60 tokens, así que la aplicación se rinde y avisa. Es lo que pasaría con el servicio sobrecargado: sin tiempo máximo, la pantalla se quedaría «pensando» hasta 180 s. El tiempo máximo correcto lo eliges en el reto 1, midiendo. Vuelve a dejar `TIEMPO_MAX_S = 20` y descomenta el paso 2.
## Reto

### 1 — Elegir el tiempo máximo midiendo

**La situación:** el cliente de los comandos del curso espera hasta 180 s. En tu aplicación has puesto 20 s, y en el paso 6 viste que con 0,3 s se rinde antes de tiempo. ¿Cuál es el valor bueno?

**Qué haces:** al final de tu script (con las líneas del paso 2 descomentadas o no, da igual), mides cuánto tarda el modelo en contestar a ocho preguntas cortas distintas y propones un tiempo máximo.

**Pistas:** `time.time()` antes y después de cada `consultar(pregunta)`; guarda los tiempos en una lista y ordénala; una regla habitual es dar el doble del peor tiempo medido.

**Lo que buscas:** el tiempo máximo que no corta las respuestas normales y no deja al técnico esperando de más.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: medir cuánto tarda de verdad antes de fijar el tiempo máximo
import time
preguntas = ["¿Qué es un PLC?", "¿Para qué sirve un husillo?", "¿Qué es el OEE?", "¿Qué es una microparada?",
             "¿Qué mide un sensor de vibración?", "¿Qué es MQTT?", "¿Qué es una consigna?", "¿Qué es un SCADA?"]
tiempos = []
for p in preguntas:
    inicio = time.time()
    consultar(p)
    tiempos.append(time.time() - inicio)
tiempos.sort()
print(f"tiempos: mínimo={tiempos[0]:.1f} s  mediana={tiempos[len(tiempos) // 2]:.1f} s  máximo={tiempos[-1]:.1f} s")
print(f"tiempo máximo propuesto (el doble del peor): {2 * tiempos[-1]:.0f} s")
```

```text
tiempos: mínimo=0.4 s  mediana=0.6 s  máximo=0.7 s
tiempo máximo propuesto (el doble del peor): 1 s
```

Con respuestas de 60 tokens como máximo, el modelo nunca pasa de un segundo, así que **20 s es demasiado** y 180 s, absurdo: un servicio caído o atascado tendría al técnico esperando sin saber nada. Un tiempo de unos pocos segundos deja margen y avisa enseguida. **La regla:** el tiempo máximo de una aplicación se fija midiendo el servicio en condiciones normales, con la longitud de respuesta que se va a pedir, y se revisa si cambia el modelo o el equipo. Si subes `MAX_TOKENS`, tienes que volver a medir.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `Connection refused` en el paso 1 | `llm` todavía no está listo | espera a que `/salud` conteste |
| no aparece `servicio caído` | el host inventado resolvió por error | no cambies el código del paso |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `httpx.ConnectError` en el paso 2 con `SERVICIO` bien puesto | el contenedor `llm` está parado o todavía cargando | `docker compose up -d llm` y espera a que `/salud` conteste |

## Conclusiones

### Qué es integrar un modelo en una aplicación

La aplicación (la tablet del técnico, la intranet de mantenimiento) no ve el modelo: ve un **servicio HTTP**. Le manda un JSON con los mensajes y recibe otro con la respuesta, igual que con cualquier otro servicio de la planta.

### Cómo debe comportarse la aplicación

| Situación | Comportamiento correcto |
|-----------|-------------------------|
| El modelo responde | Mostrar el texto y saber si se cortó (`finish_reason: "length"`) |
| El modelo responde otra cosa | No darlo por bueno: un modelo pequeño no siempre obedece |
| El servicio no está | Decir «no hay servicio», con un error claro (`ConnectError`) |
| El servicio tarda | Cortar a un tiempo máximo y avisar, no quedarse colgada |

### Sus riesgos y cómo los has visto

| Riesgo | Cómo lo has visto |
|--------|-------------------|
| El modelo no sigue la instrucción | Le pidieron una palabra y contestó otra cosa |
| La respuesta se corta | `finish_reason: "length"` al llegar a `max_tokens` |
| La aplicación se queda colgada | El cliente del lab espera hasta 180 s: demasiado para un operario |

### Cómo se hace robusta

- **Tiempo máximo corto** y visible para el usuario.
- **Validar la respuesta** antes de usarla: formato, longitud, que contenga lo que se pidió.
- **Mensaje claro cuando falla** y, si hace falta, un camino alternativo (el procedimiento en papel).

### En una frase

> 🔑 Integrar un modelo es integrar un servicio más: contrato, tiempo máximo, validación de la respuesta y qué pasa cuando no responde.
