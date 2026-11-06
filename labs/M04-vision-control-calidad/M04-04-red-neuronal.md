# M04-04 — Entrenar una red neuronal

[← Página anterior](M04-03-inspeccion-camara.md) · [Siguiente página →](../M05-ia-generativa/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **entrenar una red neuronal**: cómo aprende ajustándose iteración a iteración, cómo se sabe si ha aprendido, qué es el [sobreajuste](../glosario/03-aprendizaje-automatico.md#sobreajuste) y cómo se detecta, y cuándo una red mejora a un modelo sencillo.

### Prerrequisitos

- Las fotos de M04-01 (si no están, el comando las genera).
- Solo `lab`. CPU, sin GPU: cada entrenamiento tarda menos de un segundo.

### Qué está pasando

En el M04-01, una [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) separaba carcasas buenas de defectuosas con un **88 %** de acierto. Ahora vas a entrenar una **red neuronal** con las mismas fotos y a ver si lo mejora.

Una red neuronal es una cadena de capas de «neuronas». Cada neurona recibe números, los multiplica por unos **pesos**, los suma y pasa el resultado a la capa siguiente:

```
 foto 16×16         capa oculta            salida
 256 números  ──▶   N neuronas    ──▶   buena / defectuosa
 (el brillo         (cada una mira       (la probabilidad
  de cada punto)     una combinación      de cada clase)
                     de píxeles)
```

Al principio los pesos son aleatorios y la red acierta como una moneda al aire. **Entrenar** es repetir muchas veces: pasar las fotos de entrenamiento, medir cuánto se equivoca (la **pérdida**) y corregir un poco los pesos para equivocarse menos. Cada vuelta es una **iteración**.

Tres cosas deciden si sale bien:

| Parámetro | Qué es | En el comando |
|-----------|--------|---------------|
| Neuronas | Cuántas combinaciones de [píxeles](../glosario/03-aprendizaje-automatico.md#vision-pixeles) puede aprender | Primer número (por defecto 64) |
| Iteraciones | Cuántas veces como máximo repasa las fotos | Segundo número (por defecto 1000) |
| Fotos | Con cuántos ejemplos aprende | Tercer número: fracción de las fotos de entrenamiento (por defecto 1 = todas) |

Es el mismo tipo de red que reconoce dígitos escritos a mano (una red de una capa oculta), en pequeño.

### 1 — Entrenar la red

**Qué ocurre:** entrenas una red con 64 neuronas usando las 56 fotos de entrenamiento y la examinas con las 24 que [no ha visto](../glosario/03-aprendizaje-automatico.md#particion). El comando enseña cómo baja la pérdida durante el entrenamiento.

```bash
# Red de 64 neuronas, hasta 1000 iteraciones, con todas las fotos
docker compose --profile lab run --rm --no-deps lab m04-red
```

📋 Ficha del comando [`m04-red`](../comandos-lab.md#m04-red): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
red: 256 entradas -> 64 neuronas -> 2 salidas; 56 fotos de entrenamiento, 24 de examen
pérdida (más baja = se equivoca menos con las fotos de entrenamiento):
  iteración    1: 0.701
  ...
  iteración  705: 0.020
acierto en entrenamiento=1.00  en examen=1.00  (regresión logística en examen=0.88)
tiempo de entrenamiento: 0.22 s en CPU
OK m04-red: neuronas=64 iteraciones=705 examen=1.00
```

**Cómo se lee:**

- La **pérdida** empieza en 0,70 (lo que vale acertar al azar entre dos clases) y baja hasta 0,02: la red ha ido corrigiendo sus pesos.
- Se ha parado en la **iteración 705**, antes del máximo de 1000, porque ya no mejoraba: ha **convergido**.
- Acierta las **24 fotos de examen**, frente al 88 % de la regresión logística.
- Ha tardado menos de medio segundo en CPU: con fotos tan pequeñas no hace falta GPU.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m04_red</code>)</summary>

```python
X = np.stack([_features_imagen(r) for r in entreno["ruta"]])   # cada foto → 256 números

# Red: 256 entradas → «neuronas» en la capa oculta → 2 salidas
red = MLPClassifier(hidden_layer_sizes=(neuronas,), max_iter=iteraciones, random_state=0)
red.fit(X, y)                       # entrenar: ajustar los pesos iteración a iteración
curva = red.loss_curve_             # la pérdida en cada iteración

ent = red.score(X, y)               # acierto con las fotos de entrenamiento
exa = red.score(Xp, yp)             # acierto con las fotos de examen (no vistas)
```

</details>

### 2 — Entrenar poco

**Qué ocurre:** repites el entrenamiento con solo **20 iteraciones**.

**Predice:** ¿qué acierto tendrá?

```bash
docker compose --profile lab run --rm --no-deps lab m04-red 64 20
```

**Resultado esperado:**

```text
  iteración    1: 0.701
  iteración   20: 0.687
acierto en entrenamiento=0.57  en examen=0.50  (regresión logística en examen=0.88)
aviso: la red ha agotado las iteraciones sin terminar de aprender (no ha convergido)
```

**Cómo se lee:** la pérdida casi no se ha movido (0,70 → 0,69) y acierta el 50 % en examen: **no ha aprendido nada**, decide como una moneda. La red no se ha equivocado: no le has dado tiempo. Prueba con 200 iteraciones (`lab m04-red 64 200`): ya acierta el examen, pero sale el aviso de que no ha convergido y en entrenamiento se queda en 0,95.

### 3 — Cambiar el tamaño de la red

**Qué ocurre:** entrenas una red muy pequeña (8 neuronas) y una grande (256).

```bash
docker compose --profile lab run --rm --no-deps lab m04-red 8
docker compose --profile lab run --rm --no-deps lab m04-red 256
```

**Resultado esperado:** las dos aciertan las 24 fotos de examen (1,00). La de 8 neuronas tarda unos 0,2 s; la de 256, unos 1,4 s.

**Cómo se lee:** para un defecto tan claro como un rayón blanco, unas pocas neuronas bastan. Una red más grande no es mejor si el problema no lo necesita: solo cuesta más entrenarla y ejecutarla, algo que importa cuando corre en un equipo [edge](../glosario/01-datos-arquitectura.md#edge) junto a la máquina (M06).

## Comprueba tu entendimiento

**Qué dice la pérdida**

Una red termina con pérdida 0,69 y otra con 0,02. ¿Cuál ha aprendido?

→ La de 0,02. Una pérdida en torno a 0,69, con dos clases, es lo mismo que decidir al azar.

## Experimenta: el sobreajuste

**Qué ocurre:** vas a entrenar la red con **muy pocas fotos**: el 10 %, es decir, 3 buenas y 3 malas. Las de examen siguen siendo las mismas 24.

**Predice:** ¿cómo serán el acierto en entrenamiento y en examen?

```bash
# 64 neuronas, 1000 iteraciones, solo el 10 % de las fotos de entrenamiento
docker compose --profile lab run --rm --no-deps lab m04-red 64 1000 0.1
```

**Resultado esperado:**

```text
red: 256 entradas -> 64 neuronas -> 2 salidas; 6 fotos de entrenamiento, 24 de examen
...
acierto en entrenamiento=1.00  en examen=0.50  (regresión logística en examen=0.50)
```

**Cómo se lee:** la red acierta **todas** las fotos con las que ha entrenado y **la mitad** de las nuevas. No ha aprendido a reconocer un rayón: ha **memorizado** esas seis fotos. Eso es el **sobreajuste**, y solo se descubre examinando con datos que el modelo no ha visto.

Prueba también con el 50 % (`lab m04-red 64 1000 0.5`): el examen sube a 0,79. Más ejemplos, mejor generaliza.

## Constrúyelo tú: tu propia red, vuelta a vuelta

**Qué está pasando:** `lab m04-red` entrena la red de una vez y enseña la pérdida al final. Ahora la entrenas tú **vuelta a vuelta**: después de cada pasada por las fotos miras cuánto se equivoca y cuánto acierta, con las de entrenamiento y con las de examen. Así ves aprender a la red y ves el momento exacto en que empieza a memorizar.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que la red va a ver las mismas fotos que el modelo del M04-01.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m04_04_mi_red.py`](../../infra/construye/m04_04_mi_red.py). Arriba están las **decisiones** (`NEURONAS`, `VUELTAS`, `PARTE`); debajo, el paso 1 ya escrito: las 80 fotos convertidas en números como en el M04-01, y el mismo corte de 56 para aprender y 24 de examen. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_04_mi_red.py
```

**Resultado esperado:**

```text
fotos para aprender=56  fotos de examen=24  números por foto=256
```

**Cómo se lee:** las mismas fotos y el mismo examen que la regresión logística del M04-01, que acertaba el 88 %: así la comparación es justa. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Crear la red y darle una sola vuelta

**Para qué:** ver cómo es la red antes de aprender, y qué cambia con una sola pasada.

**Qué ocurre:** creas una red con `NEURONAS` en su capa oculta y le das **una sola** pasada por las fotos de entrenamiento con `partial_fit`. Enseñas cuántos pesos tiene, su pérdida y su acierto.

Pega debajo de `# --- PASO 2`:

```python
red = MLPClassifier(hidden_layer_sizes=(NEURONAS,), random_state=0)
red.partial_fit(X[ent], y[ent], classes=[0, 1])                   # una sola pasada por las fotos

def acierto(filas):
    return (red.predict(X[filas]) == y[filas]).mean()

pesos = sum(c.size for c in red.coefs_) + sum(b.size for b in red.intercepts_)
print(f"pesos de la red: {pesos}")
print(f"tras 1 vuelta: pérdida={red.loss_:.3f}  acierto entrenamiento={acierto(ent):.2f}  examen={acierto(exa):.2f}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
pesos de la red: 16513
tras 1 vuelta: pérdida=0.701  acierto entrenamiento=0.50  examen=0.50
```

**Cómo se lee:** **16 513 pesos**, frente a los 257 de la regresión logística: 256 entradas × 64 neuronas, más 64 conexiones a la salida, más un término por neurona. Empiezan con valores al azar, y tras una vuelta la red acierta como una moneda: 0,50. La **pérdida** mide cuánto se equivoca: es lo que el entrenamiento intenta bajar.

### 3 — Entrenar vuelta a vuelta

**Para qué:** ver aprender a la red: cómo baja la pérdida y sube el acierto en cada pasada.

**Qué ocurre:** repites `partial_fit` hasta `VUELTAS`, y diez veces a lo largo del entrenamiento enseñas la pérdida y el acierto en entrenamiento y en examen.

Pega debajo de `# --- PASO 3`:

```python
print("vuelta  pérdida  acierto_entrenamiento  acierto_examen")
for vuelta in range(2, VUELTAS + 1):
    red.partial_fit(X[ent], y[ent])                                # una pasada más
    if vuelta % (VUELTAS // 10) == 0:                              # diez filas, sean cuantas sean las vueltas
        print(f"{vuelta:6d}  {red.loss_:7.3f}  {acierto(ent):21.2f}  {acierto(exa):14.2f}")
```

**Resultado esperado** (líneas nuevas):

```text
vuelta  pérdida  acierto_entrenamiento  acierto_examen
    30    0.680                   0.75            0.58
    60    0.654                   0.86            0.88
    90    0.615                   0.86            0.88
   120    0.557                   0.91            0.96
   150    0.480                   0.93            0.96
   180    0.403                   0.93            1.00
   210    0.336                   1.00            1.00
   240    0.279                   1.00            1.00
   270    0.233                   1.00            1.00
   300    0.194                   1.00            1.00
```

**Cómo se lee:** la pérdida baja vuelta a vuelta y **los dos aciertos suben juntos**: la red aprende algo que también vale para fotos que no ha visto. Hacia la vuelta 60 iguala a la regresión logística (0,88) y hacia la 180 acierta las 24 fotos de examen. Las primeras decenas de vueltas parece que no aprende nada: es normal, los pesos tienen que alejarse de su valor al azar.

### 4 — Decide tú: pocas fotos

**Para qué:** ver el momento en que la red deja de aprender y empieza a memorizar.

**Qué ocurre:** cambias `PARTE = 1.0` por `PARTE = 0.1`: la red aprende con solo 3 fotos de cada clase. Ejecuta.

**Resultado esperado** (líneas del paso 3):

```text
vuelta  pérdida  acierto_entrenamiento  acierto_examen
    30    0.638                   1.00            0.50
    60    0.564                   1.00            0.50
    ...
   270    0.055                   1.00            0.50
   300    0.037                   1.00            0.50
```

**Cómo se lee:** el acierto en entrenamiento llega a 1,00 en 30 vueltas y **el de examen no se mueve de 0,50**. La pérdida baja mucho más que con todas las fotos (0,037 frente a 0,194): la red tiene 16 513 pesos para 6 fotos y le basta con memorizarlas. Las dos columnas separadas son el sobreajuste: una pérdida muy baja no es buena señal si el examen no acompaña. Vuelve a dejar `PARTE = 1.0`.

### 5 — Decide tú: el tamaño de la red

**Para qué:** saber si una red más grande es mejor.

**Qué ocurre:** con todas las fotos, pruebas `NEURONAS = 4` y después `NEURONAS = 256`.

**Resultado esperado** (la línea de pesos y la última vuelta):

```text
# NEURONAS = 4
pesos de la red: 1033
   300    0.692                   0.48            0.54
# NEURONAS = 256
pesos de la red: 66049
   300    0.137                   1.00            1.00
```

**Cómo se lee:** con **4 neuronas** la red no aprende en 300 vueltas: la pérdida apenas se mueve de 0,69, el valor de quien no sabe nada. Con tan pocas neuronas, el entrenamiento se queda atascado. Con **256**, aprende lo mismo que con 64, con cuatro veces más pesos. Una red tiene que tener capacidad suficiente, pero más allá de eso solo añade memoria y cálculo: en un equipo edge, cada peso de más cuenta (M06-01). Vuelve a dejar `NEURONAS = 64`.
## Reto

Los dos retos se hacen con tu red de «Constrúyelo tú», añadiendo un bloque al final.

### 1 — ¿Te fías del 100 %?

**La situación:** tu red acierta las 24 fotos de examen. Alguien propone ponerla mañana en el puesto. Pero las fotos de la línea no serán idénticas a las del laboratorio: la luz cambia y la carcasa no siempre cae en el mismo sitio de la bandeja.

**Qué haces:** examinas la red con las mismas fotos de examen cambiadas de dos formas: con un poco más de luz (+0,15) y con la carcasa movida 2 puntos a la derecha.

**Pistas:** `np.clip(X + 0.15, 0, 1)` aclara todas las fotos; `np.roll(foto.reshape(16, 16), 2, axis=1)` desplaza una foto 2 puntos en horizontal; después, `.reshape(-1)` la vuelve a poner en una fila.

**Lo que buscas:** cuánto acierta la red en cada caso.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: las mismas fotos de examen, con otras condiciones
def acierto_con(X_cambiadas):
    return (red.predict(X_cambiadas[exa]) == y[exa]).mean()

print(f"examen normal:            {acierto_con(X):.2f}")
print(f"con +0,15 de luz:         {acierto_con(np.clip(X + 0.15, 0, 1)):.2f}")
desplazadas = np.stack([np.roll(f.reshape(16, 16), 2, axis=1).reshape(-1) for f in X])   # carcasa 2 puntos a la derecha
print(f"carcasa movida 2 puntos:  {acierto_con(desplazadas):.2f}")
```

```text
examen normal:            1.00
con +0,15 de luz:         0.83
carcasa movida 2 puntos:  1.00
```

Con la carcasa movida sigue acertando, porque el rayón es una línea horizontal y moverla de lado no la cambia. Pero **con algo más de luz baja al 83 %**: la red nunca vio fotos con esa luz. El 100 % del examen solo vale para fotos como las del examen. **La regla:** antes de llevar un modelo de visión a la línea, se examina con fotos de la línea, en todas las condiciones que se van a dar (luz, posición, polvo, reflejos), y se fija la iluminación del puesto para que no cambie.

</details>

### 2 — Lo que cuesta la red

**La situación:** la red acierta más que la regresión logística del M04-01 (1,00 frente a 0,88). Antes de elegirla, el equipo de [OT](../glosario/01-datos-arquitectura.md#ot) pregunta cuánto ocupa y cuánto tarda en decidir cada carcasa, porque va a correr en un equipo edge junto a la estación.

**Qué haces:** entrenas al final de tu script una regresión logística con las mismas fotos y comparas los dos modelos: acierto, número de pesos y milisegundos por foto.

**Pistas:** `LogisticRegression(max_iter=400).fit(X[ent], y[ent])`; sus pesos son `logreg.coef_.size + 1`; para medir el tiempo, `time.perf_counter()` antes y después de repetir 100 veces `modelo.predict(X[exa])`.

**Lo que buscas:** si la ventaja de la red tiene un coste que importe en el edge.

<details>
<summary>Ver solución</summary>

```python
# Reto 2: lo que cuesta cada modelo
import time
from sklearn.linear_model import LogisticRegression
logreg = LogisticRegression(max_iter=400).fit(X[ent], y[ent])
for nombre, m in (("regresión logística", logreg), ("red", red)):
    t = time.perf_counter()
    for _ in range(100):
        m.predict(X[exa])
    ms = (time.perf_counter() - t) / (100 * len(exa)) * 1000
    pesos_m = logreg.coef_.size + 1 if m is logreg else pesos
    print(f"{nombre:20s} acierto={(m.predict(X[exa]) == y[exa]).mean():.2f}  pesos={pesos_m:6d}  ms_por_foto={ms:.3f}")
```

```text
regresión logística  acierto=0.88  pesos=   257  ms_por_foto=0.003
red                  acierto=1.00  pesos= 16513  ms_por_foto=0.004
```

La red tiene **64 veces más pesos**, pero decide en prácticamente el mismo tiempo: milésimas de milisegundo por foto, muy por debajo de 1 s de ciclo. Con fotos de 16 × 16, el coste de la red no importa y su ventaja sí. **La regla:** el coste se mide, no se supone. Con una cámara real de millones de puntos y una red de visión de verdad, la cuenta cambia y hace falta otro tipo de equipo; lo verás en el M06-01.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `aviso: la red ha agotado las iteraciones…` | Pocas iteraciones para lo que necesita | Sube el segundo número, por ejemplo a 1000 |
| El examen da 0,50 | No ha aprendido (pocas iteraciones) o ha memorizado (pocas fotos) | Mira la pérdida y el acierto en entrenamiento para saber cuál de las dos |
| Faltan las imágenes | No se hizo M04-01 | El comando las genera; si falla, `lab m04-01` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| el acierto se queda en 0,50 todas las vueltas | pocas vueltas para que la red salga de sus pesos al azar | sube `VUELTAS`; con 300 debería aprender |

## Conclusiones

### Qué es entrenar una red neuronal

Es ajustar los pesos de una cadena de neuronas, iteración a iteración, para que se equivoque cada vez menos con los ejemplos de entrenamiento. La **pérdida** mide ese error y debe bajar; cuando deja de bajar, la red ha **convergido**.

### Cómo se sabe si ha aprendido

| Señal | Qué significa | En el lab |
|-------|---------------|-----------|
| La pérdida no baja | No ha aprendido | 20 iteraciones: 0,70 → 0,69 |
| Acierta igual en entrenamiento y en examen | Ha aprendido algo que generaliza | 1000 iteraciones: 1,00 y 1,00 |
| Acierta mucho en entrenamiento y poco en examen | **Sobreajuste**: ha memorizado | 6 fotos: 1,00 y 0,50 |

### Sus límites

| Límite | Qué provoca |
|--------|-------------|
| Necesita ejemplos | Con pocas fotos, memoriza en lugar de aprender |
| Un examen pequeño engaña | 24 fotos no bastan para fiarse de un 100 % |
| No explica sus decisiones | No dice qué píxeles le hicieron decidir |
| Una red más grande no siempre es mejor | Cuesta más entrenarla y ejecutarla, sin ganar acierto |

### Cómo se mejora

- **Más fotos, y reales**: del propio puesto, con sus condiciones de luz, polvo y posición.
- **Un examen grande y separado**, que el modelo no vea nunca durante el entrenamiento.
- **Redes convolucionales** (las que se usan en visión industrial) cuando los defectos son variados. Necesitan más datos y, para entrenar en serio, GPU.
- **Elegir el tamaño mínimo** que resuelve el problema, sobre todo si va a correr en el edge.

### En una frase

> 🔑 Una red aprende lo que le enseñan los ejemplos. Se la juzga por cómo acierta con lo que no ha visto, nunca por cómo acierta con lo que memorizó.
