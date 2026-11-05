# M04-04 — Entrenar una red neuronal

[← Página anterior](M04-03-inspeccion-camara.md) · [Siguiente página →](../M05-ia-generativa/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **entrenar una red neuronal**: cómo aprende ajustándose iteración a iteración, cómo se sabe si ha aprendido, qué es el sobreajuste y cómo se detecta, y cuándo una red mejora a un modelo sencillo.

### Prerrequisitos

- Las fotos de M04-01 (si no están, el comando las genera).
- Solo `lab`. CPU, sin GPU: cada entrenamiento tarda menos de un segundo.

### Qué está pasando

En el M04-01, una regresión logística separaba carcasas buenas de defectuosas con un **88 %** de acierto. Ahora vas a entrenar una **red neuronal** con las mismas fotos y a ver si lo mejora.

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
| Neuronas | Cuántas combinaciones de píxeles puede aprender | Primer número (por defecto 64) |
| Iteraciones | Cuántas veces como máximo repasa las fotos | Segundo número (por defecto 1000) |
| Fotos | Con cuántos ejemplos aprende | Tercer número: fracción de las fotos de entrenamiento (por defecto 1 = todas) |

Es el mismo tipo de red que reconoce dígitos escritos a mano (una red de una capa oculta), en pequeño.

### 1 — Entrenar la red

**Qué ocurre:** entrenas una red con 64 neuronas usando las 56 fotos de entrenamiento y la examinas con las 24 que no ha visto. El comando enseña cómo baja la pérdida durante el entrenamiento.

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

**Cómo se lee:** para un defecto tan claro como un rayón blanco, unas pocas neuronas bastan. Una red más grande no es mejor si el problema no lo necesita: solo cuesta más entrenarla y ejecutarla, algo que importa cuando corre en un equipo edge junto a la máquina (M06).

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

## Reto

### 1 — ¿Te fías del 100 %?

La red acierta las 24 fotos de examen. ¿La pondrías mañana en el puesto de inspección?

<details>
<summary>Ver solución</summary>

Todavía no. 24 fotos son muy pocas: cada una vale un 4 %, y un 100 % con 24 ejemplos dice poco de cómo se comportará con miles. Además, las fotos son sintéticas y todas parecidas: en la línea habrá polvo, reflejos, piezas giradas y defectos que no son rayones. Antes de llevarla a planta haría falta examinarla con muchas más fotos reales del puesto.

</details>

### 2 — Red o regresión logística

La red gana aquí. ¿Gana siempre?

<details>
<summary>Ver solución</summary>

No. Con pocos datos, la red se sobreajusta y pierde su ventaja (el experimento del 10 % la deja igual que la regresión logística). En el M03-03 verás que con datos de proceso (cuatro señales numéricas) un árbol de decisión sencillo la iguala, y además se puede explicar.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `aviso: la red ha agotado las iteraciones…` | Pocas iteraciones para lo que necesita | Sube el segundo número, por ejemplo a 1000 |
| El examen da 0,50 | No ha aprendido (pocas iteraciones) o ha memorizado (pocas fotos) | Mira la pérdida y el acierto en entrenamiento para saber cuál de las dos |
| Faltan las imágenes | No se hizo M04-01 | El comando las genera; si falla, `lab m04-01` |

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
