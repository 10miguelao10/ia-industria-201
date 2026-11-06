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

## Reto

### 1 — ¿Y si el agente reiniciara él solo?

Sería fácil añadir una herramienta que ejecute `docker compose restart archivador`. ¿La añadirías?

<details>
<summary>Ver solución</summary>

No en este punto. Ya has visto que el diagnóstico puede contradecir los datos: un agente que actúa sobre lo que redacta un modelo así puede reiniciar lo que no debe. La regla es la del M05-04: **solo herramientas de lectura**. Si algún día se automatiza una acción, que sea concreta, reversible, con confirmación de una persona y registrada.

</details>

### 2 — Una alerta sin herramientas propias

Baja el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) de `TemperaturaHusilloAlta` a 62,5 °C y su `for` a 0 s, como en el M01-03, y lanza el agente cuando esté activa. ¿Qué herramientas usa y qué propone?

<details>
<summary>Ver solución</summary>

Usa solo `temperatura_actual` (lo dice `PLAN`) y propone avisar al operario y revisar la refrigeración, que es lo que dice su sección del runbook. Si la alerta ya se ha apagado cuando lanzas el agente, sale `FALLO: no hay alertas activas`: con `for: 0s` se enciende y se apaga en pocos segundos. Deja después la regla como estaba (`> 70` y `for: 5s`) y reinicia Prometheus.

</details>

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

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: Prometheus no responde` | `prometheus` parado | `docker compose up -d prometheus` |
| `FALLO: no hay alertas activas` justo después de provocar la incidencia | Aún no ha pasado el tiempo de `for` | Espera a ver la alerta en *firing* en <http://localhost:9090/alerts> |
| Error de conexión con `http://llm:8088` | `llm` parado o cargando | `docker compose up -d llm` y espera a que conteste `/salud` (M05-01) |
| El reinicio del broker no provoca la incidencia | El archivador ya está corregido (M01-03) | `git checkout linea/archivador.py` y `docker compose restart archivador` |
| El diagnóstico tarda mucho | El panel u otro contenedor ocupan memoria | `docker compose stop panel` |

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
