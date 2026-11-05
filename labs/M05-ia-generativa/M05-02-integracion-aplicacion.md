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

También tiene que saber **fallar bien**. Si el servicio del modelo está caído, la aplicación debe decir «no hay servicio» y no quedarse colgada ni enseñar un texto inventado.

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
- `usage` cuenta los tokens (trozos de palabra) de entrada y de salida.

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

## Reto

### 1 — Tiempo máximo

Si el servicio se cae a media respuesta, ¿cuánto espera esta aplicación?

<details>
<summary>Ver solución</summary>

Hasta 180 s, el `timeout` del cliente. En un puesto real el límite debe ser más corto y el operario tiene que ver en pantalla que no hubo respuesta.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `Connection refused` en el paso 1 | `llm` todavía no está listo | espera a que `/salud` conteste |
| no aparece `servicio caído` | el host inventado resolvió por error | no cambies el código del paso |

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
