# M03-01 — Predicción de defectos de fabricación

[← Página anterior](README.md) · [Siguiente página →](M03-02-anomalias.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Entrenas un clasificador que relaciona las señales de proceso con un defecto ya etiquetado, y lo mides por los defectos que encuentra.

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

## Reto

### 1 — Columna que llega tarde

Si añadieras la propia columna `defecto` como entrada, el acierto sería perfecto. ¿Sirve?

<details>
<summary>Ver solución</summary>

No predice: lee la respuesta. Las entradas permitidas son solo las señales que existen antes del control de calidad: temperatura, vibración, corriente y presión.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: recall de defecto demasiado bajo` | el CSV limpio está mal generado | repite `m02-03` y luego `m03-01` |
| no está `limpio.csv` | no hiciste M02-03 | el comando lo crea si falta; si falla, lanza `m02-03` |

## Conclusiones

- **Un modelo de clasificación aprende de ejemplos pasados**: qué combinaciones de señales acabaron en defecto.
- **Se evalúa con piezas que no ha visto**, y en orden de tiempo: entrena con el pasado y se examina con lo más reciente, como pasará en la línea.
- **El porcentaje de acierto global engaña** cuando el defecto es raro. Aquí habría dado un 81 % dejando escapar defectos.
- **Lo que importa son dos números:** cuántos defectos encuentra (recall) y cuántas piezas buenas manda a revisar sin motivo (falsas alarmas). Con este modelo: 15 de 21 defectos y 38 falsas alarmas.
- **El modelo es un fichero** (`modelo_logreg.joblib`) que se guarda, se compara y se despliega.

> 🔑 Pregunta siempre: ¿cuántos defectos se le escapan y cuántas piezas buenas para? Un solo porcentaje no responde a eso.
