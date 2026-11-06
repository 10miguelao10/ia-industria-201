# M06-03 — Predicción y actuación supervisada

[← Página anterior](M06-02-integracion-ot.md) · [Siguiente página →](../M07-mlops-observabilidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **predecir una [anomalía](../glosario/03-aprendizaje-automatico.md#anomalia) a partir del [comportamiento normal](../glosario/03-aprendizaje-automatico.md#banda-normal) y actuar antes de que ocurra**: cómo se aprende lo normal de las [métricas](../glosario/02-observabilidad.md#metrica) de la propia estación, cómo debe ser un sistema que propone o aplica una acción, cómo se detecta que el modelo ha aprendido mal, y cómo se pone un límite a lo que puede hacer.

### Prerrequisitos

- `mosquitto`, `sensor`, `archivador` y `prometheus` en marcha, con **al menos 10 minutos** de métricas **sin ningún fallo provocado** (si acabas de hacer la demo del README, espera 10 minutos o reinicia la estación con `docker compose restart sensor` y espera).
- Refrigeración en su nivel normal: `docker compose --profile lab run --rm --no-deps lab consigna 1`.
- Dos terminales en `infra/`.

### Qué está pasando

La refrigeración del husillo puede fallar. Cuando pasa, la temperatura no salta de golpe: **sube poco a poco**, unos 3 °C por minuto. La [alerta](../glosario/02-observabilidad.md#alerta) del M01-03 solo avisa al pasar de 70 °C, y para entonces se han fabricado minutos de carcasas con el husillo demasiado caliente.

Un sistema que **conoce cómo se comporta la estación cuando va bien** puede ver antes que algo se sale de lo normal, y calcular hacia dónde va:

| | Alerta fija (M01-03) | Vigilancia predictiva (este lab) |
|--|----------------------|----------------------------------|
| Qué mira | Si la temperatura pasa de 70 °C | Si se sale de lo normal **y** hacia dónde va |
| Cuándo avisa | Cuando ya ha pasado | Minutos antes |
| Qué aprende | Nada: el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) lo escribe una persona | El rango y la variación normales, de las métricas |

Y puede proponer una acción: **subir la refrigeración**. La estación acepta una **[consigna](../glosario/05-operacion-gobierno.md#consigna)** de refrigeración por [MQTT](../glosario/01-datos-arquitectura.md#mqtt) ([tema](../glosario/01-datos-arquitectura.md#tema) `linea/est01/consigna`), pero **solo entre los niveles 1 y 3**: el límite lo pone la propia máquina, no el modelo.

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Fallo de refrigeración, desgaste de herramienta | `lab evento fallo-refrigeracion` (simulado) |
| Historian o [Prometheus](../glosario/02-observabilidad.md#prometheus) con meses de datos | 10 minutos de métricas exportadas de Prometheus |
| Modelo de comportamiento normal y de tendencia | `lab m06-03 aprender` y `lab m06-03 vigilar` |
| Consigna del PLC con límites | Refrigeración 1–3, recortada por la estación |
| Operario que confirma la acción | Tú, con `lab consigna 3` |

### 1 — Ver lo normal en crudo

**Qué ocurre:** antes de enseñar nada a un modelo, miras cómo es la temperatura normal de la estación. En <http://localhost:9090/graph>, pestaña **Graph**, rango de 15 minutos:

```promql
estacion_temperatura_husillo_celsius
```

**Qué ves:** un diente de sierra entre unos 61 y 63 °C que se repite. Eso es lo normal: la temperatura sube durante unas carcasas y baja. Si hay algún hueco, es un reinicio de la estación.

### 2 — Exportar las métricas

**Qué ocurre:** bajas de Prometheus los últimos 10 minutos de temperatura y [tiempo de ciclo](../glosario/01-datos-arquitectura.md#tiempo-ciclo) a un fichero, para usarlos como datos de entrenamiento. Es un comando de ayuda que usa la [API](../glosario/05-operacion-gobierno.md#api) de Prometheus (`query_range`).

```bash
# Últimos 10 minutos, una muestra cada 5 s, a data/metricas.csv
docker compose --profile lab run --rm --no-deps lab exportar 10
```

📋 Ficha del comando [`exportar`](../comandos-lab.md#exportar).

**Resultado esperado:**

```text
muestras=121 desde=2026-11-06T02:34:02+00:00 hasta=2026-11-06T02:44:02+00:00 (una cada 5 s)
temperatura: media=62.04 mínima=60.86 máxima=63.25
OK exportar: 121 muestras en metricas.csv
```

Abre `infra/data/metricas.csv` en VS Code: una fila cada 5 segundos, con la hora, la temperatura y el tiempo de ciclo.

**Cómo se lee:** 121 muestras, entre 60,86 y 63,25 °C. Si la mínima saliera a **0,00**, habría un reinicio en medio: lo verás en el paso 3.

### 3 — Aprender el comportamiento normal

**Qué ocurre:** el modelo aprende dos cosas de esas muestras: **hasta dónde llega** la temperatura normal y **cuánto sube como mucho** en dos minutos. Antes, descarta las muestras imposibles (por debajo de 40 °C, que son huecos de reinicios).

```bash
docker compose --profile lab run --rm --no-deps lab m06-03 aprender
```

📋 Ficha del comando [`m06-03`](../comandos-lab.md#m06-03).

**Resultado esperado:**

```text
muestras=121 descartadas_por_imposibles=0
{"muestras": 121, "temperatura_media": 62.04, "limite_normal": 63.24, "pendiente_normal_max": 0.0062}
OK m06-03: comportamiento normal aprendido de 121 muestras -> modelo_termico.json
```

**Cómo se lee:**

| Campo | Valor | Qué significa |
|-------|-------|---------------|
| `limite_normal` | 63,24 °C | El 99,5 % de las muestras normales están por debajo |
| `pendiente_normal_max` | 0,0062 °C/s | Lo más que sube la temperatura en dos minutos normales: **0,37 °C por minuto** |

Es un modelo muy sencillo, y es suficiente: lo importante no es su complejidad, sino que **ha aprendido de datos normales de verdad**.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m06_03</code>)</summary>

```python
df = df[df.temperatura_c >= 40]                      # limpieza: fuera huecos de reinicios
temp = df.temperatura_c.to_numpy()
ventana = 24                                         # 24 muestras de 5 s = 2 minutos
# pendiente de una recta ajustada a cada ventana de 2 minutos (regresión lineal)
subidas = [np.polyfit(np.arange(ventana) * 5, temp[i:i + ventana], 1)[0] for i in range(len(temp) - ventana)]
modelo = {
    "limite_normal": np.percentile(temp, 99.5),               # hasta dónde llega lo normal
    "pendiente_normal_max": np.percentile(np.abs(subidas), 99.5),  # cuánto sube como mucho
}
```

</details>

### 4 — Provocar el fallo y vigilar, en modo asistido

**Qué ocurre:** provocas el fallo de refrigeración y pones al modelo a vigilar durante dos minutos y medio. Cada 10 segundos mira la temperatura y su tendencia de los últimos 2 minutos. Si se sale de lo normal y sube, **calcula cuándo llegará a 70 °C**. Si es en menos de 5 minutos, **propone** una acción, pero no la aplica.

```bash
docker compose --profile lab run --rm --no-deps lab evento fallo-refrigeracion
docker compose --profile lab run --rm --no-deps lab m06-03 vigilar segundos=150
```

📋 Fichas de los comandos [`evento`](../comandos-lab.md#evento) y [`m06-03`](../comandos-lab.md#m06-03).

**Resultado esperado** (cambian las horas y los valores):

```text
vigilando 150 s en modo ASISTIDO (propone, no actúa)
normal: hasta 63.24 °C, subida máxima 0.37 °C/min
hora      temp   subida/min  previsión
02:44:10  62.06      +0.07  normal
02:44:20  63.56      +0.10  por encima de lo normal, sin subida
02:44:30  62.53      +0.10  normal
02:44:40  64.04      +0.42  fuera de lo normal: llegará a 70 °C en ~14.1 min
02:44:50  63.30      +0.44  fuera de lo normal: llegará a 70 °C en ~15.3 min
02:45:00  64.94      +1.03  fuera de lo normal: llegará a 70 °C en ~4.9 min  -> PROPUESTA: subir refrigeración a 3
02:45:10  63.96      +1.22  fuera de lo normal: llegará a 70 °C en ~4.9 min
02:45:20  65.43      +1.61  fuera de lo normal: llegará a 70 °C en ~2.8 min
...
02:46:30  68.45      +2.86  fuera de lo normal: llegará a 70 °C en ~0.5 min
OK m06-03: vigilancia terminada; acción registrada en actuaciones.jsonl
```

**Cómo se lee:**

| Momento | Temperatura | Qué pasa |
|---------|-------------|----------|
| 02:44:20 | 63,56 °C | Por encima de lo normal, pero sin subida: un pico del diente de sierra. No avisa |
| 02:44:40 | 64,04 °C | Por encima **y** subiendo más de lo normal: primera previsión, a 14 minutos |
| 02:45:00 | 64,94 °C | La previsión baja de 5 minutos: **propone subir la refrigeración** |
| 02:46:30 | 68,45 °C | Nadie ha actuado: la temperatura sigue subiendo |

La propuesta llegó con la temperatura a **64,9 °C**, unos **5 minutos antes** de la alerta fija de 70 °C (según el puesto y el momento, entre 3 y 5 minutos). La previsión mejora con cada lectura, porque la tendencia de 2 minutos se va llenando de datos del fallo.

### 5 — Actuar, como operario

**Qué ocurre:** decides aplicar la propuesta y subes tú la refrigeración. La estación recibe la consigna y la temperatura baja.

En la **terminal 2**, deja la estación a la vista:

```bash
docker compose logs -f --tail=0 sensor
```

En la **terminal 1**:

```bash
docker compose --profile lab run --rm --no-deps lab consigna 3
```

📋 Ficha del comando [`consigna`](../comandos-lab.md#consigna).

**Resultado esperado** en la terminal 2:

```text
sensor-1  | sensor: consigna refrigeración pedida=3 aplicada=3
sensor-1  | sensor: P0906 64.93 C
sensor-1  | sensor: P0907 65.22 C
...
```

En un minuto, la temperatura baja de unos 68 °C a unos 65 °C, y sigue bajando. En <http://localhost:9090/alerts>, `TemperaturaHusilloAlta` **no llega a activarse**.

Cuando acabes, termina el fallo y vuelve al nivel normal cuando la temperatura baje de 63 °C:

```bash
docker compose --profile lab run --rm --no-deps lab evento fin
# … cuando baje de 63 °C:
docker compose --profile lab run --rm --no-deps lab consigna 1
```

## Comprueba tu entendimiento

**Por encima, pero normal**

A las 02:44:20 la temperatura estaba en 63,56 °C, por encima del límite normal. ¿Por qué no avisó?

→ Porque no subía más de lo normal. Un pico del diente de sierra pasa del límite y baja enseguida. El modelo pide las dos cosas: estar fuera **y** tender a más.

## Investiga: qué quedó registrado

**Qué ocurre:** cada propuesta o acción queda en `infra/data/actuaciones.jsonl`. Ábrelo en VS Code.

**Resultado esperado:**

```json
{"ts": "02:45:00", "temperatura_c": 64.94, "subida_c_min": 1.03, "minutos_hasta_alerta": 4.9, "accion": "subir refrigeración a 3", "estado": "propuesta: la decide el operario (lab consigna 3)"}
```

Y en Prometheus, la temperatura junto al nivel de refrigeración (dos consultas en el mismo **Graph**, con **Add Panel**):

```promql
estacion_temperatura_husillo_celsius
```

```promql
estacion_refrigeracion_nivel
```

**Cómo se lee:** se ve la subida, el momento en que el nivel pasa de 1 a 3 y la bajada. El registro dice **qué se propuso, con qué datos y en qué estado quedó**: sin él, nadie podría revisar mañana si el sistema acertó.

## Experimenta: el modo automático

**Qué ocurre:** repites el fallo, pero ahora el modelo **aplica** la acción él mismo, en vez de proponerla. Antes, vuelve al punto de partida: fallo terminado, refrigeración en 1 y temperatura normal (por debajo de 63 °C).

```bash
docker compose --profile lab run --rm --no-deps lab evento fallo-refrigeracion
docker compose --profile lab run --rm --no-deps lab m06-03 vigilar segundos=180 modo=automatico
```

**Resultado esperado:**

```text
vigilando 180 s en modo AUTOMÁTICO (con límites)
normal: hasta 63.24 °C, subida máxima 0.37 °C/min
hora      temp   subida/min  previsión
02:49:24  62.66      +0.46  normal
02:49:34  64.14      +2.25  fuera de lo normal: llegará a 70 °C en ~2.6 min  -> ACCIÓN: refrigeración a 3 (aplicada)
02:49:45  63.91      +5.11  fuera de lo normal: llegará a 70 °C en ~1.2 min
02:49:55  61.89      +6.80  normal
02:50:05  62.87      +0.50  normal
...
OK m06-03: vigilancia terminada; acción registrada en actuaciones.jsonl
```

**Cómo se lee:** con 64,1 °C el modelo aplica la refrigeración, y en 20 segundos la temperatura vuelve a lo normal. La columna de subida tarda un poco en bajar porque se calcula sobre los últimos 2 minutos. El problema se ha resuelto **sin que nadie haga nada**.

**Pregunta:** ¿lo dejarías así en tu línea? Piensa qué pasaría si el modelo hubiera aprendido mal (el reto 2), si la consigna fuera la velocidad del husillo en lugar de la refrigeración, o si el sistema siguiera subiendo la refrigeración cuando el fallo ya no existe.

Al terminar: `lab evento fin` y, cuando baje de 63 °C, `lab consigna 1`.

## Reto

### 1 — Pedir más de lo permitido

Pide una refrigeración de nivel 7 y mira qué aplica la estación.

```bash
docker compose --profile lab run --rm --no-deps lab consigna 7
curl -s http://localhost:9102/metrics | grep refrigeracion_nivel
```

<details>
<summary>Ver solución</summary>

```text
estacion_refrigeracion_nivel 3.0
```

La estación ha aplicado **3**, su máximo. El límite está en la máquina: aunque el modelo (o una persona, o un mensaje falso en el [broker](../glosario/01-datos-arquitectura.md#broker)) pida algo fuera de rango, la estación no lo hace. Es el diseño correcto: los límites de seguridad viven en el control, no en quien da la orden. Vuelve a `lab consigna 1`.

</details>

### 2 — Aprender con el fallo dentro

Exporta media hora de métricas que **incluya** alguno de los fallos que has provocado, y vuelve a aprender:

```bash
docker compose --profile lab run --rm --no-deps lab exportar 30
docker compose --profile lab run --rm --no-deps lab m06-03 aprender
```

¿Qué ha aprendido? ¿Detectaría ahora el fallo?

<details>
<summary>Ver solución</summary>

```text
{"muestras": 360, "temperatura_media": 64.16, "limite_normal": 72.92, "pendiente_normal_max": 0.1182}
```

Ha aprendido que lo «normal» llega hasta **72,9 °C** y que subir **7 °C por minuto** es normal. Con ese modelo, el fallo de refrigeración ya no se sale de lo normal: **no lo detectaría nunca**. Lo normal tiene que ser normal de verdad: hay que limpiar los datos de entrenamiento de las incidencias conocidas, igual que en el M02-03. Vuelve a exportar 10 minutos sin fallos y a aprender antes de seguir.

</details>

## Mejora: la previsión, también en Prometheus

**Qué ocurre:** Prometheus puede hacer él mismo una previsión sencilla con `predict_linear`: ajusta una recta a los últimos minutos de una serie y calcula dónde estará dentro de un tiempo. Vas a añadir una alerta predictiva junto a la fija.

Abre `infra/prometheus/alertas.yml` en VS Code y añade al final, con la misma sangría que las demás reglas:

```yaml
      # Previsión: si la tendencia de los últimos 2 minutos sigue, en 5 minutos pasará de 70 °C
      - alert: PrevisionTemperaturaAlta
        expr: predict_linear(estacion_temperatura_husillo_celsius[2m], 300) > 70
        for: 10s
        labels: {severidad: aviso}
        annotations:
          resumen: "Si sigue así, el husillo pasará de 70 °C en menos de 5 minutos"
```

Reinicia Prometheus y provoca el fallo otra vez (desde una temperatura normal):

```bash
docker compose restart prometheus
docker compose --profile lab run --rm --no-deps lab evento fallo-refrigeracion
```

Recarga <http://localhost:9090/alerts> cada 10 segundos.

**Resultado esperado** (así evolucionó en una prueba; temperatura y alertas cada 10 s):

```text
03:57:21 temp=65.24 []
03:57:31 temp=64.45 ['PrevisionTemperaturaAlta:pending']
03:57:41 temp=65.93 ['PrevisionTemperaturaAlta:firing']
...
03:59:12 temp=70    ['TemperaturaHusilloAlta:pending', 'PrevisionTemperaturaAlta:firing']
```

**Cómo se lee:** la alerta predictiva se activa con **65,9 °C**, minuto y medio antes de llegar a 70 °C. Fíjate también en que la alerta fija se queda en *pending* y no llega a *firing*: el diente de sierra hace que la temperatura baje de 70 antes de cumplir sus 5 segundos de `for`, lo que viste en el M01-03. Una alerta predictiva bien hecha es más robusta que una fija mal ajustada.

Termina el fallo (`lab evento fin`, y `lab consigna 1` cuando se normalice).

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: solo … muestras válidas` | Prometheus lleva poco tiempo recogiendo | Espera 10 minutos con la estación en marcha |
| `limite_normal` muy alto (más de 64 °C) | Has exportado un periodo con un fallo dentro | Espera 10 minutos sin fallos y repite el paso 2 |
| El modelo no propone nada | La temperatura no se sale de lo normal: ¿enviaste el evento? | `lab evento fallo-refrigeracion` y espera un minuto |
| La temperatura no baja tras la consigna | El fallo sigue y la refrigeración es 1 | `lab consigna 3` |
| La temperatura sigue alta tras `evento fin` | Se recupera despacio con refrigeración 1 | `lab consigna 3` y luego `lab consigna 1` |

## Conclusiones

### Qué es predecir y actuar

Aprender cómo se comporta la estación cuando va bien, vigilar si se sale de ahí y hacia dónde va, y **adelantarse** a la alarma con una acción: propuesta a una persona o aplicada dentro de unos límites.

### Cómo debe ser

| Requisito | En el lab |
|-----------|-----------|
| Aprender de datos normales y limpios | 10 minutos sin fallos, sin muestras imposibles |
| Avisar por salirse de lo normal **y** tender a más | Los picos del diente de sierra no avisan |
| Dar tiempo para actuar | Propuesta con 3 a 5 minutos de margen |
| Dejar registro de cada propuesta o acción | `actuaciones.jsonl` |
| Los límites, en la máquina | La consigna 7 se aplica como 3 |

### Dónde se rompe y cómo lo has detectado

| Fallo | Cómo lo has visto | Qué provoca |
|-------|-------------------|-------------|
| Aprender con el fallo dentro | Reto 2: «normal» hasta 72,9 °C | El fallo deja de detectarse |
| Muestras imposibles en el entrenamiento | Huecos a 0 °C en la exportación | Lo normal se aprende mal |
| Una alerta fija que oscila | La de 70 °C se queda en *pending* | Avisa tarde o no avisa |
| Actuar sin límites | (evitado) La estación recorta la consigna | — |

### Cómo se perfecciona

| Límite | Mejora |
|--------|--------|
| Previsión hecha fuera de la monitorización | `predict_linear` en Prometheus (lo has hecho) |
| Un modelo de una sola señal | Modelos multivariables que miren temperatura, corriente y tiempo de ciclo juntos (M03-02) |
| Actuar sin saber cuándo parar | Volver al nivel nominal cuando la temperatura se normaliza, con confirmación |
| Automático en planta | Solo en acciones reversibles y acotadas, con validación de seguridad y registro; lo habitual es el modo asistido |

### En una frase

> 🔑 Un modelo que conoce lo normal puede avisar minutos antes que una alarma fija; dejarle actuar es otra decisión, y solo es aceptable si lo que puede hacer está limitado por la propia máquina.
