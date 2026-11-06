# M03-01 — Predicción de defectos de fabricación

[← Página anterior](README.md) · [Siguiente página →](M03-02-anomalias.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es un **modelo de predicción de defectos**: cómo aprende de las piezas pasadas, cómo debe evaluarse para que el resultado sea creíble, cómo se interpretan sus errores y cómo se mejora.

### Prerrequisitos

- `infra/data/limpio.csv`, el [dataset](../glosario/01-datos-arquitectura.md#dataset) limpio que preparaste en M02-03. Si no lo tienes, el comando del paso 1 (`lab m03-01`) lo genera solo antes de entrenar. También puedes regenerarlo aparte:

  ```bash
  # Comprueba si existe el dataset limpio
  ls -l data/limpio.csv

  # Si no existe: lo regenera (crudo.csv → limpio.csv), como en M02-03
  docker compose --profile lab run --rm --no-deps lab m02-03
  ```

  📋 Fichas de [`m03-01`](../comandos-lab.md#m03-01) y [`m02-03`](../comandos-lab.md#m02-03).

- «Constrúyelo tú» lee el mismo `limpio.csv` y **no** lo genera: haz antes el paso 1 o el comando de arriba.
- RAM del entrenamiento: ~0,5 GB. CPU, sin GPU.

### Qué está pasando

**Calidad** inspecciona las carcasas después de que salgan de EST-01 y marca las defectuosas. Cuando aparece una mala, la pregunta de siempre es: ¿se podía haber visto venir con lo que medía la máquina?

Eso es lo que vas a intentar. Un modelo mira las [señales](../glosario/03-aprendizaje-automatico.md#senal) de cada carcasa (temperatura, vibración, corriente y presión) y aprende qué combinaciones acaban en defecto. Para que la prueba sea honesta, se entrena con el **pasado** (el 70 % de las piezas más antiguas) y se evalúa con el **futuro** (el 30 % más reciente), piezas que el modelo [nunca ha visto](../glosario/03-aprendizaje-automatico.md#particion).

En planta lo que importa son dos números:

- **Cuántos defectos encuentra.** Cada defecto que se escapa puede acabar en el cliente.
- **Cuántas piezas buenas manda a revisar sin motivo.** Cada [falsa alarma](../glosario/03-aprendizaje-automatico.md#matriz-confusion) es una pieza que alguien revisa a mano para nada.

El modelo no ve la columna `defecto` como entrada: esa información [llega tarde](../glosario/03-aprendizaje-automatico.md#fuga), después de la inspección.

### 0 — Mirar los datos con los que va a aprender

**Qué ocurre:** antes de entrenar nada, abres en VS Code el fichero del que aprenderá el modelo: `infra/data/limpio.csv`.

**Qué ves:** una fila por pieza, con cuatro señales (`temperatura_c`, `vibracion_mm_s`, `corriente_a`, `presion_bar`), la columna `defecto` (1 = calidad la marcó como mala) y `hueco`. Desplázate: casi todas tienen `defecto` a 0. El modelo tendrá muy pocos ejemplos de lo que más interesa encontrar.

### 1 — Entrenar y evaluar con piezas nuevas

Vas a entrenar con el pasado y evaluar con piezas que el modelo no ha visto. El porcentaje global engaña cuando el defecto es la clase pequeña, así que el paso imprime los cuatro casos de la matriz de confusión, el recall y las falsas alarmas.

```bash
# Entrena con el 70 % primero, evalúa con el 30 % último y guarda el modelo
docker compose --profile lab run --rm --no-deps lab m03-01
```

📋 Ficha del comando [`m03-01`](../comandos-lab.md#m03-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
{"tp": 15, "fp": 38, "fn": 6, "tn": 172, "recall": 0.7142857142857143, "fpr": 0.18095238095238095}
OK m03-01: recall_defecto=0.71 falsas_alarmas=0.18
```

Cómo se lee:

| Campo | Qué es | Aquí |
|-------|--------|------|
| `tp` | defectos que el modelo marcó | 15 |
| `fn` | defectos que se le escaparon | 6 |
| `fp` | piezas buenas marcadas como defecto (falsas alarmas) | 38 |
| `tn` | piezas buenas que dejó pasar | 172 |
| `recall` | defectos encontrados ÷ defectos reales = 15 / 21 | 0,71 |
| `fpr` | falsas alarmas ÷ piezas buenas = 38 / 210 | 0,18 |

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
FEATURES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]

df = pd.read_csv(DATA / "limpio.csv")
train, test = _partir(df)                     # ordena por pieza y corta en el 70 %
modelo = LogisticRegression(class_weight="balanced", max_iter=400)
modelo.fit(train[FEATURES], train["defecto"])  # aprende: señales → defecto
pred = modelo.predict(test[FEATURES])          # predice piezas no vistas
tasas = _tasas(test["defecto"], pred)          # tp, fp, fn, tn, recall y fpr
joblib.dump(modelo, DATA / "modelo_logreg.joblib")
```

`class_weight="balanced"` da más peso a la [clase rara](../glosario/03-aprendizaje-automatico.md#desequilibrio) (defecto); sin él, el modelo aprende a decir siempre «bien».

</details>

### 2 — Comprobar que el modelo quedó en disco

Vas a ver el fichero del modelo. Sin fichero no hay nada que comparar en M03-03 ni que servir después.

```bash
ls -l data/modelo_logreg.joblib
```

**Resultado esperado:**

```text
-rw-r--r-- 1 root root 1279 Nov  4 18:14 data/modelo_logreg.joblib
```

Un modelo de [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) con 4 entradas ocupa poco más de 1 KB: son 4 pesos y un término independiente.

## Comprueba tu entendimiento

**Qué número mirar**

En el JSON, lee `recall` y `fn`.

→ `fn` son defectos reales que el modelo dejó pasar. `recall` es la fracción que sí encontró.

## Experimenta: mover el umbral

**Qué ocurre:** el modelo no dice «defecto» o «buena»: da una **probabilidad**, y el código decide con un **[umbral](../glosario/03-aprendizaje-automatico.md#umbral)** (0,5 por defecto). Vas a probar con un umbral más bajo (más desconfiado) y uno más alto (más permisivo).

**Predice:** con un umbral de 0,3, ¿encontrará más o menos defectos? ¿Y las falsas alarmas?

```bash
docker compose --profile lab run --rm --no-deps lab m03-01 umbral=0.3
docker compose --profile lab run --rm --no-deps lab m03-01 umbral=0.7
```

**Resultado esperado:**

```text
umbral=0.3 equilibrar=si
{"tp": 17, "fp": 78, "fn": 4, "tn": 132, "recall": 0.8095238095238095, "fpr": 0.37142857142857144}
OK m03-01: recall_defecto=0.81 falsas_alarmas=0.37
```

```text
umbral=0.7 equilibrar=si
{"tp": 14, "fp": 6, "fn": 7, "tn": 204, "recall": 0.6666666666666666, "fpr": 0.02857142857142857}
OK m03-01: recall_defecto=0.67 falsas_alarmas=0.03
```

| Umbral | Defectos encontrados | Defectos escapados | Falsas alarmas |
|--------|----------------------|--------------------|----------------|
| 0,3 | 17 de 21 | 4 | 78 |
| 0,5 | 15 de 21 | 6 | 38 |
| 0,7 | 14 de 21 | 7 | 6 |

**Cómo se lee:** es el mismo modelo; solo cambia dónde se corta. Bajar el umbral encuentra más defectos a cambio de muchas más falsas alarmas; subirlo, al revés. **No hay un umbral correcto**: hay uno que encaja con lo que le cuesta a la planta cada error.

### Sin avisar de que el defecto es raro

**Qué ocurre:** el modelo se entrena con `class_weight="balanced"`, que da más peso a las pocas piezas defectuosas. Vas a quitarlo.

```bash
docker compose --profile lab run --rm --no-deps lab m03-01 equilibrar=no
```

**Resultado esperado:**

```text
umbral=0.5 equilibrar=no
{"tp": 12, "fp": 0, "fn": 9, "tn": 210, "recall": 0.5714285714285714, "fpr": 0.0}
```

**Cómo se lee:** cero falsas alarmas, pero **9 defectos escapados**. Sin equilibrar, al modelo le compensa decir «buena» casi siempre: acierta más en global y deja pasar más defectos. Es el mismo engaño del acierto global de la demo.

## Reto

### 1 — Una columna que llega tarde

**La situación:** cada fila de `limpio.csv` tiene dos tipos de columnas que nacen en momentos distintos:

| Columna | Quién la escribe | Cuándo |
|---------|------------------|--------|
| `temperatura_c`, `vibracion_mm_s`, `corriente_a`, `presion_bar` | La estación EST-01 | **Durante** el ciclo, mientras se fabrica la carcasa |
| `defecto` | Calidad | **Después**, cuando inspecciona la carcasa en su puesto |

El modelo entrena con las cuatro primeras como entrada y aprende a predecir `defecto`. En el código, la lista de entradas es `FEATURES` (en `cmd_m03_01`) o `SENALES` (en tu script de «Constrúyelo tú»).

Un compañero propone: «Añade `defecto` a esa lista de entradas, junto a las cuatro señales. El modelo acertará el 100 %».

**La pregunta:** ¿acertaría de verdad el 100 % en el examen? Y, sobre todo, ¿serviría en la línea, cuando una carcasa acaba de salir de EST-01 y hay que decidir si se manda a revisar?

<details>
<summary>Ver solución</summary>

**En el examen, sí, acierta el 100 %.** Lo comprobarás en el paso 9 de «Constrúyelo tú»: 21 defectos encontrados de 21 y 0 falsas alarmas. Pero no ha aprendido nada del proceso: ha aprendido «si la columna `defecto` vale 1, es defecto». Copia la respuesta.

**En la línea, no sirve.** El modelo tiene que decidir cuando la carcasa sale de la estación, y en ese momento calidad todavía no la ha inspeccionado: la columna `defecto` **aún no existe**. Al modelo le faltaría una de sus entradas justo cuando hace falta. Y, si ya tuvieras ese dato, no necesitarías el modelo.

**La regla:** como entrada del modelo solo vale lo que **ya se conoce en el momento de decidir**. Meter un dato que llega después se llama [fuga de información](../glosario/03-aprendizaje-automatico.md#fuga).

**Cómo se detecta:** un resultado demasiado bueno, como un 100 % en un problema real, es sospechoso. Ante cada columna de entrada, pregúntate **quién la escribe y cuándo**.

</details>

## Mejora: elegir el umbral por lo que cuesta

**Qué ocurre:** conviertes los errores en dinero para elegir el umbral con un criterio que la planta entiende. Supón que un **defecto que llega al cliente cuesta 500 €** (reclamación, devolución) y **revisar una pieza buena cuesta 5 €** (unos minutos de un operario).

Con los números de «Experimenta», calcula el coste de cada umbral: `coste = 500 × escapados + 5 × falsas alarmas`.

| Umbral | Escapados | Falsas alarmas | Coste |
|--------|-----------|----------------|-------|
| 0,3 | 4 | 78 | 500 × 4 + 5 × 78 = **2 390 €** |
| 0,5 | 6 | 38 | 500 × 6 + 5 × 38 = **3 190 €** |
| 0,7 | 7 | 6 | 500 × 7 + 5 × 6 = **3 530 €** |

**Cómo se lee:** con estos costes, de estos tres el mejor umbral es **0,3**, aunque dé 78 falsas alarmas, porque cada defecto escapado cuesta cien veces más que una revisión. Si revisar costara 50 € (una pieza que hay que desmontar), el resultado cambiaría. Prueba a recalcularlo. El umbral **no lo decide quien entrena el modelo**: lo decide calidad con estos números. En «Constrúyelo tú» lo calcularás para todos los umbrales y descubrirás que hay uno mejor.

## Constrúyelo tú: tu propio modelo

**Qué está pasando:** hasta aquí, `lab m03-01` lo ha hecho todo por ti. Ahora construyes tú el mismo modelo, **pieza a pieza**: en cada paso añades un bloque de código a un fichero, lo ejecutas y ves qué ha hecho. Al final tendrás unas treinta líneas de Python que parten los datos, entrenan, enseñan lo aprendido, evalúan y eligen el umbral con los costes de la planta. Y, como el código es tuyo, podrás decidir lo que el comando no te deja tocar: con qué señales aprende el modelo y qué precio tiene cada error.

**Cómo se trabaja en cada paso:**

1. Lees qué va a hacer el bloque y para qué.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m03_01_mi_modelo.py`](../../infra/construye/m03_01_mi_modelo.py). Arriba están las **decisiones** que cambiarás al final (`SENALES`, `COSTE_ESCAPADO`, `COSTE_REVISION`); debajo, el paso 1 ya escrito, que carga `limpio.csv`, y los huecos vacíos de los pasos 2 a 6. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_01_mi_modelo.py
```

**Resultado esperado:**

```text
piezas=768 defectuosas=68 señales=['temperatura_c', 'vibracion_mm_s', 'corriente_a', 'presion_bar']
```

**Cómo se lee:** el script carga las 768 piezas, de las que 68 son defectuosas, y se para porque el resto está vacío. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero** con su Python y sus librerías, en vez de un comando del curso; `infra/construye/` de tu equipo se ve dentro como `/construye/`.

### 2 — Partir en pasado y futuro

**Qué ocurre:** separas las piezas antiguas, con las que aprenderá el modelo, de las recientes, con las que lo examinarás. Se corta **por orden de fabricación**, no al azar, porque en la línea el modelo siempre decidirá sobre piezas posteriores a las que vio al aprender.

Pega debajo de `# --- PASO 2`:

```python
df = df.sort_values("pieza_id")           # ordena las piezas en el orden en que se fabricaron
corte = int(len(df) * 0.7)                # la fila donde acaba el 70 % más antiguo
entrenar = df.iloc[:corte]                # el pasado: con esto aprende el modelo
examen = df.iloc[corte:]                  # el futuro: piezas que el modelo no verá al aprender
print(f"entrenar={len(entrenar)} examen={len(examen)} defectos_en_examen={int(examen['defecto'].sum())}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (línea nueva):

```text
entrenar=537 examen=231 defectos_en_examen=21
```

**Cómo se lee:** 537 piezas para aprender (el 70 %) y 231 para el examen, de las que 21 son defectuosas. Esos 21 son los defectos que el modelo tendrá que encontrar sin haberlos visto. `iloc[:corte]` toma las filas desde la primera hasta el corte; `iloc[corte:]`, desde el corte hasta el final.

### 3 — Entrenar y ver qué ha aprendido

**Qué ocurre:** creas el modelo y lo entrenas con las señales del pasado. `fit` es la línea que «aprende». Después imprimes lo que ha aprendido, que en una regresión logística son **un peso por señal** y un término independiente: nada más.

Pega debajo de `# --- PASO 3`:

```python
# Crea el modelo: "balanced" da más peso a la clase rara (defecto)
modelo = LogisticRegression(class_weight="balanced", max_iter=400)

# Entrena: busca un peso por señal que relacione las señales con la columna defecto
modelo.fit(entrenar[SENALES], entrenar["defecto"])

# Enseña lo que ha aprendido: un peso por señal y un término independiente
for senal, peso in zip(SENALES, modelo.coef_[0]):
    print(f"peso {senal:15s} {peso:+.3f}")
print(f"término independiente  {modelo.intercept_[0]:+.3f}")
```

**Resultado esperado** (líneas nuevas):

```text
peso temperatura_c   +0.619
peso vibracion_mm_s  +2.280
peso corriente_a     +0.281
peso presion_bar     -1.420
término independiente  -32.681
```

**Cómo se lee:** esos cinco números **son el modelo**; es lo que se guarda en el `.joblib` de 1 KB del paso 2 del lab. El **signo** dice hacia dónde empuja cada señal: más temperatura, más vibración y más corriente acercan al defecto; más presión lo aleja. El tamaño de cada peso no se puede comparar a simple vista, porque cada señal tiene sus unidades. En la ficha de la [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) del glosario tienes la cuenta a mano con estos mismos pesos.

### 4 — Ver qué probabilidad da a cada pieza

**Qué ocurre:** antes de decidir nada, pides al modelo la **probabilidad de defecto** de cada pieza de examen y miras los dos extremos: las tres piezas que ve más sospechosas y las tres que ve más seguras, junto a lo que dijo calidad de verdad.

Pega debajo de `# --- PASO 4`:

```python
# Probabilidad de defecto (de 0 a 1) para cada pieza de examen
examen = examen.assign(probabilidad=modelo.predict_proba(examen[SENALES])[:, 1])

# Las 3 piezas que el modelo ve más sospechosas y las 3 que ve más seguras
columnas = ["pieza_id", "temperatura_c", "probabilidad", "defecto"]
print(examen.sort_values("probabilidad", ascending=False)[columnas].head(3).round(3).to_string(index=False))
print(examen.sort_values("probabilidad")[columnas].head(3).round(3).to_string(index=False))
```

**Resultado esperado** (líneas nuevas):

```text
pieza_id  temperatura_c  probabilidad  defecto
   H0776          67.13         0.919        1
   H0717          68.01         0.918        1
   H0562          67.45         0.916        1
pieza_id  temperatura_c  probabilidad  defecto
   H0700          54.83         0.003        0
   H0792          55.68         0.010        0
   H0712          56.17         0.013        0
```

**Cómo se lee:** el modelo **no dice «defecto» o «buena»**: da un número entre 0 y 1. En los extremos acierta: las tres más sospechosas (0,92) eran defectuosas y las tres más seguras (0,01) eran buenas. Fíjate también en la temperatura: las sospechosas están a 67-68 °C y las seguras a 55-56 °C. El problema está en las piezas del medio, que es donde hay que decidir.

### 5 — Decidir con un umbral y contar aciertos y errores

**Qué ocurre:** conviertes la probabilidad en una decisión con un **umbral**: si la probabilidad llega al umbral, la pieza va a revisión. Después cuentas los cuatro casos de la [matriz de confusión](../glosario/03-aprendizaje-automatico.md#matriz-confusion). Lo escribes como una función, `evaluar(umbral)`, porque en el paso siguiente la usarás con diecinueve umbrales.

Pega debajo de `# --- PASO 5`:

```python
def evaluar(umbral):
    """Decide con un umbral y cuenta los cuatro casos sobre las piezas de examen."""
    decision = (examen["probabilidad"] >= umbral).astype(int)   # 1 = «mándala a revisar»
    tn, fp, fn, tp = confusion_matrix(examen["defecto"], decision, labels=[0, 1]).ravel()
    return int(tp), int(fp), int(fn), int(tn)

tp, fp, fn, tn = evaluar(0.5)
print(f"umbral 0.5 -> encontrados={tp} escapados={fn} falsas_alarmas={fp} correctas={tn}")
```

**Resultado esperado** (línea nueva):

```text
umbral 0.5 -> encontrados=15 escapados=6 falsas_alarmas=38 correctas=172
```

**Cómo se lee:** es **exactamente** lo que daba `lab m03-01`: 15 encontrados, 6 escapados, 38 falsas alarmas. Has reconstruido el comando. Fíjate en que `evaluar` **no vuelve a entrenar**: usa las probabilidades del paso 4 y solo cambia dónde se corta. Por eso mover el umbral no cambia el modelo.

### 6 — Elegir el umbral por lo que cuesta

**Qué ocurre:** en «Mejora» comparaste tres umbrales a mano. Ahora el código recorre diecinueve, calcula lo que cuestan los errores de cada uno y se queda con el más barato.

**De dónde salen los euros:** pasar los errores a dinero permite sumar dos fallos que no pesan igual y elegir con un criterio que calidad entiende. Los precios son los dos que fijaste arriba del fichero, los mismos que en «Mejora»:

| Variable | Valor | Qué representa |
|----------|-------|----------------|
| `COSTE_ESCAPADO` | 500 € | Un defecto que llega al cliente: reclamación, devolución |
| `COSTE_REVISION` | 5 € | Revisar a mano una pieza buena: unos minutos de un operario |

```text
coste de un umbral = 500 € × defectos escapados + 5 € × falsas alarmas    (sobre las 231 piezas de examen)
```

Son **un supuesto del lab**, no datos de una planta real. En planta, estos dos precios los aporta calidad, y son los que deciden el resultado: en el paso 8 verás qué pasa si cambian. Además, lo compara con la alternativa de no tener modelo: **revisar a mano todas las piezas**, que no deja escapar ningún defecto y cuesta `COSTE_REVISION` por cada pieza buena.

Pega debajo de `# --- PASO 6`:

```python
print("umbral  escapados  falsas_alarmas  coste")
mejor = None
for i in range(1, 20):                                     # umbrales 0.05, 0.10 … 0.95
    umbral = round(i * 0.05, 2)
    tp, fp, fn, tn = evaluar(umbral)
    coste = COSTE_ESCAPADO * fn + COSTE_REVISION * fp      # lo que cuestan los errores
    print(f"{umbral:6.2f}  {fn:9d}  {fp:14d}  {coste:5d} €")
    if mejor is None or coste < mejor[1]:                  # guarda el más barato
        mejor = (umbral, coste)

buenas = int((examen["defecto"] == 0).sum())
revisar_todo = COSTE_REVISION * buenas                     # sin modelo: se revisa todo a mano
print(f"mejor umbral={mejor[0]} coste={mejor[1]} € | revisar todo={revisar_todo} €")
```

**Resultado esperado** (líneas nuevas; las centrales, recortadas):

```text
umbral  escapados  falsas_alarmas  coste
  0.05          0             188    940 €
  0.10          1             154   1270 €
  0.15          1             129   1145 €
  0.20          1             107   1035 €
  0.25          4              87   2435 €
  0.30          4              78   2390 €
  ...
  0.50          6              38   3190 €
  ...
  0.95         21               0  10500 €
mejor umbral=0.05 coste=940 € | revisar todo=1050 €
```

**Cómo se lee:** dos sorpresas que el comando no enseñaba.

- **El mejor umbral no es 0,3, es 0,05.** En «Mejora» solo mirabas tres. Con un defecto cien veces más caro que una revisión, lo que compensa es no dejar escapar ninguno, aunque eso mande a revisar 188 de 210 piezas buenas.
- **El modelo apenas ahorra.** Revisar todo cuesta 1 050 €; el mejor modelo, 940 €: **110 €** en 231 piezas. Antes de poner un modelo en la línea, compáralo siempre con no tenerlo.

### 7 — Decide tú: las señales

**Qué ocurre:** ahora que el código es tuyo, cambias lo que el comando no te dejaba: la lista `SENALES`, arriba del fichero. Pruébalo dos veces y ejecuta después de cada cambio.

**Predice:** ¿cuál de las cuatro señales es la que más pesa? ¿Qué pasará si la quitas?

```python
SENALES = ["temperatura_c"]                                  # prueba A: solo temperatura
```

```python
SENALES = ["vibracion_mm_s", "corriente_a", "presion_bar"]   # prueba B: todo menos temperatura
```

**Resultado esperado** (líneas que cambian):

```text
# A: solo temperatura
umbral 0.5 -> encontrados=15 escapados=6 falsas_alarmas=37 correctas=173
mejor umbral=0.1 coste=790 € | revisar todo=1050 €
```

```text
# B: sin temperatura
umbral 0.5 -> encontrados=8 escapados=13 falsas_alarmas=97 correctas=113
mejor umbral=0.35 coste=1045 € | revisar todo=1050 €
```

**Cómo se lee:**

| Señales | Escapados a 0,5 | Coste de los errores en el examen, con su mejor umbral | Ahorro frente a revisar todo |
|---------|-----------------|-------------|------------------------------|
| las cuatro | 6 | 940 € | 110 € |
| solo temperatura | 6 | **790 €** | **260 €** |
| todo menos temperatura | 13 | 1 045 € | 5 € |

El coste es el del paso 6: `500 € × escapados + 5 € × falsas alarmas` en las 231 piezas de examen, con el umbral más barato que encuentra el script para esas señales. Revisar todo a mano cuesta siempre 1 050 € (210 piezas buenas × 5 €).

Casi todo lo que el modelo sabe está en la **temperatura**. Sin ella, el modelo no vale nada. Con solo ella, funciona **mejor** que con las cuatro: las otras tres añaden ruido. **Más señales no es mejor modelo**, y que una señal se pueda medir no quiere decir que haya que meterla. Vuelve a dejar las cuatro.

### 8 — Decide tú: el precio de revisar

**Qué ocurre:** con las cuatro señales, cambias `COSTE_REVISION = 5` por `COSTE_REVISION = 50`: la pieza hay que desmontarla para revisarla.

**Predice:** ¿el umbral bueno subirá o bajará? ¿El modelo ahorrará más o menos?

**Resultado esperado** (filas y línea que importan):

```text
  0.65          7              15   4250 €
  0.70          7               6   3800 €
  0.75          8               2   4100 €
...
mejor umbral=0.7 coste=3800 € | revisar todo=10500 €
```

**Cómo se lee:** con el mismo modelo y los mismos datos, el umbral bueno pasa de 0,05 a **0,7**, y el modelo pasa de ahorrar 110 € a ahorrar **6 700 €** (10 500 − 3 800). Lo que vale un modelo no lo deciden solo sus datos: lo decide **lo que cuesta cada error en tu planta**. Por eso quien fija el umbral es calidad, con sus números. Vuelve a poner `COSTE_REVISION = 5`.

### 9 — Haz trampa a propósito

**Qué ocurre:** compruebas el Reto 1. Añades `defecto`, la columna que escribe calidad **después** de inspeccionar, a la lista de entradas del modelo:

```python
# TRAMPA: "defecto" no existe todavía cuando la carcasa sale de la estación
SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar", "defecto"]
```

**Resultado esperado** (líneas que cambian):

```text
peso temperatura_c   +0.302
peso vibracion_mm_s  +0.240
peso corriente_a     +0.082
peso presion_bar     -0.259
peso defecto         +6.724
término independiente  -21.354
umbral 0.5 -> encontrados=21 escapados=0 falsas_alarmas=0 correctas=210
mejor umbral=0.1 coste=0 € | revisar todo=1050 €
```

**Cómo se lee:** mira los pesos del paso 3: el de `defecto` (+6,7) aplasta a todos los demás, que se han encogido. El modelo ha dejado de mirar el proceso y **copia la respuesta**. Resultado: un modelo «perfecto», con coste cero, que no se puede usar en la línea, porque esa entrada llega cuando ya ha pasado el momento de decidir. El script no da ningún error: **ningún programa detecta esta trampa por ti**, solo quien sabe cuándo nace cada dato. Vuelve a dejar las cuatro señales.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: recall de defecto demasiado bajo` | el CSV limpio está mal generado | repite `m02-03` y luego `m03-01` |
| no está `limpio.csv` | no hiciste M02-03 | el comando lo crea si falta; si falla, lanza `m02-03` |
| `NameError: name 'entrenar' is not defined` (o `modelo`, `examen`, `evaluar`) | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for` y `def` |
| `FileNotFoundError: /data/limpio.csv` | no tienes el dataset limpio | lanza el paso 1 del lab (`lab m03-01`), que lo genera |
| tu paso 5 no da 15 / 6 / 38 / 172 | cambiaste `SENALES` o `COSTE_*` arriba del fichero | vuelve a las cuatro señales y a `COSTE_REVISION = 5` |

## Conclusiones

### Qué es un modelo de predicción de defectos

Es una función aprendida de ejemplos: recibe las señales de una carcasa (temperatura, vibración, corriente, presión) y devuelve si cree que saldrá defectuosa. Aprende de piezas pasadas que calidad ya marcó, buscando qué combinaciones de señales acabaron en defecto.

### Cómo debe evaluarse

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Con piezas que no ha visto | Se examina con el 30 % que no se usó para entrenar |
| En orden de tiempo | Entrena con el pasado y se examina con lo más reciente, como pasará en la línea |
| Sin hacer trampa | La [etiqueta](../glosario/03-aprendizaje-automatico.md#etiqueta) `defecto` no entra como señal: llega después de la inspección |
| Con las métricas que importan | Defectos encontrados y falsas alarmas, no un porcentaje global |

### Cómo se interpretan sus errores

De 231 piezas de examen, 21 eran defectuosas:

| | El modelo dijo «defecto» | El modelo dijo «bien» |
|--|--------------------------|-----------------------|
| **Era defectuosa** (21) | 15: defectos encontrados | 6: **defectos que se escapan** |
| **Era buena** (210) | 38: **falsas alarmas** | 172: correctas |

El acierto global sería (15 + 172) / 231 = 81 %, un número que no dice que 6 defectos llegarían al cliente ni que 38 piezas buenas se pararían para nada.

### Cómo se mejora

- **Comparar con otros modelos** sobre el mismo corte (lo harás en M03-03).
- **Mover el umbral de decisión** según qué error sea más caro para la planta (lo has hecho: con 500 € por defecto y 5 € por revisión, de tres umbrales ganaba 0,3; recorriendo diecinueve con tu código, gana 0,05).
- **Equilibrar las clases** al entrenar: sin hacerlo, el modelo dejó escapar 9 defectos.
- **Elegir las señales con criterio**, no meter todas: en «Constrúyelo tú», solo con la temperatura el modelo costó 790 € frente a 940 € con las cuatro.
- **Compararlo con no tener modelo**: con 5 € por revisión, revisar todo costaba 1 050 € y el modelo solo ahorraba 110 €; con 50 €, ahorra 6 700 €.
- **Más piezas defectuosas** de ejemplo, que son las que escasean.

### En una frase

> 🔑 Un modelo se evalúa con piezas que no ha visto y se mide por los defectos que deja escapar y las piezas buenas que para. Un solo porcentaje no responde a eso.
