# M03-03 — Comparación de modelos predictivos

[← Página anterior](M03-02-anomalias.md) · [Siguiente página →](M03-04-entrenar-datos-linea.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **elige el modelo que va a la línea**: cómo se comparan candidatos de forma justa, cómo debe ser la regla de elección, qué errores son típicos al comparar y cómo queda documentado el elegido.

### Prerrequisitos

- El `limpio.csv` de M02-03.
- Deja `modelo_defecto.joblib` y `VERSION`. Es el modelo que usan M06, M07 y M08.

### Qué está pasando

Ingeniería tiene **dos modelos candidatos** para poner en la línea: la regresión logística del M03-01 y un árbol de decisión sencillo. Hay que elegir uno, y la regla se acuerda **antes** de ver los resultados para que nadie la ajuste a su favor:

1. Gana el que encuentre más defectos.
2. Si empatan, el que dé menos falsas alarmas.

Los dos se entrenan y se evalúan con exactamente las mismas piezas. El ganador se guarda como `modelo_defecto.joblib` con la versión `defecto-0.1`. Es el modelo que usará la línea en M06, M07 y M08.

### 1 — Comparar con la misma vara

Vas a entrenar los dos candidatos con las mismas piezas y medirlos con las mismas piezas nuevas. Sin el mismo corte, la comparación no vale.

```bash
# Entrena logreg y árbol, compara y guarda el ganador como modelo_defecto.joblib
docker compose --profile lab run --rm --no-deps lab m03-03
```

📋 Ficha del comando [`m03-03`](../comandos-lab.md#m03-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
{"logreg": {"tp": 15, "fp": 38, "fn": 6, "tn": 172, "recall": 0.7142857142857143, "fpr": 0.18095238095238095}, "arbol": {"tp": 16, "fp": 3, "fn": 5, "tn": 207, "recall": 0.7619047619047619, "fpr": 0.014285714285714285}}
OK m03-03: elegido=arbol recall=0.76 fpr=0.01
```

| | Defectos encontrados | Falsas alarmas |
|--|----------------------|----------------|
| logreg | 15 de 21 (0,71) | 38 de 210 (0,18) |
| árbol | 16 de 21 (0,76) | 3 de 210 (0,01) |

El árbol encuentra uno más y apenas da falsas alarmas.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
candidatos = {
    "logreg": LogisticRegression(class_weight="balanced", max_iter=400),
    "arbol": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=7),
}
for nombre, modelo in candidatos.items():
    modelo.fit(train[FEATURES], train["defecto"])
    informe[nombre] = _tasas(test["defecto"], modelo.predict(test[FEATURES]))

# Regla: más recall; si empatan, menos falsas alarmas
ganador, datos = max(informe.items(), key=lambda it: (it[1]["recall"], -it[1]["fpr"]))
joblib.dump(datos["modelo"], DATA / "modelo_defecto.joblib")
(DATA / "VERSION").write_text("defecto-0.1\n")
```

</details>

### 2 — Leer lo que quedó escrito

Vas a mirar la versión y el nombre del modelo elegido. Son los ficheros que leerán el servicio y la auditoría.

```bash
cat data/VERSION data/modelo_elegido.txt
```

**Resultado esperado:**

```text
defecto-0.1
arbol
```

## Comprueba tu entendimiento

**La regla**

¿Coincide `modelo_elegido.txt` con lo que imprimió el `OK`?

→ Sí: los dos dicen `arbol`.

## Experimenta: una red neuronal como tercer candidato

**Qué ocurre:** añades a la comparación un tercer candidato, una **red neuronal**: un modelo formado por capas de «neuronas» que combinan las señales con unos pesos que se ajustan al entrenar. En el M04-04 la entrenarás paso a paso con fotos; aquí la usas como un candidato más, con el mismo corte y la misma regla.

`lab m03-red` entrena una red y la compara con el árbol elegido. No cambia el modelo de la línea (`modelo_defecto.joblib`).

📋 Ficha del comando [`m03-red`](../comandos-lab.md#m03-red).

### 1 — La red con las señales escaladas

```bash
# Red con dos capas ocultas de 64 y 32 neuronas
docker compose --profile lab run --rm --no-deps lab m03-red
```

**Resultado esperado:**

```text
árbol (M03-03)         defectos encontrados 16 de 21  falsas alarmas   3 de 210
red (64, 32)           defectos encontrados 16 de 21  falsas alarmas   2 de 210
OK m03-red: red recall=0.76 fpr=0.01; árbol recall=0.76 fpr=0.01
```

**Cómo se lee:** empatan en defectos encontrados (16 de 21) y la red da **una falsa alarma menos**. Por la regla del M03-03, la red ganaría por una pieza. Pero el árbol se puede leer y explicar a calidad («para cuando la vibración pasa de X…»), y la red no. Con una diferencia de una pieza en 210, la mayoría de las plantas se quedaría con el árbol. La regla de elección, en la realidad, también suele incluir «que se pueda explicar».

### 2 — La misma red sin escalar las señales

**Qué ocurre:** repites el entrenamiento sin poner cada señal en su escala. La corriente está en torno a 4, la temperatura en torno a 62 y la vibración en torno a 0,25.

**Predice:** ¿importa?

```bash
docker compose --profile lab run --rm --no-deps lab m03-red sin-escalar
```

**Resultado esperado:**

```text
red (64, 32) sin escalar defectos encontrados  0 de 21  falsas alarmas   0 de 210
```

**Cómo se lee:** la red **no encuentra ningún defecto**: ha aprendido a decir siempre «buena». Con señales de tamaños tan distintos, la temperatura (62) aplasta a la vibración (0,25) y la red no consigue ajustar sus pesos. Las redes necesitan que las entradas estén en escalas parecidas; el árbol no, porque compara cada señal por separado. Es un error típico y silencioso: el comando no falla, simplemente el modelo no sirve.

### 3 — Una red más pequeña

```bash
docker compose --profile lab run --rm --no-deps lab m03-red 8
```

**Resultado esperado:**

```text
red (8,)               defectos encontrados 13 de 21  falsas alarmas   1 de 210
```

Con 8 neuronas encuentra menos defectos. El tamaño de la red también se elige.

## Reto

### 1 — Empate

Si los dos recall fueran iguales, ¿con cuál te quedas?

<details>
<summary>Ver solución</summary>

Con el de menor tasa de falsas alarmas. Es la segunda clave de la regla.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `No such file … limpio.csv` | no está el CSV | lanza `m02-03` |
| `VERSION` vacío | el comando no terminó en `OK` | repite `m03-03` |

## Conclusiones

### Qué es elegir un modelo

Es decidir cuál de varios candidatos se pone en la línea. No es una cuestión técnica de cuál «parece mejor», sino una **decisión de proceso** con criterios que la planta acepta.

### Cómo debe ser la comparación

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Misma vara para todos | Mismas piezas de entrenamiento y de examen |
| Regla escrita antes de ver resultados | Primero más defectos encontrados; si empatan, menos falsas alarmas |
| Métricas de planta | Defectos encontrados y falsas alarmas |
| El elegido queda identificado | `modelo_defecto.joblib`, versión `defecto-0.1` |

Resultado:

| | Defectos encontrados | Falsas alarmas |
|--|----------------------|----------------|
| Regresión logística | 15 de 21 | 38 de 210 |
| **Árbol (elegido)** | **16 de 21** | **3 de 210** |

### Errores típicos al comparar

- Comparar con **cortes distintos**: un modelo parece mejor solo porque le tocaron piezas más fáciles.
- Ajustar la regla **después de ver los resultados** para que gane el favorito.
- Elegir por un **porcentaje global**, que esconde los defectos que se escapan.

### Cómo queda documentado

El modelo elegido es un fichero con **nombre y versión**. Esa versión viajará en cada dictamen (M07) y permitirá reconstruir decisiones (M08). Si mañana se entrena otro, será `defecto-0.2` y se podrá comparar con la misma regla.

### En una frase

> 🔑 El modelo que va a la línea se elige con una regla escrita de antemano, se mide igual que los demás y queda con nombre y versión.
