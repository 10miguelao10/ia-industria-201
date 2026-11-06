# M04-01 — Clasificación automática de componentes

[← Página anterior](README.md) · [Siguiente página →](M04-02-deteccion-defectos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **clasificación por visión artificial**: cómo aprende un modelo a distinguir piezas buenas de defectuosas en una foto, cómo debe evaluarse, qué puede aprender por error y cómo se mejora.

### Prerrequisitos

- Solo `lab`. Genera 80 PNG pequeñas en `infra/data/imagenes/`.
- Sin cámara y sin GPU.

### Qué está pasando

Al final de EST-01 hay un **puesto de inspección visual**: una cámara fotografía cada carcasa antes de que pase a la siguiente fase. El defecto que se busca es un **rayón** en la superficie.

Para enseñar a un modelo a separar buenas de malas hacen falta fotos de las dos clases. Aquí hay 80, generadas por el laboratorio: 40 carcasas buenas y 40 con un rayón blanco. El modelo aprende con el 70 % de cada clase y se le examina con el 30 % restante, fotos que [no ha visto](../glosario/03-aprendizaje-automatico.md#particion).

Para el modelo, una foto no es una imagen: es una lista de 256 números, el brillo de cada punto de la foto reducida a 16×16. Sin cámara real y sin GPU.

### 1 — Generar y entrenar

Vas a generar el juego de imágenes, entrenar con el 70 % y medir el acierto con el 30 % que el modelo no ha visto.

```bash
# Genera las imágenes (si faltan), entrena y guarda modelo_vision.joblib
docker compose --profile lab run --rm --no-deps lab m04-01
```

📋 Ficha del comando [`m04-01`](../comandos-lab.md#m04-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
acierto_prueba=0.88
OK m04-01: acierto=0.88 en imágenes no usadas al entrenar
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
def _features_imagen(ruta):
    img = Image.open(ruta).convert("L").resize((16, 16))    # gris y 16×16
    return np.asarray(img, dtype=np.float32).reshape(-1) / 255.0   # 256 números entre 0 y 1

X = np.stack([_features_imagen(r) for r in entreno["ruta"]])
modelo = LogisticRegression(max_iter=400)
modelo.fit(X, entreno["defecto"])                          # cada píxel es una entrada
```

Para el modelo, una imagen es una fila de 256 números: el brillo de cada [píxel](../glosario/03-aprendizaje-automatico.md#vision-pixeles).

</details>

### 2 — Mirar una de cada

Vas a abrir una imagen buena y una defectuosa. Tienes que ver qué está aprendiendo el modelo: el rayón, no un fondo distinto.

```bash
ls data/imagenes/buenas | head -3        # ok_00.png, ok_01.png…
ls data/imagenes/defectuosas | head -3   # ko_00.png, ko_01.png…
```

Ábrelas en VS Code: `infra/data/imagenes/buenas/ok_00.png` y `infra/data/imagenes/defectuosas/ko_00.png`.

**Resultado esperado:** la defectuosa tiene una línea blanca; la buena, no.

![Pieza buena (izquierda) y defectuosa con rayón blanco (derecha)](../img/M04-01-buena-defectuosa.png)

## Comprueba tu entendimiento

**Imágenes nuevas**

El acierto que imprime el comando, ¿de qué imágenes es?

→ Del 30 % apartado, no de las del entrenamiento.

## Experimenta: ¿cuánto detalle hace falta?

**Qué ocurre:** el modelo ve cada foto reducida a 16×16 píxeles. Vas a probar con menos y con más detalle. El parámetro `lado` cambia el tamaño al que se reduce la foto (estas pruebas no sustituyen el modelo guardado, que sigue siendo el de 16×16).

**Predice:** con fotos de 4×4 (16 números), ¿se verá el rayón?

```bash
docker compose --profile lab run --rm --no-deps lab m04-01 lado=4
docker compose --profile lab run --rm --no-deps lab m04-01 lado=8
docker compose --profile lab run --rm --no-deps lab m04-01 lado=32
```

**Resultado esperado:**

```text
lado=4: 16 píxeles por foto (no se guarda el modelo)
acierto_prueba=0.79
FALLO: el clasificador visual no separa las piezas
```

```text
lado=8: 64 píxeles por foto (no se guarda el modelo)
acierto_prueba=0.83
FALLO: el clasificador visual no separa las piezas
```

```text
lado=32: 1024 píxeles por foto (no se guarda el modelo)
acierto_prueba=0.92
OK m04-01: acierto=0.92 en imágenes no usadas al entrenar
```

| Lado | Números por foto | Acierto en examen |
|------|------------------|-------------------|
| 4 | 16 | 0,79 |
| 8 | 64 | 0,83 |
| 16 | 256 | 0,88 |
| 32 | 1 024 | 0,92 |

**Cómo se lee:** al reducir tanto la foto, el rayón (una línea de 2 píxeles en una foto de 64) se mezcla con el resto y casi desaparece. Con más detalle, el modelo acierta más, a cambio de procesar cuatro veces más números. En planta pasa lo mismo con la **resolución de la cámara**: tiene que ser suficiente para que el defecto más pequeño que importa ocupe varios píxeles.

## Constrúyelo tú: tu propio clasificador de imágenes

**Qué está pasando:** `lab m04-01` convierte las fotos en números y entrena un modelo sin que veas cómo. Ahora lo haces tú: abres una foto, la conviertes en la tabla de números que ve el modelo, preparas todas las fotos, entrenas y examinas. Al final miras **dónde se fija** el modelo dibujando sus pesos como una imagen: así se comprueba si ha aprendido el rayón o alguna otra cosa.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que tu código encuentra las fotos del puesto de inspección.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m04_01_mi_clasificador.py`](../../infra/construye/m04_01_mi_clasificador.py). El paso 1 ya está escrito: lee `manifiesto.csv`, la lista de fotos con su clase, y abre la primera. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_01_mi_clasificador.py
```

**Resultado esperado:**

```text
fotos=80 defectuosas=40  tamaño de cada foto=(64, 64)
```

**Cómo se lee:** 80 fotos, la mitad defectuosas, de 64 × 64 puntos cada una. Son las que generó el paso 1 del lab en `infra/data/imagenes/`. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Convertir una foto en números

**Para qué:** ver exactamente lo que recibe el modelo, que no es una imagen.

**Qué ocurre:** pasas la foto a escala de grises, la reduces a `LADO` × `LADO` puntos y la conviertes en una tabla de números entre 0 (negro) y 1 (blanco). Enseñas el tamaño de la tabla y una fila.

Pega debajo de `# --- PASO 2`:

```python
def a_numeros(ruta):
    gris = Image.open(ruta).convert("L").resize((LADO, LADO))     # gris y más pequeña
    return np.asarray(gris, dtype=np.float32) / 255.0             # cada punto: de 0 (negro) a 1 (blanco)

tabla = a_numeros(fotos["ruta"][0])
print(f"una foto son {tabla.shape[0]} × {tabla.shape[1]} = {tabla.size} números")
print("fila central:", np.round(tabla[LADO // 2], 2))
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
una foto son 16 × 16 = 256 números
fila central: [0.72 0.73 0.7  0.49 0.47 0.47 0.47 0.47 0.47 0.47 0.47 0.47 0.47 0.65
 0.73 0.72]
```

**Cómo se lee:** para el modelo, la foto es esto: 256 números. La fila central cruza la carcasa por el medio: valores bajos (más oscuro) en el centro, donde está la carcasa, y más altos en los bordes, el fondo. El modelo no sabe qué es una carcasa ni un rayón; solo ve qué números suelen ser altos en las fotos malas.

### 3 — Preparar todas las fotos

**Para qué:** tener la tabla de entrada del modelo: una fila por foto, una columna por punto.

**Qué ocurre:** conviertes cada foto en sus números y la aplanas en una sola fila. El resultado es una tabla de 80 filas y 256 columnas, y al lado, la clase de cada foto.

Pega debajo de `# --- PASO 3`:

```python
X = np.stack([a_numeros(ruta).reshape(-1) for ruta in fotos["ruta"]])   # cada foto, en una fila
y = fotos["defecto"].to_numpy()
print(f"tabla de entrada: {X.shape[0]} fotos × {X.shape[1]} puntos")
```

**Resultado esperado** (líneas nuevas):

```text
tabla de entrada: 80 fotos × 256 puntos
```

**Cómo se lee:** es la misma forma que el `limpio.csv` del M03: una fila por pieza y una columna por señal. Solo que aquí cada «señal» es el brillo de un punto de la foto.

### 4 — Entrenar y examinar

**Para qué:** medir el modelo con fotos que no ha visto, sin [desequilibrar](../glosario/03-aprendizaje-automatico.md#desequilibrio) las clases.

**Qué ocurre:** separas el 70 % de las buenas y el 70 % de las malas para entrenar, y el resto para el examen. Entrenas una [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) y cuentas cuántas fotos de examen acierta.

Pega debajo de `# --- PASO 4`:

```python
buenas, malas = np.where(y == 0)[0], np.where(y == 1)[0]
n_b, n_m = int(len(buenas) * 0.7), int(len(malas) * 0.7)
ent = np.concatenate([buenas[:n_b], malas[:n_m]])                # 70 % de cada clase
exa = np.concatenate([buenas[n_b:], malas[n_m:]])                # 30 % de cada clase
modelo = LogisticRegression(max_iter=400).fit(X[ent], y[ent])
acierto = (modelo.predict(X[exa]) == y[exa]).mean()
print(f"entrenar={len(ent)} fotos  examen={len(exa)} fotos  acierto en examen={acierto:.2f}")
```

**Resultado esperado** (líneas nuevas):

```text
entrenar=56 fotos  examen=24 fotos  acierto en examen=0.88
```

**Cómo se lee:** es el 88 % de `lab m04-01`: has reconstruido el clasificador. Se separa por clase para que el examen tenga tantas buenas como malas; si se partiera al azar, con tan pocas fotos podría quedar casi sin malas.

### 5 — Ver dónde se fija el modelo

**Para qué:** comprobar que el modelo ha aprendido el rayón y no otra cosa.

**Qué ocurre:** el modelo tiene un peso por punto de la foto. Los vuelves a colocar en su cuadrícula de `LADO` × `LADO` y los dibujas con caracteres: `#` donde un punto claro empuja hacia «defectuosa», `.` donde empuja hacia «buena».

Pega debajo de `# --- PASO 5`:

```python
pesos = modelo.coef_[0].reshape(LADO, LADO)
corte = np.abs(pesos).max() / 3
for fila in pesos:
    print("".join("#" if p > corte else "." if p < -corte else " " for p in fila))
```

**Resultado esperado** (líneas nuevas: 16 filas de 16 caracteres):

```text
                
                
                
                
  ############  
  ############  
  ############  
  ############  
  ############  
   ###########
```

**Cómo se lee:** los `#` forman **franjas horizontales** en la zona central: es donde aparecen los rayones de las fotos defectuosas, líneas blancas horizontales a distintas alturas. El modelo ha aprendido a mirar ahí. Si los `#` estuvieran en una esquina o en el fondo, el modelo estaría usando un atajo que en planta no serviría (reto 1).

### 6 — Decide tú: la foto entera, sin reducir

**Para qué:** saber si más detalle siempre es mejor.

**Qué ocurre:** cambias `LADO = 16` por `LADO = 64`, el tamaño original de la foto, y ejecutas. El modelo recibe ahora 4 096 números por foto.

**Resultado esperado** (líneas que cambian; el dibujo es ahora de 64 × 64):

```text
tabla de entrada: 80 fotos × 4096 puntos
entrenar=56 fotos  examen=24 fotos  acierto en examen=0.92
```

**Cómo se lee:** **el mismo 0,92 que con 32 × 32**, la última prueba de «Experimenta», con cuatro veces más números. A partir de cierto detalle, más resolución no mejora: el rayón ya se veía bien. El dibujo de pesos sigue marcando la misma franja central. En planta, se elige la resolución más baja que todavía ve el defecto más pequeño que hay que detectar: más detalle cuesta cámara, cálculo y [tiempo de ciclo](../glosario/01-datos-arquitectura.md#tiempo-ciclo). Vuelve a dejar `LADO = 16`.
## Reto

### 1 — Un atajo que el modelo aprende sin que nadie se lo pida

**La situación:** las fotos defectuosas de entrenamiento se hicieron otro día, con la luz del puesto algo más fuerte. Nadie se dio cuenta: a simple vista se ven igual. Las fotos del examen, como las de la línea, se hacen con la luz normal.

**Qué haces:** en tu script de «Constrúyelo tú», añades al final un bloque que aclara un poco (+0,15) todas las fotos **malas de entrenamiento**, entrena otro modelo con ellas y lo examina con las fotos normales. Después dibuja sus pesos como en el paso 5.

**Pistas:** `X_luz = X.copy()` para no tocar las originales; `ent[y[ent] == 1]` son las posiciones de las malas de entrenamiento; `np.clip(valores, 0, 1)` evita pasar de blanco.

**Lo que buscas:** el acierto en entrenamiento y en examen del modelo nuevo, y dónde se fija ahora.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: las fotos malas de entrenamiento se hicieron con más luz
X_luz = X.copy()
malas_ent = ent[y[ent] == 1]
X_luz[malas_ent] = np.clip(X_luz[malas_ent] + 0.15, 0, 1)          # todas las malas, un poco más claras
atajo = LogisticRegression(max_iter=400).fit(X_luz[ent], y[ent])
print(f"con el atajo: acierto en entrenamiento={(atajo.predict(X_luz[ent]) == y[ent]).mean():.2f}  "
      f"en examen (fotos normales)={(atajo.predict(X[exa]) == y[exa]).mean():.2f}")
p = atajo.coef_[0].reshape(LADO, LADO); c = np.abs(p).max() / 3
for fila in p:
    print("".join("#" if v > c else "." if v < -c else " " for v in fila))
```

```text
con el atajo: acierto en entrenamiento=1.00  en examen (fotos normales)=0.50
################
################
...
################
```

**Acierta el 100 % de las fotos de entrenamiento y el 50 % de las del examen, lo mismo que tirar una moneda.** El dibujo lo explica: los `#` cubren **toda la foto**. El modelo ha aprendido «foto más clara = defectuosa», un atajo más fácil que el rayón, y en la línea, con la luz normal, no sirve. Nada avisa durante el entrenamiento: el 100 % parece un éxito.

**La regla:** las fotos de las dos clases tienen que hacerse en las mismas condiciones (luz, cámara, posición, fondo), y hay que mirar dónde se fija el modelo antes de fiarse de su acierto.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el clasificador visual no separa las piezas` | las imágenes no se generaron bien | borra `data/imagenes` y repite |
| no encuentras los PNG | los buscas dentro del contenedor | están en el disco del puesto, en `infra/data/imagenes` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/imagenes/manifiesto.csv` | no has generado las fotos | lanza el paso 1 del lab, `lab m04-01` |

## Conclusiones

### Qué es clasificar con visión

Es enseñar a un modelo a decir «buena» o «defectuosa» a partir de una foto. Para el modelo, una foto es una lista de números: aquí, el brillo de 256 puntos (la foto reducida a 16×16). Aprende qué patrones de números aparecen en las fotos de cada clase.

### Cómo debe evaluarse

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Ejemplos de las dos clases | 40 buenas y 40 con rayón |
| Examen con fotos no vistas | El 30 % de cada clase se aparta |
| Ver qué ha aprendido | Abrir fotos de cada clase y comprobar que la diferencia es el rayón |

Resultado: **88 % de acierto** en las fotos de examen.

### Qué puede aprender por error

| Riesgo | Ejemplo |
|--------|---------|
| Aprender el fondo en vez del defecto | Si todas las malas se fotografiaran con otra luz, el modelo aprendería la luz |
| Pocas fotos de defecto | En planta, los defectos son raros y hay pocos ejemplos |
| Fotos de laboratorio, no de línea | Un modelo entrenado con fotos perfectas falla con polvo, reflejos o piezas giradas |

Un 88 % significa que algunas fotos se clasifican mal: en la línea, defectos que pasan o piezas buenas que se paran.

### Cómo se mejora

- Fotos **en las condiciones reales** del puesto: misma cámara, luz y posición.
- **Resolución suficiente** para el defecto más pequeño que importe (en el experimento, de 0,79 con 4×4 a 0,92 con 32×32).
- **Más ejemplos de defecto** y de variaciones normales.
- Modelos de visión más capaces (redes convolucionales) cuando el defecto no es tan simple como una línea clara.

### En una frase

> 🔑 Un modelo de visión aprende lo que diferencia a las fotos de entrenamiento, que no siempre es lo que tú querías que aprendiera.
