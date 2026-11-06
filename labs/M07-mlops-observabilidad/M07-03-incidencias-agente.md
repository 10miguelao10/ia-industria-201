# M07-03 — Gestión de incidencias con un agente local

[← Página anterior](M07-02-monitorizacion.md) · [Siguiente página →](../M08-ciberseguridad-gobierno/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **procesan [incidencias](../glosario/05-operacion-gobierno.md#incidencia) con un [agente](../glosario/04-ia-generativa.md#agente) y un modelo local**: qué parte del trabajo hace el código y qué parte el modelo, cómo debe ser un agente que diagnostica sin tocar el proceso, cómo se detecta que su diagnóstico no es fiable y cómo se mejora.

### Prerrequisitos

- M01-03 hecho: `prometheus` en marcha, con la estación y el archivador publicando [métricas](../glosario/02-observabilidad.md#metrica).
- M05-01 hecho: el fichero del modelo en `infra/modelos/`.
- `mosquitto`, `sensor`, `archivador`, `prometheus` y `llm` en marcha. Para el panel si lo tienes arrancado: el modelo pide memoria.

### Qué está pasando

En el M01-03 las [alertas](../glosario/02-observabilidad.md#alerta) aparecían en [Prometheus](../glosario/02-observabilidad.md#prometheus), pero alguien tenía que verlas, entender qué significaban, buscar los datos y decidir qué hacer. De madrugada, con varias alertas a la vez, eso cuesta.

Un **agente de incidencias** hace el primer trabajo: cuando hay una alerta, **reúne los datos**, **consulta el procedimiento** y **redacta un diagnóstico con la acción propuesta**. No ejecuta nada: la acción la decide y la hace una persona.

```
 alerta en Prometheus
      │
      ▼
 1. EL CÓDIGO elige las herramientas según la alerta y las ejecuta (todas de lectura)
      │   estado de los servicios · segundos sin guardar · carcasas perdidas · último registro
      ▼
 2. EL CÓDIGO busca en el runbook la sección de esa alerta
      │
      ▼
 3. EL MODELO LOCAL redacta el diagnóstico con esos datos y ese texto
      │
      ▼
 informe en data/incidencias.jsonl  ──▶  una persona lo revisa y actúa
```

El reparto es deliberado. Ya viste en el M05 que un modelo de 0,5B no siempre obedece: por eso **la elección de herramientas no se la dejamos al modelo**. El código decide qué mirar; el modelo solo pone las palabras.

El **[runbook](../glosario/04-ia-generativa.md#runbook)** (`infra/linea/docs/runbook-est01.md`) es el documento que dice qué hacer ante cada alerta. Es el equivalente del procedimiento del M05-03, pero para incidencias.

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Sistema de alertas (Alertmanager, [SCADA](../glosario/01-datos-arquitectura.md#scada)) | Prometheus del M01-03 |
| Runbook o procedimiento de incidencias | `infra/linea/docs/runbook-est01.md` |
| Asistente de guardia o ticket de incidencia | El comando `m07-03` y `data/incidencias.jsonl` |

### 1 — Leer el runbook

**Qué ocurre:** lees lo que hay que hacer ante cada alerta. El agente no sabe nada que no esté aquí o en los datos que mide.

```bash
cat linea/docs/runbook-est01.md
```

**Resultado esperado** (extracto):

```text
## HistoricoSinDatos

El archivador está vivo pero no guarda registros. Causa habitual: el broker se reinició y el archivador no renovó su suscripción.
Acción: reiniciar el archivador (docker compose restart archivador) y comprobar que vuelve a guardar.
Si se repite, corregir la reconexión del archivador.
```

### 2 — Sin incidencias, el agente no tiene nada que hacer

**Qué ocurre:** lanzas el agente con la línea funcionando bien. Consulta las alertas activas en Prometheus y no encuentra ninguna.

```bash
# Arranca lo que necesita el agente
docker compose up -d mosquitto sensor archivador prometheus llm

docker compose --profile lab run --rm --no-deps lab m07-03
```

📋 Ficha del comando [`m07-03`](../comandos-lab.md#m07-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
FALLO: no hay alertas activas; provoca una incidencia primero
```

Aquí el `FALLO` es lo esperado: no hay nada que diagnosticar.

> Si en el M01-03 corregiste `archivador.py`, el reinicio del [broker](../glosario/01-datos-arquitectura.md#broker) ya no deja de guardar. Para ver la incidencia completa, vuelve al archivador original con `git checkout linea/archivador.py` y `docker compose restart archivador`.

### 3 — Provocar una incidencia

**Qué ocurre:** reinicias el broker, como en el reto 2 del M01-03. El archivador sigue vivo pero deja de guardar, y Prometheus lo detecta.

```bash
docker compose restart mosquitto
# … espera 40 segundos …
```

Abre <http://localhost:9090/alerts>.

**Resultado esperado:** `HistoricoSinDatos` y `RegistrosPerdidos` en **firing**.

### 4 — El agente diagnostica

**Qué ocurre:** lanzas el agente. Para cada alerta activa, el código reúne los datos con sus herramientas, busca la sección del runbook y pide al modelo local que redacte el diagnóstico.

```bash
docker compose --profile lab run --rm --no-deps lab m07-03
```

**Resultado esperado** (cambian los números y la redacción del diagnóstico):

```text
== HistoricoSinDatos (critica)
herramientas: estado_servicios, retraso_historico, perdida_ultimo_minuto, ultimo_registro
hechos: {"sensor": "vivo", "archivador": "vivo", "segundos_sin_guardar": 48, "carcasas_sin_guardar_ultimo_minuto": 50, "ultimo_registro": "P0022 a las 2026-11-05T12:35:49+00:00"}
diagnóstico: El archivador está vivo pero no guarda registros. El broker se reinició y el archivador no renovó su suscripción. El runbook propone reiniciar el archivador y comprobar que vuelve a guardar. Si se repite, corregir la reconexión del archivador.
== RegistrosPerdidos (critica)
herramientas: estado_servicios, retraso_historico, perdida_ultimo_minuto
hechos: {"sensor": "vivo", "archivador": "vivo", "segundos_sin_guardar": 50, "carcasas_sin_guardar_ultimo_minuto": 50}
diagnóstico: La estación fabrica más carcasas de las que llegan al histórico. El broker y el archivador están en marcha y el archivador guarda. Conciliar la pérdida.
OK m07-03: 2 incidencia(s) diagnosticada(s) en incidencias.jsonl; ninguna acción ejecutada
```

Tarda unos segundos: el modelo redacta un diagnóstico por cada alerta, en la CPU del puesto.

**Cómo se lee:**

| Línea | Quién la produce | ¿Te puedes fiar? |
|-------|------------------|------------------|
| `herramientas` | El código, según la alerta | Sí: es una tabla fija (`PLAN` en `cli.py`) |
| `hechos` | Las herramientas, midiendo Prometheus y el [histórico](../glosario/01-datos-arquitectura.md#historico) | Sí: son medidas |
| `diagnóstico` | El modelo local | **Hay que comprobarlo contra los hechos** |

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m07_03</code>)</summary>

```python
# Qué herramientas usa el agente para cada alerta. Lo decide el código, no el modelo.
PLAN = {
    "ArchivadorCaido": ["estado_servicios", "ultimo_registro"],
    "HistoricoSinDatos": ["estado_servicios", "retraso_historico", "perdida_ultimo_minuto", "ultimo_registro"],
    "RegistrosPerdidos": ["estado_servicios", "retraso_historico", "perdida_ultimo_minuto"],
    ...
}

for alerta in activas:                                   # las alertas en firing de Prometheus
    nombre = alerta["labels"]["alertname"]
    hechos = {}
    for herramienta in PLAN.get(nombre, ["estado_servicios"]):
        hechos.update(HERRAMIENTAS[herramienta]())       # 1. medir (todo de lectura)
    procedimiento = _runbook(nombre)                     # 2. la sección del runbook
    diagnostico = _chat(                                 # 3. el modelo solo redacta
        f"Alerta: {nombre}. Datos medidos: {hechos}. Runbook: {procedimiento} ...",
        "Usa solo los datos y el runbook. No inventes cifras. No ejecutes nada: solo propones.",
    )
    # se añade el informe a data/incidencias.jsonl con estado "propuesta pendiente de una persona"
```

Ninguna herramienta escribe, reinicia ni para nada.

</details>

### 5 — Revisar el diagnóstico contra los hechos

**Qué ocurre:** haces lo que haría el técnico de guardia antes de actuar: comprobar que lo que dice el agente cuadra con lo que se ha medido.

Mira el segundo diagnóstico de la salida de ejemplo:

> «El broker y el archivador están en marcha **y el archivador guarda**.»

y los hechos de esa misma alerta:

```text
"segundos_sin_guardar": 50
```

**El diagnóstico se contradice con los datos.** El archivador lleva 50 segundos sin guardar. El modelo ha tomado la acción del runbook («comprobar que el archivador guarda») y la ha escrito como si fuera un hecho.

Fíjate también en el primer diagnóstico: «El broker se reinició» no es una medida, sino la **causa habitual** que dice el runbook. Aquí acierta porque lo has provocado tú, pero el agente no lo ha comprobado.

Con un modelo tan pequeño, en cada ejecución pueden salir errores distintos o ninguno. La regla no cambia: **las cifras se miran en `hechos`; el diagnóstico es una ayuda para leerlas**.

### 6 — Actuar, como persona

**Qué ocurre:** decides y ejecutas la acción que propone el runbook. El agente no lo hace por ti.

```bash
docker compose restart archivador
# … espera 15 segundos …
docker compose --profile lab run --rm --no-deps lab m07-03
```

**Resultado esperado:** `HistoricoSinDatos` desaparece enseguida. `RegistrosPerdidos` puede seguir un minuto (su ventana de cálculo). Cuando se apagan las dos:

```text
FALLO: no hay alertas activas; provoca una incidencia primero
```

## Comprueba tu entendimiento

**Quién decide qué**

¿Quién eligió consultar el «último registro» para `HistoricoSinDatos`: el modelo o el código?

→ El código, en la tabla `PLAN`. El modelo no elige herramientas ni ejecuta nada: solo redacta.

## Investiga el registro de incidencias

**Qué ocurre:** cada diagnóstico queda en `data/incidencias.jsonl`, una línea por incidencia. Es la [trazabilidad](../glosario/05-operacion-gobierno.md#trazabilidad) del agente: qué alerta, qué midió, qué dijo y en qué estado quedó.

```bash
tail -1 data/incidencias.jsonl
```

**Resultado esperado:**

```json
{"ts": "2026-11-05T12:36:41Z", "alerta": "RegistrosPerdidos", "severidad": "critica", "herramientas": ["estado_servicios", "retraso_historico", "perdida_ultimo_minuto"], "hechos": {"sensor": "vivo", "archivador": "vivo", "segundos_sin_guardar": 50, "carcasas_sin_guardar_ultimo_minuto": 50}, "diagnostico": "…", "estado": "propuesta pendiente de una persona"}
```

**Pregunta:** si mañana alguien pregunta por qué se reinició el archivador a las 12:37, ¿qué te dice este registro y qué no?

<details>
<summary>Ver solución</summary>

Dice qué alerta saltó, qué se midió y qué propuso el agente. **No dice** quién decidió reiniciar ni cuándo: el estado se queda en «propuesta pendiente de una persona». En una herramienta real, la persona que actúa cerraría la incidencia con su nombre y la acción hecha.

</details>

## Experimenta: cambia el runbook

**Qué ocurre:** el agente propone lo que dice el runbook. Si cambias el runbook, cambia la propuesta, sin tocar el código ni el modelo.

En `infra/linea/docs/runbook-est01.md`, en la sección `## RegistrosPerdidos`, añade al final esta línea:

```text
Si la pérdida supera 30 carcasas, avisar a calidad: ese tramo no tendrá trazabilidad.
```

Provoca otra vez la incidencia y lanza el agente:

```bash
docker compose restart mosquitto
# … espera 40 segundos …
docker compose --profile lab run --rm --no-deps lab m07-03
```

**Resultado esperado:** el diagnóstico de `RegistrosPerdidos` menciona ahora el aviso a calidad. Comprueba en `hechos` si la pérdida supera de verdad las 30 carcasas: es el agente quien lo compara, y puede equivocarse.

Al terminar, `docker compose restart archivador` para recuperar el histórico.

## Mejora el agente

**Qué ocurre:** para `RegistrosPerdidos`, el agente no mira cuál fue la última carcasa guardada, que es un dato útil para saber desde cuándo se pierde. Vas a añadirle esa herramienta.

En `infra/linea/cli.py`, en la tabla `PLAN`, cambia la línea:

```python
    "RegistrosPerdidos": ["estado_servicios", "retraso_historico", "perdida_ultimo_minuto"],
```

por:

```python
    "RegistrosPerdidos": ["estado_servicios", "retraso_historico", "perdida_ultimo_minuto", "ultimo_registro"],
```

No hace falta reiniciar nada: `lab` lee el código cada vez. Provoca la incidencia y lanza el agente otra vez.

**Resultado esperado:** en `hechos` de `RegistrosPerdidos` aparece `ultimo_registro`, con la pieza y la hora.

**Cómo se lee:** mejorar un agente así es **darle mejores datos**, no un modelo más grande. Cada herramienta nueva es de lectura y está escrita y revisada por una persona.

## Constrúyelo tú: tu propio agente de incidencias

**Qué está pasando:** `lab m07-03` reúne los datos de una alerta, busca su sección en el runbook y pide al modelo un diagnóstico. Ahora lo construyes tú, con una pieza que el comando no tiene: **una comprobación automática del diagnóstico** contra los datos medidos, que en el lab hacías a ojo en el paso 5. Al final provocas el fallo silencioso del archivador y dejas que tu agente lo diagnostique.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** saber si hay algo que diagnosticar antes de construir el agente.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m07_03_mi_agente_incidencias.py`](../../infra/construye/m07_03_mi_agente_incidencias.py). El paso 1 ya está escrito: una función `promql` para preguntar a Prometheus y la lista de alertas **disparadas**, la misma que ves en <http://localhost:9090/alerts>. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_03_mi_agente_incidencias.py
```

**Resultado esperado:**

```text
alertas activas: ninguna
```

**Cómo se lee:** con la línea sana, ninguna. Un agente de incidencias empieza siempre por aquí: sin alerta, no tiene nada que hacer. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Las herramientas de lectura

**Para qué:** darle al agente los datos que necesita para entender una alerta, sin poder cambiar nada.

**Qué ocurre:** escribes tres herramientas que **solo leen** de Prometheus: qué servicios están vivos, cuántos segundos lleva el archivador sin guardar y cuántas carcasas se han perdido en el último minuto. Las pruebas ahora, con la línea sana.

Pega debajo de `# --- PASO 2`:

```python
def estado_servicios():
    return {r["metric"]["job"]: "vivo" if r["value"][1] == "1" else "caído" for r in promql("up")}

def segundos_sin_guardar():
    r = promql("time() - archivador_ultimo_registro_timestamp_seconds")
    return {"segundos_sin_guardar": round(float(r[0]["value"][1])) if r else "sin dato"}

def perdidas_ultimo_minuto():
    r = promql("sum(increase(estacion_piezas_fabricadas_total[1m])) - sum(increase(archivador_registros_guardados_total[1m]))")
    return {"carcasas_perdidas_ultimo_minuto": round(float(r[0]["value"][1])) if r else "sin dato"}

HERRAMIENTAS = {"estado_servicios": estado_servicios, "segundos_sin_guardar": segundos_sin_guardar,
                "perdidas_ultimo_minuto": perdidas_ultimo_minuto}
for nombre, herramienta in HERRAMIENTAS.items():
    print(f"{nombre}: {herramienta()}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas; cambian los números):

```text
estado_servicios: {'archivador': 'vivo', 'sensor': 'vivo'}
segundos_sin_guardar: {'segundos_sin_guardar': 5}
perdidas_ultimo_minuto: {'carcasas_perdidas_ultimo_minuto': 0}
```

**Cómo se lee:** son las preguntas de tu alerta del M01-03, convertidas en herramientas. Con la línea sana, todo vivo, pocos segundos sin guardar y ninguna carcasa perdida. Ninguna de las tres puede reiniciar ni escribir nada.

### 3 — El plan: qué herramientas para cada alerta

**Para qué:** que sea tu código, y no el modelo, quien decida qué datos se miran ante cada alerta.

**Qué ocurre:** escribes el `PLAN`: para cada alerta, la lista de herramientas que hay que usar. Una función reúne los datos de una alerta ejecutando sus herramientas.

Pega debajo de `# --- PASO 3`:

```python
PLAN = {
    "ArchivadorCaido": ["estado_servicios"],
    "HistoricoSinDatos": ["estado_servicios", "segundos_sin_guardar", "perdidas_ultimo_minuto"],
    "RegistrosPerdidos": ["segundos_sin_guardar", "perdidas_ultimo_minuto"],
}

def reunir(alerta):
    hechos = {}
    for herramienta in PLAN.get(alerta, ["estado_servicios"]):
        hechos.update(HERRAMIENTAS[herramienta]())
    return hechos

print("datos que reuniría para HistoricoSinDatos:", reunir("HistoricoSinDatos"))
```

**Resultado esperado** (línea nueva; cambian los números):

```text
datos que reuniría para HistoricoSinDatos: {'archivador': 'vivo', 'sensor': 'vivo', 'segundos_sin_guardar': 5, 'carcasas_perdidas_ultimo_minuto': 0}
```

**Cómo se lee:** para `HistoricoSinDatos`, el agente mira las tres cosas. El plan es una tabla que cualquiera puede leer y revisar: se sabe de antemano qué hará el agente ante cada alerta. Una alerta sin plan usa solo `estado_servicios`.

### 4 — La sección del runbook

**Para qué:** que el agente proponga lo que dice el procedimiento, no lo que se le ocurra.

**Qué ocurre:** lees el runbook, lo partes por sus títulos `## Alerta` y devuelves la sección de la alerta pedida.

Pega debajo de `# --- PASO 4`:

```python
RUNBOOK = open("/opt/linea/docs/runbook-est01.md", encoding="utf-8").read()     # infra/linea/docs/

def procedimiento(alerta):
    for seccion in RUNBOOK.split("\n## ")[1:]:
        titulo, _, cuerpo = seccion.partition("\n")
        if titulo.strip() == alerta:
            return cuerpo.strip()
    return "No hay entrada en el runbook para esta alerta."

print("runbook de HistoricoSinDatos:", procedimiento("HistoricoSinDatos")[:160], "...")
```

**Resultado esperado** (líneas nuevas):

```text
runbook de HistoricoSinDatos: El archivador está vivo pero no guarda registros. Causa habitual: el broker se reinició y el archivador no renovó su suscripción.
Acción: reiniciar el archivado ...
```

**Cómo se lee:** es el texto que escribieron las personas que conocen la línea. El agente no decide qué hacer: **busca qué dice el procedimiento**, igual que el asistente del M05-03 buscaba el párrafo.

### 5 — El diagnóstico y su comprobación

**Para qué:** redactar el diagnóstico con el modelo y no fiarse de él sin comprobarlo.

**Qué ocurre:** das al modelo la alerta, los datos y el runbook, y le pides dos frases. Después sacas las cifras del diagnóstico y compruebas que **cada una está en los datos medidos**; si alguna no está, el diagnóstico se marca para revisar.

Pega debajo de `# --- PASO 5`:

```python
def diagnosticar(alerta, hechos):
    mensajes = [{"role": "system", "content": "Eres el asistente de mantenimiento. Usa solo los datos y el runbook. No inventes cifras."},
                {"role": "user", "content": f"Alerta: {alerta}\nDatos: {json.dumps(hechos, ensure_ascii=False)}\n"
                                            f"Runbook: {procedimiento(alerta)}\n\nEn dos frases: qué pasa y qué propone el runbook."}]
    r = httpx.post("http://llm:8088/v1/chat/completions", json={"messages": mensajes, "max_tokens": 120}, timeout=60)
    return r.json()["choices"][0]["message"]["content"].strip()

def cifras_inventadas(texto, hechos):
    medidas = set(re.findall(r"\d+", json.dumps(hechos)))
    return sorted(set(re.findall(r"\d+", texto)) - medidas)

for alerta in activas:
    hechos = reunir(alerta)
    diagnostico = diagnosticar(alerta, hechos)
    inventadas = cifras_inventadas(diagnostico, hechos)
    informe = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "alerta": alerta, "hechos": hechos,
               "diagnostico": diagnostico, "cifras_sin_respaldo": inventadas,
               "estado": "REVISAR: cifras sin respaldo" if inventadas else "propuesta pendiente de una persona"}
    with open("/data/mis_incidencias.jsonl", "a") as f:
        f.write(json.dumps(informe, ensure_ascii=False) + "\n")
    print(json.dumps(informe, ensure_ascii=False, indent=1))
if not activas:
    print("sin alertas activas: el agente no hace nada")
```

**Resultado esperado** (líneas nuevas):

```text
sin alertas activas: el agente no hace nada
```

**Cómo se lee:** con la línea sana no hay alertas y el agente no llama al modelo. Lo nuevo frente al comando es `cifras_inventadas`: en el paso 5 del lab comparabas el diagnóstico con los hechos a ojo; ahora lo hace el código, y un diagnóstico con cifras que no salen de los datos queda marcado. El paso 6 lo pone a prueba.

### 6 — Decide tú: provocar el fallo silencioso

**Para qué:** ver al agente diagnosticar una incidencia real, y comprobar si su diagnóstico se sostiene.

**Qué ocurre:** reinicias el broker, como en el paso 3 del lab, esperas a que `HistoricoSinDatos` se dispare y ejecutas tu agente. Después recuperas el archivador.

```bash
docker compose restart mosquitto
sleep 40                                  # que la alerta pase de pendiente a disparada
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_03_mi_agente_incidencias.py
docker compose restart archivador         # la acción la hace una persona
```

**Resultado esperado** (cambian los números y el texto del diagnóstico):

```text
alertas activas: ['HistoricoSinDatos', 'RegistrosPerdidos']
...
{
 "ts": "2026-11-06T15:14:29Z",
 "alerta": "HistoricoSinDatos",
 "hechos": {
  "archivador": "vivo",
  "sensor": "vivo",
  "segundos_sin_guardar": 46,
  "carcasas_perdidas_ultimo_minuto": 45
 },
 "diagnostico": "Qué pasa: El archivador está vivo pero no guarda registros. Propone: Reiniciar el archivador y comprobar que vuelve a guardar.",
 "cifras_sin_respaldo": [],
 "estado": "propuesta pendiente de una persona"
}
{
 "ts": "2026-11-06T15:14:31Z",
 "alerta": "RegistrosPerdidos",
 "hechos": {
  "segundos_sin_guardar": 49,
  "carcasas_perdidas_ultimo_minuto": 50
 },
 "diagnostico": "¿Qué pasa? El broker y el archivador están en marcha, y el archivador guarda. El runbook propone que comprobar que el broker y el archivador están en marcha y que el archivador guarda.",
 "cifras_sin_respaldo": [],
 "estado": "propuesta pendiente de una persona"
}
```

**Cómo se lee:** se han disparado dos alertas y el agente ha hecho un informe para cada una, con sus datos: 46 segundos sin guardar y 45 carcasas perdidas en el último minuto. **El primer diagnóstico es correcto** y propone lo que dice el runbook. **El segundo dice que «el archivador guarda»**, justo lo contrario de los datos que tiene delante (49 s sin guardar, 50 carcasas perdidas). Y tu comprobación lo deja pasar, porque no hay ninguna **cifra** [inventada](../glosario/04-ia-generativa.md#alucinacion): el error está en las palabras. Por eso el estado de cada informe es «propuesta pendiente de una persona»: la comprobación automática atrapa una parte de los errores, no todos. En el reto 1 añades una segunda comprobación para este caso.
## Reto

### 1 — Antes de dejarle reiniciar, comprobar lo que dice

**La situación:** sería fácil añadir al agente una herramienta que ejecute `docker compose restart archivador`, y así se arreglaría solo. Pero en el paso 6 de «Constrúyelo tú» uno de los dos diagnósticos decía que el archivador guardaba, cuando los datos decían lo contrario, y la comprobación de cifras no lo vio.

**Qué haces:** después de «Constrúyelo tú», añades al final de tu agente una segunda comprobación, de **coherencia**: lees tus incidencias registradas en `mis_incidencias.jsonl` y marcas las que dicen que el archivador guarda cuando sus propios datos dicen que lleva más de 15 s sin guardar.

**Pistas:** recorre el fichero línea a línea con `json.loads`; `informe["hechos"].get("segundos_sin_guardar")`; `re.search(r"archivador (sí )?guarda", texto)` encuentra la afirmación, y `"no guarda" not in texto` descarta la negación.

**Lo que buscas:** qué informes contradicen sus propios datos, y si dejarías actuar solo a un agente que los escribe.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: una segunda comprobación, de coherencia, sobre las incidencias registradas
def contradice(informe):
    sin_guardar = informe["hechos"].get("segundos_sin_guardar")
    dice_que_guarda = re.search(r"archivador (sí )?guarda", informe["diagnostico"]) and "no guarda" not in informe["diagnostico"]
    return isinstance(sin_guardar, int) and sin_guardar > 15 and bool(dice_que_guarda)

for linea in open("/data/mis_incidencias.jsonl"):
    informe = json.loads(linea)
    print(f"{informe['alerta']:18s} sin_guardar={informe['hechos'].get('segundos_sin_guardar')}  "
          f"{'CONTRADICE los datos: no actuar sin revisar' if contradice(informe) else 'coherente'}")
```

```text
HistoricoSinDatos  sin_guardar=46  coherente
RegistrosPerdidos  sin_guardar=49  CONTRADICE los datos: no actuar sin revisar
```

La comprobación atrapa el informe incoherente. Pero fíjate en lo que ha hecho falta: una regla escrita a mano **para una frase concreta**. Otro día el modelo dirá lo mismo con otras palabras y la regla no lo verá. Por mucho que se añadan comprobaciones, siempre quedará un hueco.

**Por eso la herramienta de reiniciar no se añade.** Un agente que actúa sobre lo que redacta un modelo pequeño acabará reiniciando lo que no debe. La regla es la del M05-04: **solo herramientas de lectura**; el agente reúne, redacta y propone, y una persona revisa y actúa. Si algún día se automatiza una acción, se hace con una regla fija sobre los datos (como la alerta), no sobre el texto del modelo.

</details>

### 2 — Una alerta sin herramientas propias

Baja el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) de `TemperaturaHusilloAlta` a 62,5 °C y su `for` a 0 s, como en el M01-03, y lanza el agente cuando esté activa. ¿Qué herramientas usa y qué propone?

<details>
<summary>Ver solución</summary>

Usa solo `temperatura_actual` (lo dice `PLAN`) y propone avisar al operario y revisar la refrigeración, que es lo que dice su sección del runbook. Si la alerta ya se ha apagado cuando lanzas el agente, sale `FALLO: no hay alertas activas`: con `for: 0s` se enciende y se apaga en pocos segundos. Deja después la regla como estaba (`> 70` y `for: 5s`) y reinicia Prometheus.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: Prometheus no responde` | `prometheus` parado | `docker compose up -d prometheus` |
| `FALLO: no hay alertas activas` justo después de provocar la incidencia | Aún no ha pasado el tiempo de `for` | Espera a ver la alerta en *firing* en <http://localhost:9090/alerts> |
| Error de conexión con `http://llm:8088` | `llm` parado o cargando | `docker compose up -d llm` y espera a que conteste `/salud` (M05-01) |
| El reinicio del broker no provoca la incidencia | El archivador ya está corregido (M01-03) | `git checkout linea/archivador.py` y `docker compose restart archivador` |
| El diagnóstico tarda mucho | El panel u otro contenedor ocupan memoria | `docker compose stop panel` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `alertas activas: ninguna` después de reiniciar el broker | todavía no ha pasado el tiempo de la alerta, o ya corregiste el archivador en «Mejora» | espera 40 s; si corregiste el archivador, para el archivador con `docker compose stop archivador` para provocar `ArchivadorCaido` |

## Conclusiones

### Qué es un agente de incidencias

Es un programa que, ante una alerta, **reúne los datos, consulta el procedimiento y redacta un diagnóstico** para la persona que tiene que actuar. Ahorra el primer trabajo de entender qué pasa, pero no decide.

### Cómo debe repartirse el trabajo

| Tarea | Quién la hace aquí | Por qué |
|-------|--------------------|---------|
| Detectar el problema | Las reglas de Prometheus | Son deterministas y se pueden revisar |
| Elegir qué mirar | El código (`PLAN`) | Un modelo pequeño no elige herramientas de forma fiable |
| Medir | Herramientas de solo lectura | Las cifras tienen que ser medidas, no redactadas |
| Saber qué hacer | El runbook | Lo escribe y lo mantiene la planta |
| Explicarlo en lenguaje claro | El modelo local | Es lo que mejor hace |
| Decidir y actuar | **Una persona** | Es la responsable, y el diagnóstico puede equivocarse |

### Dónde falla y cómo lo has detectado

| Fallo | Cómo lo has visto | Qué provoca |
|-------|-------------------|-------------|
| El modelo convierte una acción en un hecho | «El archivador guarda» frente a `segundos_sin_guardar: 50` | Un diagnóstico que tranquiliza cuando no debería |
| Presenta la causa habitual como comprobada | «El broker se reinició», tomado del runbook | Se puede actuar sobre una causa equivocada |
| Solo ve lo que le dan sus herramientas | Sin `ultimo_registro`, no sabe desde cuándo se pierde | Diagnósticos incompletos |
| Solo sabe lo que dice el runbook | Al cambiar el runbook, cambia la propuesta | Un runbook malo produce propuestas malas |

### Cómo se perfecciona

| Límite | Mejora |
|--------|--------|
| El diagnóstico puede contradecir los datos | Mostrar siempre los hechos junto al texto, y validar con código que las cifras del texto aparecen en los hechos |
| Datos incompletos | Añadir herramientas de lectura según la alerta (lo has hecho) |
| Propuestas que dependen del runbook | Mantener el runbook al día, revisarlo después de cada incidencia |
| Un modelo pequeño redacta mal | Un modelo algo mayor, si el puesto lo permite, y mejor contexto antes que más tamaño |
| Nadie cierra la incidencia | Registrar quién actuó, qué hizo y cuándo |

### En una frase

> 🔑 Un agente de incidencias reúne los datos y propone; la persona comprueba y decide. Las cifras se miran en los hechos, nunca en el texto del modelo.
