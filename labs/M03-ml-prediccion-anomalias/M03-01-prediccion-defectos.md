# M03-01 — Predicción de defectos de fabricación

[← Página anterior](README.md) · [Siguiente página →](M03-02-anomalias.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es un **modelo de predicción de defectos**: cómo aprende de las piezas pasadas, cómo debe evaluarse para que el resultado sea creíble, cómo se interpretan sus errores y cómo se mejora.

### Prerrequisitos

- `infra/data/limpio.csv` (sale de M02-03). Si falta, este comando lo regenera.
- RAM del entrenamiento: ~0,5 GB. CPU, sin GPU.

### Qué está pasando

**Calidad** inspecciona las carcasas después de que salgan de EST-01 y marca las defectuosas. Cuando aparece una mala, la pregunta de siempre es: ¿se podía haber visto venir con lo que medía la máquina?

Eso es lo que vas a intentar. Un modelo mira las señales de cada carcasa (temperatura, vibración, corriente y presión) y aprende qué combinaciones acaban en defecto. Para que la prueba sea honesta, se entrena con el **pasado** (el 70 % de las piezas más antiguas) y se evalúa con el **futuro** (el 30 % más reciente), piezas que el modelo nunca ha visto.

En planta lo que importa son dos números:

- **Cuántos defectos encuentra.** Cada defecto que se escapa puede acabar en el cliente.
- **Cuántas piezas buenas manda a revisar sin motivo.** Cada falsa alarma es una pieza que alguien revisa a mano para nada.

El modelo no ve la columna `defecto` como entrada: esa información llega tarde, después de la inspección.

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

`class_weight="balanced"` da más peso a la clase rara (defecto); sin él, el modelo aprende a decir siempre «bien».

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

Un modelo de regresión logística con 4 entradas ocupa poco más de 1 KB: son 4 pesos y un término independiente.

## Comprueba tu entendimiento

**Qué número mirar**

En el JSON, lee `recall` y `fn`.

→ `fn` son defectos reales que el modelo dejó pasar. `recall` es la fracción que sí encontró.

## Experimenta: mover el umbral

**Qué ocurre:** el modelo no dice «defecto» o «buena»: da una **probabilidad**, y el código decide con un **umbral** (0,5 por defecto). Vas a probar con un umbral más bajo (más desconfiado) y uno más alto (más permisivo).

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

**Cómo se lee:** con estos costes, el mejor umbral es **0,3**, aunque dé 78 falsas alarmas, porque cada defecto escapado cuesta cien veces más que una revisión. Si revisar costara 50 € (una pieza que hay que desmontar), el resultado cambiaría. Prueba a recalcularlo. El umbral **no lo decide quien entrena el modelo**: lo decide calidad con estos números.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: recall de defecto demasiado bajo` | el CSV limpio está mal generado | repite `m02-03` y luego `m03-01` |
| no está `limpio.csv` | no hiciste M02-03 | el comando lo crea si falta; si falla, lanza `m02-03` |

## Conclusiones

### Qué es un modelo de predicción de defectos

Es una función aprendida de ejemplos: recibe las señales de una carcasa (temperatura, vibración, corriente, presión) y devuelve si cree que saldrá defectuosa. Aprende de piezas pasadas que calidad ya marcó, buscando qué combinaciones de señales acabaron en defecto.

### Cómo debe evaluarse

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Con piezas que no ha visto | Se examina con el 30 % que no se usó para entrenar |
| En orden de tiempo | Entrena con el pasado y se examina con lo más reciente, como pasará en la línea |
| Sin hacer trampa | La etiqueta `defecto` no entra como señal: llega después de la inspección |
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
- **Mover el umbral de decisión** según qué error sea más caro para la planta (lo has hecho: con 500 € por defecto y 5 € por revisión, gana 0,3).
- **Equilibrar las clases** al entrenar: sin hacerlo, el modelo dejó escapar 9 defectos.
- **Añadir señales** que expliquen el defecto, y **más piezas defectuosas** de ejemplo, que son las que escasean.

### En una frase

> 🔑 Un modelo se evalúa con piezas que no ha visto y se mide por los defectos que deja escapar y las piezas buenas que para. Un solo porcentaje no responde a eso.
