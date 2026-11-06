# Glosario 3 — Aprendizaje automático y visión

[← Hoja anterior](02-observabilidad.md) · [Índice del glosario](README.md) · [Siguiente hoja →](04-ia-generativa.md)

Cómo aprende un modelo de los datos, cómo se le examina y qué algoritmos hay. Lo usas en el M03 y el M04, y vuelve en el M06 y el M07.

La hoja tiene tres partes:

1. [**El mapa de familias**](#mapa): dónde encaja cada algoritmo y cuáles son sus hermanos.
2. [**Los algoritmos**](#algoritmos): qué es cada uno, cómo funciona por dentro con números reales del curso, y cómo se compara con los demás.
3. [**Los conceptos de evaluación**](#evaluacion): cómo se sabe si un modelo sirve.

---

<a id="mapa"></a>
## 1. El mapa de familias

✔ = lo usas en el curso · ○ = hermano que no usamos, para que sepas que existe y cuándo se elige.

```text
Aprendizaje automático
│
├── Supervisado ── aprende de ejemplos CON la respuesta (etiqueta)
│   │
│   ├── Clasificación ── ¿a qué clase pertenece? (defecto sí / no)
│   │   ├── ✔ Regresión logística ........ M03-01, M04-01
│   │   ├── ✔ Árbol de decisión .......... M03-03, M03-04
│   │   ├── ✔ Red neuronal (MLP) ......... M03-03, M04-04
│   │   ├── ○ Bosque aleatorio (muchos árboles que votan)
│   │   ├── ○ Gradient boosting (XGBoost, LightGBM: árboles que corrigen al anterior)
│   │   ├── ○ k vecinos más cercanos (k-NN)
│   │   └── ○ Máquinas de vectores soporte (SVM)
│   │
│   └── Regresión ── ¿qué valor tendrá? (temperatura dentro de 5 min)
│       ├── ✔ Regresión lineal (recta de tendencia) ... M06-03 (predict_linear)
│       └── ○ Árboles y redes de regresión
│
├── No supervisado ── aprende SIN respuesta: solo cómo son los datos
│   │
│   ├── Detección de anomalías ── ¿esto es normal?
│   │   ├── ✔ Distancia de Mahalanobis .......... M03-02
│   │   ├── ✔ Banda normal + pendiente .......... M06-03
│   │   ├── ○ Bosque de aislamiento (Isolation Forest): probado y descartado en M03-02
│   │   ├── ○ One-class SVM
│   │   └── ○ Autoencoder (red que aprende a reconstruir lo normal)
│   │
│   └── Agrupamiento ── ¿qué grupos hay? (○ k-means: familias de ciclos parecidos)
│
└── Aprendizaje profundo ── redes con muchas capas
    ├── ○ Redes convolucionales (CNN): visión industrial real
    └── ✔ Transformers: los modelos de lenguaje → hoja 4
```

**Lo primero que aclara el mapa:** la **regresión logística no es una regresión, es un clasificador**. Se llama así por la historia de la estadística: por dentro calcula un número (una regresión) y lo convierte en una probabilidad de clase.

---

<a id="algoritmos"></a>
## 2. Los algoritmos

<a id="comparacion-clasificadores"></a>
### Comparación de clasificadores

Con la misma vara: las mismas piezas de examen del M03-03 (21 defectuosas y 210 buenas).

| | Regresión logística | Árbol de decisión | Red neuronal (MLP) | ○ Bosque / boosting | ○ k-NN |
|--|--|--|--|--|--|
| **Cómo decide** | Suma ponderada de las señales → probabilidad | Preguntas «¿señal ≤ valor?» en cadena | Muchas sumas ponderadas en capas | Muchos árboles que votan o se corrigen | Mira las piezas pasadas más parecidas |
| **Qué forma de frontera** | Una sola recta (o plano) | Escalones: rectángulos | Cualquier forma | Escalones muy finos | Cualquier forma |
| **Se explica** | Sí: un peso por señal | **Sí: se lee como reglas** | No | A medias | Sí: «se parece a estas» |
| **Datos que necesita** | Pocos | Pocos | Muchos | Medios | Medios, y todos en memoria |
| **Hay que escalar las señales** | Conviene | No | **Sí, imprescindible** | No | Sí |
| **En el curso (M03-03)** | 15 de 21, 38 falsas alarmas | **16 de 21, 3 falsas alarmas** | 16 de 21, 2 falsas alarmas | — | — |
| **Cuándo se elige** | Primera prueba; si hay que justificar cada señal | Datos de proceso y hay que explicarlo a calidad | Imágenes, sonido, muchas entradas | Datos de proceso y se busca el máximo acierto | Pocos datos y casos muy parecidos |

**Cómo se lee:** en los datos de la línea, el defecto depende de **combinaciones con corte** («temperatura alta **y** presión baja»). Una recta no sabe dibujar eso; un árbol sí. Por eso el árbol gana a la regresión logística, y empata con la red siendo mucho más sencillo y explicable.

<a id="regresion-logistica"></a>
### Regresión logística

**Qué es:** un clasificador que da a cada señal un **peso**, suma `peso × señal` y convierte la suma en una **probabilidad** entre 0 y 1.

**Cómo funciona por dentro**, con el modelo real del M03-01 (`modelo.coef_` y `modelo.intercept_`):

| Señal | Peso |
|-------|------|
| `temperatura_c` | +0,619 |
| `vibracion_mm_s` | +2,280 |
| `corriente_a` | +0,281 |
| `presion_bar` | −1,420 |
| término independiente | −32,681 |

Para la pieza H0562 (67,45 °C, 0,264 mm/s, 3,69 A, 5,86 bar):

```text
puntuación = 0,619 × 67,45 + 2,280 × 0,264 + 0,281 × 3,69 − 1,420 × 5,86 − 32,681
           = 41,75 + 0,60 + 1,04 − 8,32 − 32,68
           = 2,39

probabilidad = 1 / (1 + e^(−2,39)) = 0,92   → por encima de 0,5: «defecto»  (y lo era)
```

La función `1 / (1 + e^(−x))` es la **curva en S** (sigmoide): convierte cualquier puntuación en un número entre 0 y 1. Puntuación 0 → 0,5; muy positiva → cerca de 1; muy negativa → cerca de 0. Para H0558, una pieza buena de 57,23 °C, la puntuación es −3,89 y la probabilidad, 0,02.

**Cómo se leen los pesos:** el **signo** dice hacia dónde empuja la señal (presión más alta → menos probable el defecto). El **tamaño** no se puede comparar entre señales, porque cada una tiene sus unidades: un grado de temperatura no es lo mismo que un mm/s de vibración. Multiplicado por lo que varía cada señal en la línea, la temperatura pesa 1,46, la presión 0,17, la vibración 0,15 y la corriente 0,04. Casi todo lo que sabe el modelo está en la temperatura, que es lo que descubres en «Constrúyelo tú» del M03-01.

**Qué es entrenar:** buscar los cinco números que hacen que las probabilidades se parezcan lo más posible a lo que marcó calidad en las piezas de entrenamiento. El algoritmo empieza con pesos cualquiera y los corrige poco a poco (`max_iter=400` es el máximo de vueltas).

**Dónde se rompe:** solo traza **una frontera recta**. Si el defecto depende de un «y» con cortes, se queda corto.

**Lo usas en:** <!--usos:regresion-logistica-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-03](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [M04](../M04-vision-control-calidad/README.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md) · [M06-01](../M06-edge-integracion-ot/M06-01-inferencia-edge.md)<!--/usos-->

Relacionado: [umbral](#umbral) · [comparación de clasificadores](#comparacion-clasificadores)

<a id="arbol"></a>
### Árbol de decisión

**Qué es:** un clasificador que hace **preguntas en cadena** sobre las señales, del tipo «¿temperatura ≤ 65,49?», hasta llegar a una hoja que dice «defecto» o «buena».

**Cómo funciona por dentro:** en cada nodo, el algoritmo prueba todas las señales y todos los cortes posibles, y elige el que **mejor separa** las defectuosas de las buenas. Repite en cada rama hasta la profundidad máxima (`max_depth=3` en el curso: tres preguntas como mucho). El árbol real del M03-03 empieza así:

```text
|--- temperatura_c <= 65.490
|   |--- vibracion_mm_s <= 0.412
|   |   |--- presion_bar <= 5.735  → defecto
|   |   |--- presion_bar >  5.735  → buena
...
```

**Por qué importa en planta:** las reglas **se pueden enseñar a calidad y discutir**. No necesita escalar las señales, porque compara cada una por separado con su propio corte.

**Dónde se rompe:** un árbol muy profundo **memoriza** el entrenamiento ([sobreajuste](#sobreajuste)). Los hermanos ○ bosque aleatorio y ○ boosting lo resuelven combinando muchos árboles, a cambio de perder la lectura directa.

**Lo usas en:** <!--usos:arbol-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-03](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md)<!--/usos-->

<a id="red-neuronal"></a>
### Red neuronal (MLP)

**Qué es:** una cadena de **capas de neuronas**. Cada neurona hace lo mismo que una regresión logística en pequeño: multiplica sus entradas por unos pesos, las suma y aplica una función. Su salida es la entrada de la capa siguiente. MLP (*multilayer perceptron*) es la red más sencilla: todas las neuronas de una capa conectadas con todas las de la siguiente.

**Cómo funciona por dentro:**

```text
 4 señales  ──▶  capa de 64 neuronas  ──▶  capa de 32 neuronas  ──▶  probabilidad de defecto
 (M03-03)
 256 píxeles ──▶ capa de N neuronas  ──▶  buena / defectuosa
 (M04-04)
```

Con muchas neuronas puede dibujar **fronteras de cualquier forma**. Entrenar es repetir: pasar los ejemplos, medir cuánto se equivoca (la **pérdida**) y corregir un poco todos los pesos. Cada vuelta es una **iteración**.

**Dónde se rompe:**

- **Sin escalar las señales no aprende:** en el M03-03, sin escalar, encuentra 0 defectos de 21. La temperatura (62) aplasta a la vibración (0,25).
- **Con pocos datos memoriza:** en el M04-04, con el 10 % de las fotos acierta el 100 % del entrenamiento y el 50 % del examen.
- **No se explica:** miles de pesos que no se leen.

**Lo usas en:** <!--usos:red-neuronal-->[M04](../M04-vision-control-calidad/README.md)<!--/usos-->

Relacionado: [escalado](#escalado) · [sobreajuste](#sobreajuste) · ○ CNN en el [mapa](#mapa)

<a id="mahalanobis"></a>
### Distancia de Mahalanobis

**Qué es:** una forma de medir **cuánto se aleja una pieza de lo normal** mirando todas las señales a la vez, teniendo en cuenta cuánto varía cada una y cómo se mueven juntas.

**Cómo funciona por dentro:** aprende de piezas normales la media de cada señal, cuánto varía y qué señales suben y bajan juntas. Una pieza con mucha vibración y mucha corriente puede ser normal si siempre van juntas; mucha vibración con **poca** corriente es rara aunque cada valor por separado esté en su rango. El resultado es un número: la distancia.

**El umbral:** con cuatro señales, una pieza normal supera la distancia **13,3** solo 1 de cada 100 veces (percentil 99 de una chi-cuadrado con 4 grados de libertad). Ese es el umbral por defecto del M03-02.

**Hermanos:** el ○ bosque de aislamiento se probó al preparar el M03-02 y se descartó: agrupaba el valor extremo con el borde del histórico y no avisaba.

**Lo usas en:** <!--usos:mahalanobis-->[M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md)<!--/usos-->

Relacionado: [anomalía](#anomalia) · [umbral](#umbral)

<a id="banda-normal"></a>
### Banda normal y pendiente

**Qué es:** el detector más sencillo: aprende de un periodo sano **hasta dónde llega** una señal (percentil 99,5) y **qué subida es normal**. Avisa cuando la señal pasa de la banda **y** sube más de lo normal.

**En la línea:** el M06-03 lo aprende de 10 min de temperatura de Prometheus: límite 63,24 °C y subida máxima 0,37 °C/min. Con eso prevé cuánto falta para los 70 °C y propone subir la refrigeración.

**Dónde se rompe:** si el periodo «sano» contenía el fallo, el límite sale en 72,9 °C y ya no avisa de nada (Reto 2 del M06-03).

**Lo usas en:** <!--usos:banda-normal-->[M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md)<!--/usos-->

<a id="vision-pixeles"></a>
### Visión: una imagen son números

**Qué es:** para un modelo, una foto es una **tabla de números**, el brillo de cada punto. En el M04, una foto reducida a 16×16 son 256 números, y una regresión logística tiene un peso por píxel.

**Familia:**

| Método | Cómo decide | En el curso |
|--------|-------------|-------------|
| ✔ Regla de brillo | La fila más clara es el rayón | M04-02 |
| ✔ Clasificador sobre píxeles | Un peso por píxel | M04-01: 88 % de acierto |
| ✔ Red neuronal | Capas sobre los píxeles | M04-04 |
| ○ Red convolucional (CNN) | Aprende formas (bordes, líneas) que se repiten en cualquier zona | Visión industrial real, con GPU |
| ○ Detección de objetos (YOLO…) | Dice qué hay **y dónde**, con un recuadro | Localizar defectos en fotos grandes |

**Lo usas en:** <!--usos:vision-pixeles-->[M04](../M04-vision-control-calidad/README.md) · [M04-01](../M04-vision-control-calidad/M04-01-clasificacion-componentes.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md)<!--/usos-->

---

<a id="evaluacion"></a>
## 3. Los conceptos de evaluación

<a id="modelo"></a>
### Modelo y entrenamiento

**Qué es:** un **modelo** es una función aprendida de ejemplos: recibe las señales de una pieza y devuelve una respuesta. **Entrenar** es ajustar sus números internos para que se equivoque lo menos posible con los ejemplos. Lo que se guarda en disco (`.joblib`) son esos números.

**Lo usas en:** <!--usos:modelo-->[M03](../M03-ml-prediccion-anomalias/README.md)<!--/usos-->

<a id="etiqueta"></a>
### Etiqueta

**Qué es:** la respuesta correcta de cada ejemplo, la que el modelo tiene que aprender a predecir. En la línea, la columna `defecto`: 1 si calidad marcó la pieza como mala.

**Dónde se rompe:** si la etiqueta tiene errores, el modelo los aprende. Calidad se equivoca en un 3 % de las inspecciones (M02-04).

**Lo usas en:** <!--usos:etiqueta-->[M02](../M02-captura-integracion-datos/README.md) · [M02-04](../M02-captura-integracion-datos/M02-04-dataset-linea.md) · [M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md)<!--/usos-->

<a id="senal"></a>
### Señal (característica)

**Qué es:** cada columna de entrada del modelo. En inglés, *feature*. En la línea: temperatura, vibración, corriente y presión.

**Dónde se rompe:** más señales no es mejor modelo. En el M03-01, solo con la temperatura el modelo cuesta menos que con las cuatro.

**Lo usas en:** <!--usos:senal-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md) · [M03-03](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md)<!--/usos-->

<a id="particion"></a>
### Entrenamiento y examen (partición temporal)

**Qué es:** se separan los datos en dos: con unos **aprende** y con otros se le **examina**. En planta, se corta **por tiempo**: aprende con el pasado (70 % más antiguo) y se examina con el futuro (30 % más reciente), como pasará en la línea.

**Dónde se rompe:** si se parte al azar, el modelo aprende con piezas posteriores a las que examina, y el examen sale mejor de lo que será la realidad.

**Lo usas en:** <!--usos:particion-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M04](../M04-vision-control-calidad/README.md) · [M04-01](../M04-vision-control-calidad/M04-01-clasificacion-componentes.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md)<!--/usos-->

<a id="fuga"></a>
### Fuga de información

**Qué es:** dar al modelo, como entrada, algo que en la realidad **no tendrá a tiempo**. El ejemplo extremo es meter la columna `defecto` como señal: el acierto es perfecto porque el modelo lee la respuesta.

**Lo usas en:** <!--usos:fuga-->[M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md)<!--/usos-->

<a id="matriz-confusion"></a>
### Matriz de confusión, recall y falsas alarmas

**Qué es:** la tabla de los cuatro casos posibles al examinar un clasificador.

| | Dijo «defecto» | Dijo «buena» |
|--|----------------|--------------|
| **Era defectuosa** | `tp`: encontrado | `fn`: **se escapa** |
| **Era buena** | `fp`: **falsa alarma** | `tn`: correcta |

- **Recall** = encontrados ÷ defectuosas reales. En el M03-01, 15 / 21 = 0,71.
- **Tasa de falsas alarmas** (`fpr`) = falsas alarmas ÷ buenas reales. En el M03-01, 38 / 210 = 0,18.
- **Acierto global** = (tp + tn) ÷ total. Engaña cuando el defecto es raro: un modelo que siempre dice «buena» acierta el 91 %.

**Lo usas en:** <!--usos:matriz-confusion-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md) · [M03-03](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md) · [M04-02](../M04-vision-control-calidad/M04-02-deteccion-defectos.md)<!--/usos-->

<a id="umbral"></a>
### Umbral de decisión

**Qué es:** el corte que convierte la probabilidad del modelo en una decisión. Por defecto, 0,5. **No es parte del modelo:** el modelo da probabilidades y el umbral se aplica después; se puede cambiar sin reentrenar.

**Cómo se elige:** por lo que cuesta cada error. Con 500 € por defecto escapado y 5 € por revisión, el mejor umbral del M03-01 es 0,05; con 50 € por revisión, 0,7.

**Lo usas en:** <!--usos:umbral-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md) · [M04](../M04-vision-control-calidad/README.md) · [M04-02](../M04-vision-control-calidad/M04-02-deteccion-defectos.md) · [M04-03](../M04-vision-control-calidad/M04-03-inspeccion-camara.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M07-02](../M07-mlops-observabilidad/M07-02-monitorizacion.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md)<!--/usos-->

Relacionado: [zona de duda](#zona-duda) · [matriz de confusión](#matriz-confusion)

<a id="desequilibrio"></a>
### Clases desequilibradas

**Qué es:** cuando una clase es mucho más rara que la otra; en planta, casi siempre el defecto. El modelo aprende que decir siempre «buena» compensa.

**Cómo se corrige:** dar más peso a la clase rara al entrenar (`class_weight="balanced"`). En el M03-01, sin equilibrar, se escapan 9 defectos en vez de 6.

**Lo usas en:** <!--usos:desequilibrio-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md)<!--/usos-->

<a id="escalado"></a>
### Escalado de las señales

**Qué es:** poner todas las señales en tamaños parecidos (por ejemplo, restar la media y dividir por lo que varían) antes de entrenar.

**Quién lo necesita:** las redes neuronales, k-NN y las distancias como Mahalanobis, sí. Los árboles, no.

**Lo usas en:** <!--usos:escalado-->[M03](../M03-ml-prediccion-anomalias/README.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md)<!--/usos-->

<a id="sobreajuste"></a>
### Sobreajuste

**Qué es:** cuando el modelo **memoriza** los ejemplos de entrenamiento en vez de aprender el patrón. Acierta mucho en entrenamiento y poco en examen.

**Cómo se detecta:** comparando el acierto en entrenamiento con el de examen. En el M04-04, con el 10 % de las fotos: 100 % frente a 50 %.

**Lo usas en:** <!--usos:sobreajuste-->[M04](../M04-vision-control-calidad/README.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md)<!--/usos-->

<a id="anomalia"></a>
### Anomalía

**Qué es:** un comportamiento que **no se parece a lo normal**, aunque nadie lo haya etiquetado como defecto. Se detecta aprendiendo cómo es lo normal, no cómo es el fallo.

**Por qué importa:** los fallos nuevos (un rodamiento que empieza a fallar) no tienen ejemplos etiquetados.

**Lo usas en:** <!--usos:anomalia-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M03](../M03-ml-prediccion-anomalias/README.md) · [M03-02](../M03-ml-prediccion-anomalias/M03-02-anomalias.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md)<!--/usos-->

<a id="zona-duda"></a>
### Zona de duda

**Qué es:** un intervalo alrededor del umbral en el que el modelo **no decide**: la pieza va a una persona. El modelo resuelve lo evidente y la persona, lo dudoso.

**En la línea:** en el M04-03, las piezas a menos de 0,1 del umbral van a revisión. El tamaño se ajusta a cuántas piezas puede revisar el turno.

**Lo usas en:** <!--usos:zona-duda-->[M04](../M04-vision-control-calidad/README.md) · [M04-03](../M04-vision-control-calidad/M04-03-inspeccion-camara.md)<!--/usos-->
