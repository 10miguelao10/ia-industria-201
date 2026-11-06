# M03-04 — Entrenar con los datos de tu línea

[← Página anterior](M03-03-comparacion-modelos.md) · [Siguiente página →](../M04-vision-control-calidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué supone **entrenar con datos recogidos de la propia producción**: cómo debe partirse un dataset real, qué puede descubrir un modelo sobre el proceso, qué límites le ponen los datos y las etiquetas, y cómo se mejora recogiendo mejor.

### Prerrequisitos

- M02-04 hecho: existe `infra/data/dataset_linea.csv`.
- Solo `lab`. CPU, sin GPU.

### Qué está pasando

Hasta ahora, en M03-01 a M03-03, los modelos aprendían de un histórico generado de golpe por el laboratorio. En el M02-04 construiste **tu propio dataset**: las carcasas que tu estación ha fabricado, con las señales que guardó el archivador y el resultado que apuntó calidad.

Ahora entrenas con él. Es lo que haría un equipo en planta: no hay un fichero preparado, sino unos cientos de piezas de unos minutos de producción, con sus huecos y sus errores de inspección.

Vas a entrenar los dos tipos de modelo que ya conoces, con la misma regla del M03-03:

| Modelo | Qué es |
|--------|--------|
| Árbol de decisión | Reglas del tipo «si la corriente pasa de X y la vibración de Y…». Se puede leer |
| Red neuronal (32 neuronas) | La que pruebas en el «Experimenta» del M03-03, con las señales escaladas. En el M04-04 verás cómo se entrena paso a paso. No se puede leer |

Y vas a ver algo que en el M03 no podías: **qué señales ha usado el modelo**, para compararlo con el criterio de calidad que descubriste a mano en el M02-04.

### 1 — Entrenar con tu dataset

**Qué ocurre:** ordenas las piezas por hora, entrenas con el 70 % más antiguo y examinas con el 30 % más reciente, como harías antes de poner el modelo en la línea. Solo se usan las tres señales que la estación publica en vivo: temperatura, vibración y corriente.

```bash
docker compose --profile lab run --rm --no-deps lab m03-04
```

📋 Ficha del comando [`m03-04`](../comandos-lab.md#m03-04): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambian los números: es tu producción):

```text
317 piezas para entrenar, 137 para examinar (las más recientes)
árbol                  defectos encontrados 10 de 12  falsas alarmas   1 de 125
red (32)               defectos encontrados  8 de 12  falsas alarmas   2 de 125
qué señales usa el árbol (importancia):
  corriente_a      0.61
  vibracion_mm_s   0.29
  temperatura_c    0.10
OK m03-04: árbol recall=0.83 fpr=0.01; red recall=0.67 fpr=0.02
```

**Cómo se lee:**

- **Los dos modelos encuentran la mayoría de los defectos** de las carcasas más recientes, con muy pocas falsas alarmas.
- **El árbol gana a la red** en estos datos: con tres señales y unos cientos de piezas, un modelo sencillo basta.
- **La importancia** dice cuánto ha usado el árbol cada señal. Corriente y vibración suman el 90 %: **son las mismas dos señales** del criterio que descubriste en el M02-04. El modelo ha encontrado el criterio de calidad sin que nadie se lo dijera.
- La temperatura pesa poco: no influye en el defecto, y lo poco que pesa es el árbol ajustándose al ruido.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m03_04</code>)</summary>

```python
SENALES_VIVAS = ["temperatura_c", "vibracion_mm_s", "corriente_a"]   # lo que la estación publica

df = pd.read_csv(DATA / "dataset_linea.csv").sort_values("ts")      # en orden de fabricación
corte = int(len(df) * 0.7)
train, test = df.iloc[:corte], df.iloc[corte:]                       # pasado / más reciente

arbol = DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=7)
arbol.fit(train[SENALES_VIVAS], train["defecto"])
red = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(32,), max_iter=1000, random_state=0))
red.fit(train[SENALES_VIVAS], train["defecto"])

# cuánto ha usado el árbol cada señal para decidir
for senal, peso in zip(SENALES_VIVAS, arbol.feature_importances_): ...
joblib.dump(arbol, DATA / "modelo_linea.joblib")
```

</details>

### 2 — Más producción, otro resultado

**Qué ocurre:** la línea ha seguido fabricando y calidad inspeccionando desde el M02-04. Vuelves a construir el dataset, ahora con más piezas, y entrenas otra vez.

```bash
docker compose --profile lab run --rm --no-deps lab m02-04
docker compose --profile lab run --rm --no-deps lab m03-04
```

**Resultado esperado:** más piezas para entrenar y examinar, y números algo distintos. La importancia sigue señalando corriente y vibración.

**Cómo se lee:** con pocos cientos de piezas, el resultado de examen **cambia bastante** de un día a otro: 12 defectos de examen son muy pocos para medir con precisión. Lo que se mantiene estable es **lo que el modelo ha aprendido del proceso** (qué señales importan). Por eso, antes de fiarse de un porcentaje, hay que fijarse en cuántos casos hay detrás.

## Comprueba tu entendimiento

**Por qué en orden de tiempo**

¿Por qué se examina con las carcasas más recientes y no con una muestra al azar?

→ Porque así se usará el modelo: aprendiendo del pasado para decidir sobre lo que viene. Si el proceso cambia con el tiempo, examinar al azar lo escondería.

## Investiga: las reglas que ha aprendido de tu línea

**Qué ocurre:** lees las reglas del árbol entrenado con tu dataset, con el mismo comando de ayuda que en el M03-03.

```bash
docker compose --profile lab run --rm --no-deps lab arbol linea
```

**Resultado esperado** (cambia con tu producción):

```text
reglas de modelo_linea.joblib (class: 1 = defecto, 0 = buena):
|--- corriente_a <= 4.085
|   |--- …                         (todas las ramas: class: 0)
|--- corriente_a >  4.085
|   |--- vibracion_mm_s <= 0.257
|   |   |--- temperatura_c <= 60.920
|   |   |   |--- class: 1
|   |   |--- temperatura_c >  60.920
|   |   |   |--- class: 0
|   |--- vibracion_mm_s >  0.257
|   |   |--- temperatura_c <= 60.975
|   |   |   |--- class: 0
|   |   |--- temperatura_c >  60.975
|   |   |   |--- class: 1

OK arbol: 8 hojas, profundidad 3
```

**Cómo se lee:** las dos primeras preguntas son **el criterio de calidad** que encontraste a mano en el M02-04: corriente por encima de 4,08 y vibración por encima de ~0,26. El modelo lo ha descubierto solo. Pero la tercera pregunta, sobre la temperatura (60,92 y 60,98 °C), **no tiene sentido**: el criterio real no mira la temperatura. Es el árbol aprendiendo el **ruido** de unas pocas piezas, probablemente las que calidad inspeccionó mal. Con más datos o un árbol menos profundo, desaparecería.

## Experimenta: el modelo explica el proceso

**Qué ocurre:** el árbol se puede leer, y eso permite comparar lo que ha aprendido con lo que sabes del proceso. Repasa los dos resultados:

| Lo que descubriste a mano (M02-04) | Lo que dice el árbol (M03-04) |
|------------------------------------|-------------------------------|
| Defecto casi seguro con vibración **y** corriente altas | Importancia: corriente 0,61, vibración 0,29 |
| La temperatura no cambia la tasa de defecto | Temperatura: 0,10 |

**Pregunta:** si el árbol hubiera dado a la temperatura la importancia más alta, ¿qué pensarías?

<details>
<summary>Ver solución</summary>

Que algo no cuadra, y habría que investigar antes de usarlo: un dataset demasiado pequeño, una unión mal hecha (como la del `pieza_id` del M02-04) o una relación casual. Un modelo que contradice lo que se sabe del proceso no se pone en la línea sin entender por qué. Esa comprobación solo es posible con modelos que se pueden leer, como el árbol; con la red no podrías hacerla.

</details>

## Reto

### 1 — Entrenar con muy poca producción

Si solo tuvieras 2 minutos de producción (unas 120 piezas, con unos 15 defectos), ¿te fiarías del modelo?

<details>
<summary>Ver solución</summary>

No. Con unos 15 defectos, el 30 % de examen tendría 4 o 5: un acierto más o menos cambia el resultado un 20 %. Y con tan pocos ejemplos, el modelo puede aprender casualidades. `m02-04` no construye el dataset por debajo de 200 piezas precisamente por eso. En planta, cuántos datos hacen falta depende sobre todo de **cuántos defectos** hay, no de cuántas piezas.

</details>

### 2 — El techo del acierto

Calidad se equivoca en un 3 % de las inspecciones. ¿Qué pasa si el modelo «falla» en una carcasa cuya etiqueta estaba mal?

<details>
<summary>Ver solución</summary>

Que el modelo tenía razón y la medida dice que se ha equivocado. Por eso no se puede esperar un 100 % contra etiquetas imperfectas. Cuando un modelo bueno discrepa de calidad, merece la pena revisar esa pieza: a veces quien se equivoca es la inspección.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: falta dataset_linea.csv` | No se hizo M02-04 | Haz M02-04 y repite |
| Ningún defecto en el examen (`de 0`) | Muy poca producción o una tanda sin defectos | Deja fabricar más, repite `m02-04` y luego `m03-04` |
| Resultados muy distintos cada vez | Pocos datos | Normal con pocos cientos de piezas; fíjate en la importancia, que es más estable |

## Conclusiones

### Qué es entrenar con datos de la propia línea

Es cerrar el ciclo completo: la línea fabrica, el histórico guarda cómo, calidad apunta cómo salió, se unen las dos fuentes y un modelo aprende la relación. Es lo más parecido al trabajo real en planta, con todos sus problemas.

### Cómo debe hacerse

| Requisito | En el lab |
|-----------|-----------|
| Partir en orden de tiempo | 70 % más antiguo para entrenar, 30 % más reciente para examinar |
| Usar solo lo que la línea mide en vivo | Tres señales, sin presión |
| Comparar modelos con la misma regla | Árbol y red, con defectos encontrados y falsas alarmas |
| Comprobar que el modelo tiene sentido | La importancia coincide con el criterio de calidad |

### Sus límites y cómo los has visto

| Límite | Cómo lo has visto | Qué provoca |
|--------|-------------------|-------------|
| Pocos datos | El resultado cambia al recoger más | Porcentajes poco fiables |
| Pocos defectos | 12 defectos de examen | Un solo acierto cambia mucho la medida |
| Etiquetas con error | El 3 % de la inspección | Un techo al acierto medible |
| La red no se puede leer | Solo el árbol dice qué señales usa | No se puede comprobar si la red tiene sentido |

### Cómo se mejora

- **Recoger durante más tiempo**, hasta tener suficientes **defectos**, no solo suficientes piezas.
- **Mejorar las etiquetas**: revisar las piezas en las que el modelo y calidad discrepan.
- **Preferir modelos que se puedan explicar** cuando rinden igual: en planta, hay que poder justificar por qué se paró una pieza.
- **Volver a entrenar** cuando cambie el proceso, con datos nuevos y la misma regla (M07-02).

### En una frase

> 🔑 Con datos de tu propia línea, un modelo puede descubrir cómo funciona el proceso. Pero solo te puedes fiar de él si tiene suficientes ejemplos y si lo que ha aprendido tiene sentido para quien conoce la máquina.
