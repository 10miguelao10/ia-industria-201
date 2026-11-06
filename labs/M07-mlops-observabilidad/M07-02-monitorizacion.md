# M07-02 — Monitorización y seguimiento operacional

[← Página anterior](M07-01-servicio-inferencia.md) · [Siguiente página →](M07-03-incidencias-agente.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **monitorización de un modelo en operación**: por qué un modelo se degrada sin avisar, cómo debe vigilarse, cómo se detecta la [deriva](../glosario/05-operacion-gobierno.md#deriva) y qué se hace cuando aparece.

### Prerrequisitos

- El mismo `data/modelo_defecto.joblib`.

### Qué está pasando

Pasan las semanas. Se cambia el refrigerante, llega el verano o se cambia de utillaje, y el husillo pasa a trabajar **8 °C más caliente** que cuando se entrenó el modelo.

El modelo no se rompe: sigue contestando como si nada. Pero la línea ya no se parece a la que aprendió, y sus dictámenes dejan de tener sentido. Esto se llama **deriva**, y la única forma de verla es **vigilar** cómo se comporta el modelo en operación.

En este lab se mide la tasa de piezas que manda a revisión con los datos normales (la base) y con los mismos datos 8 °C más calientes. Sin la base, el segundo número no dice nada.

### 1 — Medir la base y el desplazamiento

Vas a puntuar las piezas de evaluación tal cual (la base) y otra vez con 8 °C más. Sin una línea base, el número de después no dice nada.

```bash
docker compose --profile lab run --rm --no-deps lab m07-02
```

📋 Ficha del comando [`m07-02`](../comandos-lab.md#m07-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
tasa_base=0.08 tasa_desplazada=0.96
OK m07-02: base=0.08 desplazada=0.96
```

Con el proceso normal, el 8 % de las piezas va a revisión. Con el proceso desplazado, el 96 %: el modelo sigue contestando, pero ya no describe esta línea.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
_, test = _partir(df)                                   # las piezas de evaluación de M03
base = _tasa_alerta(modelo, test)                       # % con probabilidad ≥ 0,5

movido = test.copy()
movido["temperatura_c"] = movido["temperatura_c"] + 8   # el proceso «se ha ido»
deriva = _tasa_alerta(modelo, movido)
```

</details>

### 2 — Guardar el seguimiento

Vas a leer el resumen que queda escrito para compararlo con la medida de mañana.

```bash
cat data/seguimiento.json
```

**Resultado esperado:**

```json
{"tasa_base": 0.08225108225108226, "tasa_desplazada": 0.9567099567099567}
```

## Comprueba tu entendimiento

**Dos fallos distintos**

Si `api` se cae a mitad de un lote, ¿hay que reentrenar?

→ No. Eso es una caída del servicio. La deriva es el servicio funcionando con datos que ya no se parecen a los del entrenamiento.

## Experimenta: ¿cuánta deriva hace falta?

**Qué ocurre:** 8 °C es mucho. Pruebas con desplazamientos más pequeños.

```bash
docker compose --profile lab run --rm --no-deps lab m07-02 grados=2
docker compose --profile lab run --rm --no-deps lab m07-02 grados=4
```

**Resultado esperado:**

```text
tasa_base=0.08 tasa_desplazada=0.28 (+2 °C)
```

```text
tasa_base=0.08 tasa_desplazada=0.56 (+4 °C)
```

| Desplazamiento | Piezas a revisión |
|----------------|-------------------|
| 0 °C (base) | 8 % |
| +2 °C | 28 % |
| +4 °C | 56 % |
| +8 °C | 96 % |

**Cómo se lee:** con solo **2 °C** más, el modelo manda a revisión **tres veces más piezas**. Un cambio así (un verano, otro refrigerante) puede pasar desapercibido en el panel, y en una semana el puesto de revisión estaría desbordado sin que nadie supiera por qué. La tasa de piezas a revisión es la señal: hay que vigilarla cada día.

## Investiga: la deriva en la línea en vivo

**Qué ocurre:** hasta ahora la deriva era simulada (sumando grados al examen). Ahora mides la tasa con **las últimas 120 carcasas reales** de la línea, con la opción `vivo`.

```bash
docker compose --profile lab run --rm --no-deps lab m07-02 vivo
```

**Resultado esperado** (con la línea normal):

```text
tasa_base=0.08 tasa_linea_ahora=0.15 (últimas 120 carcasas, temperatura media 63.13 °C)
```

Ahora provoca un fallo de refrigeración (el del M06-03), espera un minuto y medio y repite:

```bash
docker compose --profile lab run --rm --no-deps lab evento fallo-refrigeracion
# … espera unos 100 segundos …
docker compose --profile lab run --rm --no-deps lab m07-02 vivo
```

**Resultado esperado:**

```text
tasa_base=0.08 tasa_linea_ahora=0.28 (últimas 120 carcasas, temperatura media 64.26 °C)
```

**Cómo se lee:** la línea real ya no es la del entrenamiento: con el fallo, la tasa sube al 28 %. Un sistema de [MLOps](../glosario/05-operacion-gobierno.md#mlops) calcularía esta tasa cada pocos minutos y avisaría si se aleja de la base, igual que una [alerta](../glosario/02-observabilidad.md#alerta) de [Prometheus](../glosario/02-observabilidad.md#prometheus). Termina el fallo antes de seguir:

```bash
docker compose --profile lab run --rm --no-deps lab evento fin
docker compose --profile lab run --rm --no-deps lab consigna 3
# … cuando baje de 63 °C:
docker compose --profile lab run --rm --no-deps lab consigna 1
```

## Constrúyelo tú: tu propio vigilante de deriva

**Qué está pasando:** `lab m07-02` compara la tasa de piezas que el modelo manda a revisar con la de una base. Ahora construyes tú el vigilante con **dos** comprobaciones distintas: la del comportamiento del modelo (cuánto manda a revisar) y la de sus datos de entrada (si se parecen a los del entrenamiento). Al final descubres una deriva que la primera no ve y la segunda sí.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** tener las dos referencias con las que se compara la línea: los datos de entrenamiento y una base sana.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m07_02_mi_vigilante_deriva.py`](../../infra/construye/m07_02_mi_vigilante_deriva.py). Arriba están las **decisiones** (`GRADOS`, `TOLERANCIA`, `DESVIACIONES`); debajo, el paso 1 ya escrito: carga el modelo del M03-03 y separa sus datos en entrenamiento y examen, como siempre. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m07_02_mi_vigilante_deriva.py
```

**Resultado esperado:**

```text
entrenamiento=537 piezas  base de comparación=231 piezas
```

**Cómo se lee:** el examen hace de **base**: es cómo se comportaba la línea cuando el modelo se puso en marcha. Sin una base guardada, cualquier número que midas después no se puede comparar con nada. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — La tasa de «revisar» de la base

**Para qué:** saber cuánto manda a revisar el modelo cuando todo va bien.

**Qué ocurre:** pides al modelo la decisión para cada pieza de la base y calculas qué fracción manda a revisar.

Pega debajo de `# --- PASO 2`:

```python
def tasa_revisar(datos):
    return float((modelo.predict_proba(datos[SENALES])[:, 1] >= 0.5).mean())

tasa_base = tasa_revisar(base)
print(f"tasa de revisar en la base: {tasa_base:.2f}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
tasa de revisar en la base: 0.08
```

**Cómo se lee:** es el 0,08 de `lab m07-02`: con la línea sana, el modelo manda a revisar unas 8 de cada 100 piezas. Es el comportamiento normal del modelo; lo que se vigila es si cambia.

### 3 — Simular que la línea se calienta

**Para qué:** ver cómo cambia el comportamiento del modelo cuando cambian los datos, sin que el modelo cambie.

**Qué ocurre:** copias la base, le sumas `GRADOS` a la temperatura de todas las piezas, como si se hubiera cambiado el refrigerante, y vuelves a calcular la tasa. Si se aleja de la base más que la `TOLERANCIA`, avisas.

Pega debajo de `# --- PASO 3`:

```python
movida = base.copy()
movida["temperatura_c"] += GRADOS
tasa = tasa_revisar(movida)
alerta = abs(tasa - tasa_base) > TOLERANCIA
print(f"con +{GRADOS} °C: tasa de revisar={tasa:.2f}  ->  {'DERIVA: el modelo se comporta distinto' if alerta else 'normal'}")
```

**Resultado esperado** (líneas nuevas):

```text
con +8.0 °C: tasa de revisar=0.96  ->  DERIVA: el modelo se comporta distinto
```

**Cómo se lee:** el modelo pasa de mandar a revisar 8 de cada 100 piezas a **96 de cada 100**. No ha fallado nada: el modelo es el mismo y sigue contestando sin error. Lo que ha cambiado es la línea, que ya no se parece a la que aprendió. Es la deriva.

### 4 — Vigilar también los datos de entrada

**Para qué:** detectar el cambio en la línea directamente, sin esperar a que se note en las decisiones.

**Qué ocurre:** para cada señal, comparas la media de los datos nuevos con la del entrenamiento y cuentas a cuántas desviaciones de la media de entrenamiento está. Si pasa de `DESVIACIONES`, avisas.

Pega debajo de `# --- PASO 4`:

```python
def deriva_datos(nuevos):
    avisos = []
    for s in SENALES:
        media, desv = entrenamiento[s].mean(), entrenamiento[s].std()
        error_media = desv / len(nuevos) ** 0.5                # cuánto varía una media de tantas piezas
        z = (nuevos[s].mean() - media) / error_media
        if abs(z) > DESVIACIONES:
            avisos.append(f"{s} ({z:+.0f})")
    return avisos

print("señales que han cambiado:", deriva_datos(movida) or "ninguna")
```

**Resultado esperado** (líneas nuevas):

```text
señales que han cambiado: ['temperatura_c (+51)']
```

**Cómo se lee:** avisa de la temperatura, con +51: la media de 231 piezas se ha movido 51 veces lo que suele variar una media de tantas piezas. Esta comprobación no usa el modelo para nada: mira solo los datos. Por eso puede ver cambios que el modelo todavía no ha notado (paso 6 y reto 1).

### 5 — Las dos comprobaciones sobre la línea de ahora

**Para qué:** aplicar el vigilante a la producción real, no a una simulación.

**Qué ocurre:** lees las últimas 120 carcasas del [histórico](../glosario/01-datos-arquitectura.md#historico) (la presión no viaja en vivo, así que se pone la nominal) y les pasas las dos comprobaciones.

Pega debajo de `# --- PASO 5`:

```python
with sqlite3.connect("file:/data/historial.sqlite?mode=ro", uri=True) as con:
    ahora = pd.read_sql_query("SELECT temperatura_c, vibracion_mm_s, corriente_a FROM lecturas ORDER BY id DESC LIMIT 120", con)
ahora["presion_bar"] = 6.0
print(f"línea de ahora: tasa de revisar={tasa_revisar(ahora):.2f} (base {tasa_base:.2f})")
print("señales de la línea de ahora que han cambiado:", deriva_datos(ahora) or "ninguna")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
línea de ahora: tasa de revisar=0.08 (base 0.08)
señales de la línea de ahora que han cambiado: ['temperatura_c (+7)', 'corriente_a (-4)']
```

**Cómo se lee:** la tasa de la línea es **la de la base**: por las decisiones, todo en orden. Pero la comprobación de datos **avisa de la temperatura y la corriente**: la estación simulada y el `limpio.csv` del M02-03 no son la misma máquina. La temperatura media de la línea es algo más alta y la corriente algo más baja que en los datos de entrenamiento: diferencias pequeñas, pero sostenidas en 120 carcasas. El modelo del M03-03 se entrenó con datos que no son los de esta línea, que es justo por lo que el M03-04 entrena con los de la propia línea. Si acabas de provocar el fallo del M06-03, espera unos minutos: la línea todavía está caliente.

### 6 — Decide tú: una deriva pequeña

**Para qué:** comparar qué comprobación avisa antes.

**Qué ocurre:** cambias `GRADOS = 8.0` por `GRADOS = 1.0` y ejecutas.

**Resultado esperado** (líneas que cambian):

```text
con +1.0 °C: tasa de revisar=0.17  ->  normal
señales que han cambiado: ['temperatura_c (+5)']
```

**Cómo se lee:** con un grado más, la tasa sube de 0,08 a 0,17, por debajo de la tolerancia de 0,10, y **la alarma del modelo no salta**; **la comprobación de datos sí avisa** de la temperatura. Un grado no basta para disparar las decisiones, pero es un cambio real y sostenido. Vigilar los datos de entrada avisa antes que vigilar las decisiones: da tiempo a revisar el modelo antes de que empiece a equivocarse. Vuelve a dejar `GRADOS = 8.0`.
## Reto

### 1 — Una deriva que el modelo no ve

**La situación:** cambia el lote de material y el motor de la estación trabaja con más esfuerzo: la corriente sube 0,3 A en todas las carcasas. La temperatura no cambia.

**Qué haces:** en tu vigilante de «Constrúyelo tú», añades al final un bloque que copia la base, le suma 0,3 A a la corriente y le pasa las dos comprobaciones: la tasa de «revisar» y la de los datos de entrada.

**Pistas:** igual que el paso 3, pero con `otra["corriente_a"] += 0.3`; después, `tasa_revisar(otra)` y `deriva_datos(otra)`.

**Lo que buscas:** cuál de las dos comprobaciones se entera del cambio.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: una deriva en otra señal
otra = base.copy()
otra["corriente_a"] += 0.3                              # el motor trabaja con más esfuerzo
tasa_otra = tasa_revisar(otra)
print(f"corriente +0,3 A: tasa de revisar={tasa_otra:.2f} (base {tasa_base:.2f})  "
      f"-> {'DERIVA en el modelo' if abs(tasa_otra - tasa_base) > TOLERANCIA else 'el modelo no se entera'}")
print("señales que han cambiado:", deriva_datos(otra) or "ninguna")
```

```text
corriente +0,3 A: tasa de revisar=0.08 (base 0.08)  -> el modelo no se entera
señales que han cambiado: ['corriente_a (+30)']
```

**La tasa no se mueve nada**: el modelo del M03-03 apenas usa la corriente, así que sus decisiones no cambian. Pero la corriente ha cambiado muchísimo (+30), y en la línea real del M03-04 la corriente es **justo una de las causas del defecto**. Vigilando solo las decisiones, nadie se enteraría hasta que calidad empezara a encontrar carcasas malas que el modelo deja pasar.

**La regla:** un modelo en producción se vigila por dos lados: cómo decide (la tasa) y qué le entra (los datos). La segunda vigilancia avisa también de cambios en señales que el modelo no usa, y que pueden importar igual.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no se ve la deriva al subir 8 °C` | el CSV no es el limpio de este curso | repite `m02-03` y `m03-03` |
| `No such file … modelo_defecto.joblib` | saltaste M03-03 | `m03-03` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| la línea de ahora da una tasa de revisar muy alta | acabas de provocar el fallo de refrigeración del M06-03 y la estación sigue caliente | espera unos minutos y vuelve a ejecutar |

## Conclusiones

### Qué es la deriva

Es que **la línea cambie** y el modelo siga contestando como si nada. El modelo aprendió con un proceso concreto; si cambia el refrigerante, llega el verano o se cambia de utillaje, sus dictámenes dejan de describir la realidad. No da ningún error.

### Cómo debe vigilarse

| Requisito | En el lab |
|-----------|-----------|
| Una línea base | Con el proceso normal, el 8 % de las piezas va a revisión |
| Una medida periódica | La misma tasa con los datos de ahora |
| Un [umbral](../glosario/03-aprendizaje-automatico.md#umbral) de alarma | Avisar si sube más de 0,10 |
| Un registro | `seguimiento.json` con las dos tasas |

Resultado: con el husillo 8 °C más caliente, la tasa pasó del **8 % al 96 %**; con solo 2 °C, al 28 %. En la línea en vivo, durante un fallo de refrigeración, al 28 %.

### Cómo se detecta

- **Cambio en lo que dice el modelo**: más o menos piezas a revisión de lo habitual.
- **Cambio en lo que recibe**: la temperatura media, la vibración… se alejan de las del entrenamiento.
- **Cambio en el resultado real**: calidad encuentra defectos que el modelo no marcó, o al revés.

### Qué se hace cuando aparece

| Situación | Qué hacer |
|-----------|-----------|
| El servicio está caído | Es una avería: se reinicia; no hay que reentrenar |
| El proceso cambió de forma legítima | Reentrenar con datos del proceso nuevo y desplegar otra versión |
| El proceso se ha desviado por un problema | Avisar a proceso o mantenimiento: el problema es la máquina, no el modelo |

### En una frase

> 🔑 Poner un modelo en marcha no es el final: hay que medir cada día si la línea sigue pareciéndose a la que aprendió.
