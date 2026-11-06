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

Ingeniería tiene **dos modelos candidatos** para poner en la línea: la [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) del M03-01 y un [árbol de decisión](../glosario/03-aprendizaje-automatico.md#arbol) sencillo. Hay que elegir uno, y la regla se acuerda **antes** de ver los resultados para que nadie la ajuste a su favor:

1. Gana el que encuentre más defectos.
2. Si empatan, el que dé menos [falsas alarmas](../glosario/03-aprendizaje-automatico.md#matriz-confusion).

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

## Investiga: leer las reglas del árbol

**Qué ocurre:** el árbol ganó. A diferencia de la regresión logística o de una red, un árbol **se puede leer**: son reglas del tipo «si… entonces…». El comando de ayuda `lab arbol` las enseña en texto.

```bash
docker compose --profile lab run --rm --no-deps lab arbol
```

📋 Ficha del comando [`arbol`](../comandos-lab.md#arbol).

**Resultado esperado:**

```text
reglas de modelo_defecto.joblib (class: 1 = defecto, 0 = buena):
|--- temperatura_c <= 65.490
|   |--- vibracion_mm_s <= 0.412
|   |   |--- presion_bar <= 5.735
|   |   |   |--- class: 1
|   |   |--- presion_bar >  5.735
|   |   |   |--- class: 0
|   |--- vibracion_mm_s >  0.412
|   |   |--- temperatura_c <= 60.080
|   |   |   |--- class: 1
|   |   |--- temperatura_c >  60.080
|   |   |   |--- class: 1
|--- temperatura_c >  65.490
|   |--- presion_bar <= 6.250
|   |   |--- class: 1
|   |--- presion_bar >  6.250
|   |   |--- class: 0

OK arbol: 6 hojas, profundidad 3
```

**Cómo se lee:** cada línea es una pregunta; cada `class` final, la decisión. Traducido a lenguaje de planta, el árbol ha aprendido tres reglas de defecto:

| Regla | En palabras |
|-------|-------------|
| Temperatura > 65,5 °C **y** presión ≤ 6,25 bar | Husillo caliente con presión normal o baja |
| Temperatura ≤ 65,5 °C **y** vibración > 0,41 mm/s | Vibra mucho, aunque la temperatura sea normal |
| Temperatura ≤ 65,5 °C, vibración normal **y** presión ≤ 5,7 bar | Presión baja |

Estas reglas se pueden **enseñar a calidad y a proceso** y discutir: «¿tiene sentido que la presión baja dé defecto?». Con una regresión logística o una red, esa conversación no es posible. Fíjate también en una rareza: bajo `vibracion_mm_s > 0.412`, las dos ramas dicen `class: 1`. Esa pregunta sobre la temperatura no sirve para nada: un árbol puede hacer preguntas inútiles.

## Experimenta: una red neuronal como tercer candidato

**Qué ocurre:** añades a la comparación un tercer candidato, una **red neuronal**: un modelo formado por capas de «neuronas» que combinan las [señales](../glosario/03-aprendizaje-automatico.md#senal) con unos pesos que se ajustan al entrenar. En el M04-04 la entrenarás paso a paso con fotos; aquí la usas como un candidato más, con el mismo corte y la misma regla.

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

## Constrúyelo tú: tu propia comparación de modelos

**Qué está pasando:** `lab m03-03` compara dos candidatos y elige uno con una regla que está dentro del comando. Ahora montas tú la comparación: **escribes la regla antes de mirar los resultados**, defines los candidatos, los examinas a todos con la misma vara y guardas el elegido con nombre y versión. Como la comparación es tuya, podrás añadir un candidato que el comando no tiene, uno de los «hermanos» del mapa de familias del glosario, y cambiar la regla para ver cómo cambia el ganador.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que todos los candidatos van a examinarse con las mismas piezas.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m03_03_mi_comparacion.py`](../../infra/construye/m03_03_mi_comparacion.py). El paso 1 ya está escrito: el corte por orden de fabricación del M03-01 y una función `examinar` que entrena un modelo y cuenta sus aciertos y errores. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_03_mi_comparacion.py
```

**Resultado esperado:**

```text
entrenar=537 examen=231 defectos_en_examen=21
```

**Cómo se lee:** las mismas 231 piezas de examen y los mismos 21 defectos del M03-01. Todo lo que compares a partir de aquí se mide con esta vara. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Escribir la regla antes de mirar

**Para qué:** que la elección no dependa de qué resultado te guste más una vez visto.

**Qué ocurre:** escribes la regla de elección como una función: gana el que encuentra más defectos; si empatan, el que da menos falsas alarmas. La imprimes para que quede escrita antes de ver ningún número.

Pega debajo de `# --- PASO 2`:

```python
REGLA = "más defectos encontrados; si empatan, menos falsas alarmas"

def clave(resultado):
    return (resultado["recall"], -resultado["fpr"])     # Python compara la tupla de izquierda a derecha

print(f"regla de elección: {REGLA}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
regla de elección: más defectos encontrados; si empatan, menos falsas alarmas
```

**Cómo se lee:** la regla queda fijada antes de entrenar nada. Si la escribieras después de ver los resultados, sería muy fácil elegir la que da la razón a tu favorito.

### 3 — Los candidatos

**Para qué:** decidir qué modelos compiten, con su configuración, antes de examinarlos.

**Qué ocurre:** defines los tres candidatos del lab en un diccionario: la regresión logística del M03-01, el árbol de decisión y la red neuronal de «Experimenta», esta con sus señales [escaladas](../glosario/03-aprendizaje-automatico.md#escalado).

Pega debajo de `# --- PASO 3`:

```python
candidatos = {
    "logreg": LogisticRegression(class_weight="balanced", max_iter=400),
    "arbol": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=7),
    "red": make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=0)),
}
print(f"candidatos: {list(candidatos)}")
```

**Resultado esperado** (líneas nuevas):

```text
candidatos: ['logreg', 'arbol', 'red']
```

**Cómo se lee:** tres familias distintas del mapa de familias: una suma ponderada, preguntas en cadena y capas de neuronas. `make_pipeline` pega el escalado delante de la red, para que nunca se entrene sin él.

### 4 — Examinarlos con la misma vara

**Para qué:** tener los resultados de todos en una sola tabla, comparables.

**Qué ocurre:** pasas cada candidato por `examinar` y enseñas sus defectos encontrados y sus falsas alarmas.

Pega debajo de `# --- PASO 4`:

```python
resultados = {nombre: examinar(modelo) for nombre, modelo in candidatos.items()}
print("candidato  encontrados  falsas_alarmas")
for nombre, r in resultados.items():
    print(f"{nombre:9s}  {r['encontrados']:5d} de 21  {r['falsas']:6d} de 210")
```

**Resultado esperado** (líneas nuevas):

```text
candidato  encontrados  falsas_alarmas
logreg        15 de 21      38 de 210
arbol         16 de 21       3 de 210
red           16 de 21       2 de 210
```

**Cómo se lee:** son los mismos números de `lab m03-03` y de `lab m03-red`: has reconstruido la comparación. La regresión logística queda muy por detrás; el árbol y la red empatan en defectos encontrados.

### 5 — Elegir con la regla y guardar

**Para qué:** que el elegido salga de la regla, no de una opinión, y quede rastreable.

**Qué ocurre:** aplicas `clave` para elegir el ganador, guardas el modelo en `mi_modelo.joblib` y, al lado, una ficha con su nombre, su versión, la regla y sus resultados.

Pega debajo de `# --- PASO 5`:

```python
ganador = max(resultados, key=lambda nombre: clave(resultados[nombre]))
joblib.dump(candidatos[ganador], "/data/mi_modelo.joblib")
ficha = {"modelo": ganador, "version": VERSION, "regla": REGLA, **resultados[ganador]}
with open("/data/mi_modelo.json", "w") as f:
    json.dump(ficha, f, indent=1)
print(f"elegido: {ganador} -> mi_modelo.joblib, ficha en mi_modelo.json")
```

**Resultado esperado** (líneas nuevas):

```text
elegido: red -> mi_modelo.joblib, ficha en mi_modelo.json
```

**Cómo se lee:** gana **la red**: empata con el árbol en defectos encontrados y da una falsa alarma menos, así que la segunda parte de la regla decide. Es la regla aplicada al pie de la letra; si te parece una mala elección, es la regla lo que hay que cambiar (reto 1). La ficha `mi_modelo.json` dice qué se eligió, con qué regla y con qué resultados: es lo que se despliega y se audita.

### 6 — Decide tú: un candidato que el comando no tiene

**Para qué:** ver dónde queda un hermano del mapa de familias que no usamos en el curso.

**Qué ocurre:** añades al diccionario `candidatos` del paso 3 un **bosque aleatorio**: muchos árboles que votan. Añade también su `import` arriba del fichero, junto a los demás:

```python
from sklearn.ensemble import RandomForestClassifier      # arriba, con los demás import

    "bosque": RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=0),   # dentro de candidatos
```

**Resultado esperado** (líneas que cambian):

```text
candidatos: ['logreg', 'arbol', 'red', 'bosque']
candidato  encontrados  falsas_alarmas
logreg        15 de 21      38 de 210
arbol         16 de 21       3 de 210
red           16 de 21       2 de 210
bosque        16 de 21       0 de 210
elegido: bosque -> mi_modelo.joblib, ficha en mi_modelo.json
```

**Cómo se lee:** el bosque encuentra los mismos 16 defectos y **no da ninguna falsa alarma**: por la regla, gana. Es el hermano del árbol que el mapa de familias recomienda cuando se busca el máximo acierto con datos de proceso. Pero son 200 árboles votando: ya no hay unas reglas que enseñar a calidad. Entre 3, 2 y 0 falsas alarmas de 210, ¿compensa perder la explicación? Eso no lo decide el código: lo decide la regla, y la regla la escribes tú (reto 1). Deja el bosque en la lista para el reto.
## Reto

### 1 — Una regla que pida poder explicarlo

**La situación:** con tu comparación de «Constrúyelo tú», la regla elige el bosque (0 falsas alarmas) o la red (2), por delante del árbol (3). Los tres encuentran los mismos 16 defectos de 21. Calidad pide que el modelo que vaya a la línea **se pueda explicar**: quiere leer sus reglas y discutirlas.

**Qué haces:** escribes una regla nueva en la que, a igualdad de defectos encontrados, gane el candidato que se puede explicar, y solo después cuenten las falsas alarmas. Añádela al final de tu script, con el bosque todavía en la lista de candidatos.

**Pistas:** un diccionario `EXPLICABLE = {"logreg": True, "arbol": True, "red": False, "bosque": False}`; una función que, dado el nombre de un candidato, devuelva la tupla `(recall, explicable, -fpr)`; `max(resultados, key=esa_funcion)` elige el ganador.

**Lo que buscas:** qué candidato elige la regla nueva, y cuánto cuesta esa elección en falsas alarmas.

<details>
<summary>Ver solución</summary>

```python
REGLA_2 = "más defectos encontrados; si empatan, el que se puede explicar; después, menos falsas alarmas"
EXPLICABLE = {"logreg": True, "arbol": True, "red": False, "bosque": False}

def clave_explicable(nombre):
    r = resultados[nombre]
    return (r["recall"], EXPLICABLE[nombre], -r["fpr"])

print(f"con la regla «{REGLA_2}»: elegido {max(resultados, key=clave_explicable)}")
```

```text
con la regla «más defectos encontrados; si empatan, el que se puede explicar; después, menos falsas alarmas»: elegido arbol
```

**Gana el árbol**, a cambio de 3 falsas alarmas en 210 piezas en vez de 0: unas 3 revisiones más cada 200 piezas. Es la elección que haría la mayoría de las plantas. **La regla:** el criterio de elección es una decisión de proceso, y tiene que incluir todo lo que importa (aquí, poder explicarlo), escrito antes de mirar. Si lo añades después de ver que no gana tu favorito, ya no es una regla. Quita el bosque y el bloque del reto cuando acabes.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `No such file … limpio.csv` | no está el CSV | lanza `m02-03` |
| `VERSION` vacío | el comando no terminó en `OK` | repite `m03-03` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/limpio.csv` | no tienes el [dataset](../glosario/01-datos-arquitectura.md#dataset) limpio | lanza `lab m03-01`, que lo genera |

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

El modelo elegido es un fichero con **nombre y versión**. Esa versión viajará en cada [dictamen](../glosario/05-operacion-gobierno.md#dictamen) (M07) y permitirá reconstruir decisiones (M08). Si mañana se entrena otro, será `defecto-0.2` y se podrá comparar con la misma regla.

### En una frase

> 🔑 El modelo que va a la línea se elige con una regla escrita de antemano, se mide igual que los demás y queda con nombre y versión.
