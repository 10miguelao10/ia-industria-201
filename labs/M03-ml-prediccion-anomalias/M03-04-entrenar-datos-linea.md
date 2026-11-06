# M03-04 — Entrenar con los datos de tu línea

[← Página anterior](M03-03-comparacion-modelos.md) · [Siguiente página →](../M04-vision-control-calidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué supone **entrenar con datos recogidos de la propia producción**: cómo debe partirse un [dataset](../glosario/01-datos-arquitectura.md#dataset) real, qué puede descubrir un modelo sobre el proceso, qué límites le ponen los datos y las [etiquetas](../glosario/03-aprendizaje-automatico.md#etiqueta), y cómo se mejora recogiendo mejor.

### Prerrequisitos

- M02-04 hecho: existe `infra/data/dataset_linea.csv`.
- Solo `lab`. CPU, sin GPU.

### Qué está pasando

Hasta ahora, en M03-01 a M03-03, los modelos aprendían de un [histórico](../glosario/01-datos-arquitectura.md#historico) generado de golpe por el laboratorio. En el M02-04 construiste **tu propio dataset**: las carcasas que tu estación ha fabricado, con las [señales](../glosario/03-aprendizaje-automatico.md#senal) que guardó el archivador y el resultado que apuntó calidad.

Ahora entrenas con él. Es lo que haría un equipo en planta: no hay un fichero preparado, sino unos cientos de piezas de unos minutos de producción, con sus huecos y sus errores de inspección.

Vas a entrenar los dos tipos de modelo que ya conoces, con la misma regla del M03-03:

| Modelo | Qué es |
|--------|--------|
| [Árbol de decisión](../glosario/03-aprendizaje-automatico.md#arbol) | Reglas del tipo «si la corriente pasa de X y la vibración de Y…». Se puede leer |
| Red neuronal (32 neuronas) | La que pruebas en el «Experimenta» del M03-03, con las señales [escaladas](../glosario/03-aprendizaje-automatico.md#escalado). En el M04-04 verás cómo se entrena paso a paso. No se puede leer |

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

- **Los dos modelos encuentran la mayoría de los defectos** de las carcasas más recientes, con muy pocas [falsas alarmas](../glosario/03-aprendizaje-automatico.md#matriz-confusion).
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

## Constrúyelo tú: tu propio modelo de tu línea

**Qué está pasando:** `lab m03-04` entrena con tu dataset y enseña lo que ha aprendido. Ahora lo entrenas tú: un árbol de decisión con las carcasas de tu propia línea, del que lees las reglas y compruebas si coinciden con el criterio de calidad que descubriste en el M02-04. Después contestas con tu código dos preguntas que en planta siempre se hacen: **cuántos datos hacen falta** y **cuánto puede llegar a acertar** un modelo contra unas etiquetas imperfectas.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que entrenas con tu propia producción, cortada por tiempo.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m03_04_mi_modelo_linea.py`](../../infra/construye/m03_04_mi_modelo_linea.py). El paso 1 ya está escrito: lee el `dataset_linea.csv` del M02-04, lo ordena por hora y lo corta en un 70 % para entrenar y un 30 % para examinar. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_04_mi_modelo_linea.py
```

**Resultado esperado** (cambian los números):

```text
carcasas: entrenar=1588 examen=681 defectuosas_en_examen=97
```

**Cómo se lee:** tus carcasas, no unas generadas por el laboratorio: los números dependen de cuánto tiempo dejaste fabricar con calidad en marcha. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Entrenar un árbol y leer sus reglas

**Para qué:** ver qué ha aprendido el modelo de tu línea, en una forma que se puede discutir con calidad.

**Qué ocurre:** entrenas un árbol de decisión con `PROFUNDIDAD` preguntas como mucho y lo imprimes como texto: cada línea es una pregunta sobre una señal.

Pega debajo de `# --- PASO 2`:

```python
arbol = DecisionTreeClassifier(max_depth=PROFUNDIDAD, class_weight="balanced", random_state=7)
arbol.fit(entrenar[SENALES], entrenar["defecto"])
print(export_text(arbol, feature_names=SENALES, class_names=["buena", "defectuosa"]))
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas, recortadas; los cortes cambian un poco con tus datos):

```text
|--- corriente_a <= 4.09
|   |--- temperatura_c <= 62.84
|   |   |--- vibracion_mm_s <= 0.27
|   |   |   |--- class: buena
|   |   |--- vibracion_mm_s >  0.27
|   |   |   |--- class: buena
|   |--- temperatura_c >  62.84
|   |   |--- ...
|   |   |   |--- class: buena
|--- corriente_a >  4.09
|   |--- vibracion_mm_s <= 0.26
|   |   |--- ...
|   |   |   |--- class: buena
|   |--- vibracion_mm_s >  0.26
|   |   |--- temperatura_c <= 65.67
|   |   |   |--- class: defectuosa
|   |   |--- temperatura_c >  65.67
|   |   |   |--- class: defectuosa
```

**Cómo se lee:** la primera pregunta es la corriente (**4,09 A**) y la segunda, la vibración (**0,26 mm/s**): muy cerca de 4,08 y 0,265, el criterio oculto de calidad que descubriste con SQL en el M02-04. El árbol lo ha encontrado solo, a partir de los ejemplos. Las preguntas sobre la temperatura llevan a la misma respuesta por los dos lados: no aportan nada, porque en esta línea la temperatura no influye en el defecto.

### 3 — Examinar el modelo

**Para qué:** medir el árbol con las carcasas más recientes, que [no ha visto](../glosario/03-aprendizaje-automatico.md#particion).

**Qué ocurre:** le pides la decisión para cada carcasa de examen y cuentas defectos encontrados y falsas alarmas.

Pega debajo de `# --- PASO 3`:

```python
def examinar(modelo, datos=examen):
    tn, fp, fn, tp = confusion_matrix(datos["defecto"], modelo.predict(datos[SENALES]), labels=[0, 1]).ravel()
    return tp, fn, fp, tn

tp, fn, fp, tn = examinar(arbol)
print(f"encontrados={tp} de {tp + fn}  falsas_alarmas={fp} de {fp + tn}")
```

**Resultado esperado** (línea nueva; cambian los números):

```text
encontrados=82 de 97  falsas_alarmas=2 de 584
```

**Cómo se lee:** casi todas las defectuosas encontradas y pocas falsas alarmas: con datos de la propia línea, el modelo funciona mucho mejor que en el M03-01. No porque el algoritmo sea mejor, sino porque **aquí el defecto depende de las señales que se miden**.

### 4 — ¿Cuántos datos hacen falta?

**Para qué:** saber a partir de cuánta producción merece la pena entrenar.

**Qué ocurre:** entrenas el mismo árbol con solo las primeras 60, 120, 300 y 600 carcasas de entrenamiento, y lo examinas siempre con el mismo examen. Así ves cómo mejora con más datos.

Pega debajo de `# --- PASO 4`:

```python
print("carcasas_para_aprender  defectuosas_entre_ellas  encontrados  falsas_alarmas")
for n in (60, 120, 300, 600, len(entrenar)):
    parte = entrenar.iloc[:n]
    modelo = DecisionTreeClassifier(max_depth=PROFUNDIDAD, class_weight="balanced", random_state=7)
    modelo.fit(parte[SENALES], parte["defecto"])
    tp, fn, fp, tn = examinar(modelo)
    print(f"{n:22d}  {int(parte['defecto'].sum()):23d}  {tp:5d} de {tp + fn}  {fp:7d} de {fp + tn}")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
carcasas_para_aprender  defectuosas_entre_ellas  encontrados  falsas_alarmas
                    60                        8     83 de 97       61 de 584
                   120                       15     83 de 97       61 de 584
                   300                       33     82 de 97       31 de 584
                   600                       77     82 de 97        2 de 584
                  1588                      184     82 de 97        2 de 584
```

**Cómo se lee:** con pocas carcasas el árbol **ya encuentra los defectos**, pero con muchas falsas alarmas: 61 de 584 con 60 carcasas, 2 a partir de 600. Con pocos ejemplos aprende un criterio aproximado («corriente alta») y le falta afinar el segundo corte. Fíjate en la segunda columna: lo que manda **no es cuántas carcasas hay, sino cuántas defectuosas**. En planta se pregunta «¿cuántos defectos tenemos registrados?», no «¿cuántas piezas?».

### 5 — ¿Los fallos son del modelo o de la etiqueta?

**Para qué:** saber cuánto puede llegar a acertar un modelo contra unas etiquetas que tienen errores.

**Qué ocurre:** tomas las carcasas de examen en las que el árbol y calidad no coinciden y les aplicas el criterio real (vibración ≥ 0,265 y corriente > 4,08). Si el criterio da la razón al árbol, el que se equivocó fue la inspección.

Pega debajo de `# --- PASO 5`:

```python
pred = arbol.predict(examen[SENALES])
criterio = ((examen["vibracion_mm_s"] >= 0.265) & (examen["corriente_a"] > 4.08)).astype(int)
discrepan = pred != examen["defecto"]
razon_al_modelo = int((discrepan & (pred == criterio)).sum())
print(f"el árbol y calidad no coinciden en {int(discrepan.sum())} carcasas; en {razon_al_modelo} el criterio da la razón al árbol")
```

**Resultado esperado** (línea nueva; cambian los números):

```text
el árbol y calidad no coinciden en 17 carcasas; en 17 el criterio da la razón al árbol
```

**Cómo se lee:** **en las 17 discrepancias, el árbol tenía razón y la etiqueta estaba mal**: es el 3 % de error de la inspección. Los 15 defectos «escapados» y las 2 «falsas alarmas» del paso 3 son, en realidad, errores de calidad. La medida dice que el modelo falla, pero falla la inspección. Por eso no se puede esperar un 100 % contra etiquetas imperfectas.

### 6 — Decide tú: cuántas preguntas puede hacer el árbol

**Para qué:** ver qué pasa si el modelo es demasiado sencillo o demasiado complejo para el criterio real.

**Qué ocurre:** pruebas `PROFUNDIDAD = 1` y después `PROFUNDIDAD = 8`, y miras las reglas del paso 2 y el resultado del paso 3.

**Resultado esperado** (líneas que cambian):

```text
# PROFUNDIDAD = 1
|--- corriente_a <= 4.09
|   |--- class: buena
|--- corriente_a >  4.09
|   |--- class: defectuosa

encontrados=83 de 97  falsas_alarmas=104 de 584

# PROFUNDIDAD = 8 (el árbol ocupa más de 200 líneas)
encontrados=76 de 97  falsas_alarmas=18 de 584
```

**Cómo se lee:** con **una sola pregunta**, el árbol solo puede mirar una señal: no le cabe «corriente alta **y** vibración alta», y da 104 falsas alarmas. Con **ocho**, sus reglas se llenan de cortes como «temperatura entre 61,01 y 61,02» que solo explican casos sueltos del entrenamiento, incluidos los errores de la inspección: memoriza en lugar de aprender, el [sobreajuste](../glosario/03-aprendizaje-automatico.md#sobreajuste) del M04-04. Encuentra menos defectos y da más falsas alarmas que con tres, y ya no se puede enseñar a calidad. Tres preguntas bastan porque el criterio real tiene dos. Vuelve a dejar `PROFUNDIDAD = 3`.
## Reto

Los dos retos se hacen con tu script de «Constrúyelo tú», añadiendo un bloque al final.

### 1 — Entrenar con muy poca producción

**La situación:** alguien propone entrenar con los dos primeros minutos de producción, unas 120 carcasas, para tener el modelo cuanto antes. En el paso 4 viste que con 120 carcasas el árbol daba 61 falsas alarmas. ¿Es siempre así, o depende de qué dos minutos te toquen?

**Qué haces:** entrenas el árbol con tres ventanas distintas de 120 carcasas del tramo de entrenamiento (las primeras, unas del medio y unas del final) y lo examinas siempre con el mismo examen.

**Pistas:** `entrenar.iloc[inicio:inicio + 120]` toma 120 carcasas a partir de `inicio`; repite el bucle del paso 4 con `for inicio in (0, 700, 1400)`.

**Lo que buscas:** cuánto cambia el resultado según la ventana.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: tres ventanas distintas de 120 carcasas
for inicio in (0, 700, 1400):
    parte = entrenar.iloc[inicio:inicio + 120]
    modelo = DecisionTreeClassifier(max_depth=PROFUNDIDAD, class_weight="balanced", random_state=7)
    modelo.fit(parte[SENALES], parte["defecto"])
    tp, fn, fp, tn = examinar(modelo)
    print(f"carcasas {inicio}-{inicio + 119}: defectuosas={int(parte['defecto'].sum()):2d}  encontrados={tp} de {tp + fn}  falsas_alarmas={fp} de {fp + tn}")
```

```text
carcasas 0-119: defectuosas=15  encontrados=83 de 97  falsas_alarmas=61 de 584
carcasas 700-819: defectuosas=15  encontrados=80 de 97  falsas_alarmas=124 de 584
carcasas 1400-1519: defectuosas=14  encontrados=83 de 97  falsas_alarmas=80 de 584
```

Con el mismo número de carcasas y de defectuosas, las falsas alarmas van **de 61 a 124** según los dos minutos que te toquen. Con tan pocos ejemplos, el modelo depende de la casualidad. **La regla:** antes de fiarte de un modelo entrenado con poca producción, entrénalo con varias ventanas distintas; si el resultado cambia mucho, faltan datos. Por eso `m02-04` no construye el dataset por debajo de 200 carcasas.

</details>

### 2 — Mirar las carcasas en las que discrepan

**La situación:** en el paso 5 viste que, en las 17 carcasas en las que el árbol y calidad no coinciden, el criterio da la razón al árbol. Calidad quiere verlas antes de creérselo.

**Qué haces:** enseñas esas carcasas con sus señales, lo que dijo calidad, lo que dijo el árbol y lo que dice el criterio.

**Pistas:** `examen.assign(arbol=pred, criterio=criterio)` añade dos columnas; `[discrepan]` se queda con las filas en las que no coinciden.

**Lo que buscas:** una carcasa que calidad marcó como defectuosa y cuyas señales son claramente normales.

<details>
<summary>Ver solución</summary>

```python
# Reto 2: las carcasas en las que el árbol y calidad no coinciden
tabla = examen.assign(arbol=pred, criterio=criterio)[discrepan]
print(tabla[["pieza_id", "vibracion_mm_s", "corriente_a", "defecto", "arbol", "criterio"]].head(5).to_string(index=False))
```

```text
pieza_id  vibracion_mm_s  corriente_a  defecto  arbol  criterio
   P0536           0.235         3.99        1      0         0
   P0562           0.250         4.03        1      0         0
   P0563           0.265         4.12        0      1         1
   P0618           0.265         3.98        1      0         0
   P0635           0.220         4.00        1      0         0
```

La P0536, por ejemplo: vibración 0,235 y corriente 3,99, las dos por debajo de los cortes, y calidad la marcó como defectuosa. Todo indica un error de la inspección. **La regla:** cuando un modelo bueno discrepa de calidad, esa carcasa es la primera que hay que volver a revisar; a menudo quien se equivoca es la inspección, y corregir esas etiquetas mejora el siguiente entrenamiento.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: falta dataset_linea.csv` | No se hizo M02-04 | Haz M02-04 y repite |
| Ningún defecto en el examen (`de 0`) | Muy poca producción o una tanda sin defectos | Deja fabricar más, repite `m02-04` y luego `m03-04` |
| Resultados muy distintos cada vez | Pocos datos | Normal con pocos cientos de piezas; fíjate en la importancia, que es más estable |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/dataset_linea.csv` | no has hecho el M02-04 | arranca calidad, deja fabricar unos minutos y lanza `lab m02-04` |

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
