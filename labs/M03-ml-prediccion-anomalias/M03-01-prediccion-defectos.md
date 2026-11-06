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

### 1 — Columna que llega tarde

Si añadieras la propia columna `defecto` como entrada, el acierto sería perfecto. ¿Sirve?

<details>
<summary>Ver solución</summary>

No predice: lee la respuesta. Las entradas permitidas son solo las señales que existen antes del control de calidad: temperatura, vibración, corriente y presión.

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

**Qué está pasando:** hasta aquí, `lab m03-01` lo ha hecho todo por ti. Ahora lo escribes tú: unas quince líneas de Python que parten los datos, entrenan, evalúan y eligen el umbral con los costes de la planta. Con tu propio código vas a poder decidir cosas que el comando no te deja tocar: con qué señales aprende el modelo y qué precio tiene cada error.

Trabajas sobre un **esqueleto**: el fichero [`infra/construye/m03_01_mi_modelo.py`](../../infra/construye/m03_01_mi_modelo.py). Ya tiene la carga de los datos y las impresiones; los huecos que tienes que rellenar están marcados con **TU PARTE**. Cada hueco tiene una línea `raise NotImplementedError(...)`: bórrala y escribe tu código en su lugar.

📋 Ficha del comando [`construye`](../comandos-lab.md#construye): ejecuta tu script dentro del contenedor `lab`.

### 1 — Ejecutar el esqueleto sin tocarlo

**Qué ocurre:** abres el fichero en VS Code, lo lees de arriba abajo y lo ejecutas tal cual. Así ves qué hace ya y dónde se para.

```bash
# Ejecuta tu script de infra/construye/ en el contenedor lab
docker compose --profile lab run --rm --no-deps lab construye m03_01_mi_modelo.py
```

**Resultado esperado:**

```text
piezas=768 defectuosas=68 señales=['temperatura_c', 'vibracion_mm_s', 'corriente_a', 'presion_bar']
FALLO: te falta completar: paso 2: crea las tablas «entrenar» y «examen»
```

**Cómo se lee:** los datos cargan bien (768 piezas, 68 defectuosas) y el script se para en el primer hueco. Ese mensaje te guía en cada paso: cuando completes uno, el siguiente `FALLO` te dirá cuál viene después.

### 2 — Partir en pasado y futuro

**Qué ocurre:** separas las piezas antiguas, con las que aprende el modelo, de las recientes, con las que lo examinas. Es lo que hacía `_partir` dentro de `m03-01`.

**Pista:** `df.sort_values("pieza_id")` ordena por orden de fabricación; `int(len(df) * 0.7)` te da la fila del corte; `df.iloc[:corte]` y `df.iloc[corte:]` toman cada parte.

**Cómo sabes que está bien:** al ejecutar, aparece esta línea antes del siguiente `FALLO`.

```text
entrenar=537 examen=231 defectos_en_examen=21
```

<details>
<summary>Ver solución</summary>

```python
df = df.sort_values("pieza_id")           # orden de fabricación
corte = int(len(df) * 0.7)                # dónde acaba el 70 %
entrenar = df.iloc[:corte]                # pasado: con esto aprende
examen = df.iloc[corte:]                  # futuro: piezas que nunca ha visto
```

Si partes al azar (`df.sample(frac=0.7)`), el modelo aprende con piezas posteriores a las que examina: en la línea nunca tendrás el futuro para entrenar.

</details>

### 3 — Entrenar

**Qué ocurre:** creas el modelo y lo entrenas con las señales del pasado. Esta línea es la que «aprende».

**Pista:** `LogisticRegression(class_weight="balanced", max_iter=400)` crea el modelo; `.fit(X, y)` lo entrena, donde `X` son las columnas `SENALES` de `entrenar` e `y` es su columna `defecto`. Llama `modelo` a lo que crees.

<details>
<summary>Ver solución</summary>

```python
modelo = LogisticRegression(class_weight="balanced", max_iter=400)
modelo.fit(entrenar[SENALES], entrenar["defecto"])   # aprende: señales -> defecto
```

</details>

### 4 — Evaluar con un umbral

**Qué ocurre:** escribes la función que, para un umbral, cuenta los cuatro casos sobre las piezas de examen. Es el corazón de la evaluación: la vas a usar en el paso siguiente con diecinueve umbrales.

**Pista:** `modelo.predict_proba(examen[SENALES])[:, 1]` da la probabilidad de defecto de cada pieza; `(proba >= umbral).astype(int)` la convierte en 0 o 1; `confusion_matrix(examen["defecto"], pred, labels=[0, 1]).ravel()` devuelve `tn, fp, fn, tp`, en ese orden.

**Cómo sabes que está bien:** con las cuatro señales y umbral 0,5, tu modelo tiene que dar **exactamente** lo mismo que `lab m03-01` (15 encontrados, 6 escapados, 38 falsas alarmas, 172 correctas).

```text
umbral 0.5 -> encontrados=15 escapados=6 falsas_alarmas=38 correctas=172
```

Si no coincide, revisa el orden del corte (paso 2) o el orden en que devuelves los cuatro números.

<details>
<summary>Ver solución</summary>

```python
def evaluar(umbral):
    proba = modelo.predict_proba(examen[SENALES])[:, 1]   # probabilidad de defecto
    pred = (proba >= umbral).astype(int)                  # 1 = «mándala a revisar»
    tn, fp, fn, tp = confusion_matrix(examen["defecto"], pred, labels=[0, 1]).ravel()
    return int(tp), int(fp), int(fn), int(tn)
```

</details>

### 5 — Elegir el umbral por lo que cuesta

**Qué ocurre:** en «Mejora» comparaste tres umbrales a mano. Ahora tu código recorre diecinueve y, además, los compara con la alternativa de no tener modelo: **revisar a mano todas las piezas**.

**Pista:** un bucle `for i in range(1, 20)` con `umbral = round(i * 0.05, 2)`; en cada vuelta, `coste = COSTE_ESCAPADO * fn + COSTE_REVISION * fp`. Revisar todo no deja escapar ningún defecto y cuesta `COSTE_REVISION` por cada pieza buena del examen.

**Resultado esperado** (filas centrales recortadas):

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
OK construye m03-01: el modelo ahorra 110 € frente a revisar todo
```

**Cómo se lee:** dos sorpresas que el comando no enseñaba.

- **El mejor umbral no es 0,3, es 0,05.** En «Mejora» solo mirabas tres umbrales. Con un defecto cien veces más caro que una revisión, lo que compensa es no dejar escapar ninguno, aunque eso mande a revisar 188 de 210 piezas buenas.
- **El modelo apenas ahorra.** Revisar todo cuesta 1 050 €; el mejor modelo, 940 €. Con estos costes el modelo vale **110 €** en 231 piezas. Antes de poner un modelo en la línea, compáralo siempre con no tenerlo.

<details>
<summary>Ver solución</summary>

```python
print("umbral  escapados  falsas_alarmas  coste")
mejor = None
for i in range(1, 20):
    umbral = round(i * 0.05, 2)
    tp, fp, fn, tn = evaluar(umbral)
    coste = COSTE_ESCAPADO * fn + COSTE_REVISION * fp
    print(f"{umbral:6.2f}  {fn:9d}  {fp:14d}  {coste:5d} €")
    if mejor is None or coste < mejor[1]:
        mejor = (umbral, coste)

buenas = int((examen["defecto"] == 0).sum())
revisar_todo = COSTE_REVISION * buenas                   # sin modelo: se revisa todo
print(f"mejor umbral={mejor[0]} coste={mejor[1]} € | revisar todo={revisar_todo} €")
print("OK construye m03-01: el modelo", "ahorra" if mejor[1] < revisar_todo else "NO ahorra",
      f"{abs(revisar_todo - mejor[1])} € frente a revisar todo")
```

</details>

### 6 — Decide tú: las señales

**Qué ocurre:** ahora que el código es tuyo, cambias lo que el comando no te dejaba: la lista `SENALES`, al principio del fichero. Pruébalo dos veces y ejecuta después de cada cambio.

**Predice:** ¿cuál de las cuatro señales es la que más pesa? ¿Qué pasará si la quitas?

```python
SENALES = ["temperatura_c"]                                  # prueba A: solo temperatura
SENALES = ["vibracion_mm_s", "corriente_a", "presion_bar"]   # prueba B: todo menos temperatura
```

**Resultado esperado** (últimas líneas de cada prueba):

```text
# A: solo temperatura
umbral 0.5 -> encontrados=15 escapados=6 falsas_alarmas=37 correctas=173
mejor umbral=0.1 coste=790 € | revisar todo=1050 €
OK construye m03-01: el modelo ahorra 260 € frente a revisar todo
```

```text
# B: sin temperatura
umbral 0.5 -> encontrados=8 escapados=13 falsas_alarmas=97 correctas=113
mejor umbral=0.35 coste=1045 € | revisar todo=1050 €
OK construye m03-01: el modelo ahorra 5 € frente a revisar todo
```

**Cómo se lee:**

| Señales | Escapados a 0,5 | Mejor coste | Ahorro frente a revisar todo |
|---------|-----------------|-------------|------------------------------|
| las cuatro | 6 | 940 € | 110 € |
| solo temperatura | 6 | **790 €** | **260 €** |
| todo menos temperatura | 13 | 1 045 € | 5 € |

Casi todo lo que el modelo sabe está en la **temperatura**. Sin ella, el modelo no vale nada. Con solo ella, funciona **mejor** que con las cuatro: las otras tres añaden ruido. **Más señales no es mejor modelo**, y que una señal se pueda medir no quiere decir que haya que meterla.

### 7 — Decide tú: el precio de revisar

**Qué ocurre:** vuelve a poner las cuatro señales y cambia `COSTE_REVISION = 5` por `COSTE_REVISION = 50`: la pieza hay que desmontarla para revisarla.

**Predice:** ¿el umbral bueno subirá o bajará? ¿El modelo ahorrará más o menos?

**Resultado esperado** (últimas líneas):

```text
  0.65          7              15   4250 €
  0.70          7               6   3800 €
  0.75          8               2   4100 €
...
mejor umbral=0.7 coste=3800 € | revisar todo=10500 €
OK construye m03-01: el modelo ahorra 6700 € frente a revisar todo
```

**Cómo se lee:** con el mismo modelo y los mismos datos, el umbral bueno pasa de 0,05 a **0,7**, y el modelo pasa de ahorrar 110 € a ahorrar **6 700 €**. Lo que vale un modelo no lo deciden solo sus datos: lo decide **lo que cuesta cada error en tu planta**. Por eso quien fija el umbral es calidad, con sus números.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: recall de defecto demasiado bajo` | el CSV limpio está mal generado | repite `m02-03` y luego `m03-01` |
| no está `limpio.csv` | no hiciste M02-03 | el comando lo crea si falta; si falla, lanza `m02-03` |
| `FALLO: te falta completar: paso N` | queda un hueco «TU PARTE» con su `raise` | borra la línea `raise NotImplementedError(...)` de ese paso y escribe tu código |
| `NameError: name 'entrenar' is not defined` (o `modelo`) | el nombre de tu variable no es el que espera el resto del esqueleto | usa exactamente `entrenar`, `examen` y `modelo` |
| tu paso 4 no da 15 / 6 / 38 / 172 | corte al azar en vez de por `pieza_id`, o los cuatro números en otro orden | `confusion_matrix(...).ravel()` devuelve `tn, fp, fn, tp` |

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
