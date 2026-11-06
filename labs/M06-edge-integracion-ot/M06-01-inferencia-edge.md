# M06-01 — Inferencia en entornos edge

[← Página anterior](README.md) · [Siguiente página →](M06-02-integracion-ot.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **[inferencia](../glosario/05-operacion-gobierno.md#inferencia) en el [edge](../glosario/01-datos-arquitectura.md#edge)**: por qué el modelo se ejecuta junto a la máquina, cómo debe medirse si llega a tiempo, qué riesgos tiene y cómo se asegura que funcione sin red.

### Prerrequisitos

- `data/modelo_defecto.joblib` de M03-03.
- Unos 0,4 GB. Este paso no usa el modelo generativo.

### Qué está pasando

El modelo de defecto del M03-03 tiene que dar su [dictamen](../glosario/05-operacion-gobierno.md#dictamen) de cada carcasa **antes de que salga la siguiente**, y en EST-01 sale una por segundo. Además, la línea no puede depender de que funcione la red de la oficina o internet.

Por eso el modelo se ejecuta en el **equipo edge**, el ordenador que está junto a la máquina. En este laboratorio ese equipo es tu puesto: el modelo se carga desde un fichero del disco, sin ninguna dirección de red.

Se dictaminan 20 piezas seguidas y se mide la media. La primera no cuenta, porque incluye el tiempo de cargar el modelo y no se repite en cada pieza.

### 1 — Liberar memoria

Vas a parar el modelo generativo, que en este módulo no hace falta y es el que más memoria ocupa.

```bash
docker compose stop llm
```

### 2 — Medir en caliente

Vas a cargar el modelo de defecto desde el disco y medir cuántos milisegundos tarda en dictaminar una pieza. La [latencia](../glosario/05-operacion-gobierno.md#latencia) que importa es la de la pieza siguiente, no la del arranque.

```bash
docker compose --profile lab run --rm --no-deps lab m06-01
```

📋 Ficha del comando [`m06-01`](../comandos-lab.md#m06-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (el tiempo depende del puesto; tiene que quedar por debajo de 200 ms):

```text
ms_por_pieza=0.35 fichero=modelo_defecto.joblib tamaño=2.5 KB tipo=DecisionTreeClassifier
OK m06-01: 0.35 ms por pieza, modelo en disco
```

Menos de medio milisegundo frente a un ciclo de estación de alrededor de 1 segundo: cabe de sobra. El modelo ocupa 2,5 KB.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
modelo = joblib.load(DATA / "modelo_defecto.joblib")    # del disco, sin red
fila = pd.read_csv(DATA / "limpio.csv").head(1)[FEATURES]
modelo.predict_proba(fila)                              # calentamiento: la primera no cuenta

t0 = time.perf_counter()
for _ in range(20):
    modelo.predict_proba(fila)
ms = (time.perf_counter() - t0) * 1000 / 20             # media por pieza
```

</details>

## Comprueba tu entendimiento

**Sin nube**

¿A qué dirección se conecta este paso para predecir?

→ A ninguna. Lee `modelo_defecto.joblib` del disco.

## Experimenta: otro modelo, el mismo tiempo

**Qué ocurre:** mides la latencia del otro candidato del M03, la [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica). El parámetro `modelo` elige el fichero.

```bash
docker compose --profile lab run --rm --no-deps lab m06-01 modelo=modelo_logreg.joblib
```

**Resultado esperado:**

```text
ms_por_pieza=0.35 fichero=modelo_logreg.joblib tamaño=1.2 KB tipo=LogisticRegression
OK m06-01: 0.35 ms por pieza, modelo en disco
```

**Cómo se lee:** el mismo tiempo, con un modelo distinto. Con modelos tan pequeños, casi todo ese tiempo **no es el modelo**: es preparar la entrada (convertir la fila en una tabla) y devolver el resultado. En un equipo edge real, lo que suele tardar es leer el dato y comunicarse, no el modelo. Por eso se mide la cadena completa, no solo el modelo.

## Constrúyelo tú: tu propio banco de pruebas de inferencia

**Qué está pasando:** `lab m06-01` mide una vez cuánto tarda el modelo en decidir una pieza. Ahora montas tú el banco de pruebas que usaría un integrador antes de instalar un modelo en el edge: la primera inferencia frente a las siguientes, el **peor caso** en mil piezas y no solo la media, la diferencia entre decidir una a una o en lote, y el margen frente al ciclo de la estación.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** saber qué modelo vas a medir y con qué piezas.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m06_01_mi_banco_pruebas.py`](../../infra/construye/m06_01_mi_banco_pruebas.py). Arriba están las **decisiones** (`MODELO`, `CICLO_S`, `PIEZAS`); debajo, el paso 1 ya escrito: carga el modelo elegido en el M03-03 y prepara mil piezas sacadas de `limpio.csv`. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m06_01_mi_banco_pruebas.py
```

**Resultado esperado:**

```text
modelo=modelo_defecto.joblib tipo=DecisionTreeClassifier tamaño=2.5 KB  piezas de prueba=1000
```

**Cómo se lee:** un árbol de decisión de pocos KB: el modelo que iría al edge. Las mil piezas son de verdad, de tu [histórico](../glosario/01-datos-arquitectura.md#historico) limpio, repetidas al azar para tener suficientes. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — La primera inferencia y las siguientes

**Para qué:** saber si la primera pieza después de arrancar tarda más que las demás.

**Qué ocurre:** mides en milisegundos la primera decisión y, después, la segunda y la tercera, siempre con una pieza.

Pega debajo de `# --- PASO 2`:

```python
def medir_una(i):
    inicio = time.perf_counter()
    modelo.predict(piezas.iloc[[i]])                  # una sola pieza, como en la línea
    return (time.perf_counter() - inicio) * 1000      # milisegundos

print("ms: primera={:.2f}  segunda={:.2f}  tercera={:.2f}".format(medir_una(0), medir_una(1), medir_una(2)))
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (línea nueva; cambian los números):

```text
ms: primera=1.22  segunda=0.65  tercera=0.74
```

**Cómo se lee:** la primera tarda casi el doble que las siguientes: Python y la librería preparan cosas la primera vez. Aquí es poco, pero con modelos grandes la primera inferencia puede tardar segundos. Por eso `lab m06-01` mide «en caliente», y por eso un servicio de inferencia se calienta al arrancar, antes de recibir piezas reales.

### 3 — El peor caso en mil piezas

**Para qué:** conocer cuánto puede llegar a tardar, que es lo que importa en una línea.

**Qué ocurre:** decides las mil piezas una a una, guardas cuánto tarda cada una y calculas la media, el percentil 99 (lo que tardan 99 de cada 100) y el máximo.

Pega debajo de `# --- PASO 3`:

```python
tiempos = np.array([medir_una(i) for i in range(len(piezas))])
p99 = np.percentile(tiempos, 99)
print(f"ms por pieza: media={tiempos.mean():.2f}  p99={p99:.2f}  máximo={tiempos.max():.2f}")
```

**Resultado esperado** (línea nueva; cambian los números):

```text
ms por pieza: media=0.46  p99=0.76  máximo=1.02
```

**Cómo se lee:** media de medio milisegundo, pero **el máximo es más del doble de la media**: alguna pieza coincide con otra tarea del equipo y tarda más. Un dictamen llega a tiempo si llega a tiempo **la pieza más lenta**, no la media. Por eso se mira el p99 y el máximo.

### 4 — Una a una o en lote

**Para qué:** saber cuánto del tiempo es el modelo y cuánto es preparar cada llamada.

**Qué ocurre:** decides las mil piezas **de una vez**, en una sola llamada, y calculas lo que toca por pieza.

Pega debajo de `# --- PASO 4`:

```python
inicio = time.perf_counter()
modelo.predict(piezas)                                 # las mil de golpe
por_pieza_lote = (time.perf_counter() - inicio) * 1000 / len(piezas)
print(f"en lote: {por_pieza_lote:.4f} ms por pieza  ({tiempos.mean() / por_pieza_lote:.0f} veces menos que una a una)")
```

**Resultado esperado** (línea nueva; cambian los números):

```text
en lote: 0.0005 ms por pieza  (913 veces menos que una a una)
```

**Cómo se lee:** en lote, cada pieza cuesta **cientos de veces menos**: casi todo el tiempo de la llamada una a una es preparar la llamada, no el árbol. En una línea no se puede esperar a juntar mil piezas, así que se decide una a una; pero si se analiza el histórico de un turno, se hace en lote.

### 5 — El margen frente al ciclo

**Para qué:** convertir los milisegundos en una respuesta para producción: ¿cabe o no cabe?

**Qué ocurre:** comparas el peor tiempo medido con el ciclo de la estación y calculas qué parte del ciclo se lleva la inferencia.

Pega debajo de `# --- PASO 5`:

```python
peor = tiempos.max()
print(f"peor caso={peor:.2f} ms de un ciclo de {CICLO_S * 1000:.0f} ms -> usa el {peor / (CICLO_S * 1000):.2%} del ciclo")
print("veredicto:", "cabe con margen" if peor < CICLO_S * 1000 * 0.1 else "NO cabe con margen (más del 10 % del ciclo)")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
peor caso=1.02 ms de un ciclo de 1000 ms -> usa el 0.10% del ciclo
veredicto: cabe con margen
```

**Cómo se lee:** incluso la pieza más lenta usa una fracción minúscula del ciclo. El 10 % es un margen habitual: el dictamen tiene que viajar por [MQTT](../glosario/01-datos-arquitectura.md#mqtt) y el automatismo tiene que actuar en el resto. Con un árbol pequeño en un procesador normal sobra tiempo: no hace falta GPU ni nube.

### 6 — Decide tú: otro modelo

**Para qué:** ver cómo cambia el coste con el tipo de modelo.

**Qué ocurre:** cambias `MODELO` por `"mi_modelo.joblib"`, el que elegiste con tu propia comparación en el M03-03 (si no lo tienes, usa `"modelo_logreg.joblib"`), y ejecutas.

**Resultado esperado** (líneas que cambian):

```text
modelo=mi_modelo.joblib tipo=Pipeline tamaño=75.8 KB  piezas de prueba=1000
ms por pieza: media=0.59  p99=0.90  máximo=30.51
peor caso=30.51 ms de un ciclo de 1000 ms -> usa el 3.05% del ciclo
```

**Cómo se lee:** la red (aquí, el elegido en el M03-03) ocupa 30 veces más que el árbol y tarda algo más de media. Y fíjate en el **máximo: 30 ms**, una pieza que tardó 50 veces la media sin que el modelo cambiara; fue el equipo, ocupado en otra cosa en ese instante. Aun así usa el 3 % del ciclo. Con datos de proceso de cuatro señales, cualquier modelo de estos cabe en el edge; la decisión entre ellos se toma por lo que aciertan y por si se pueden explicar. Con imágenes grandes la cuenta sería otra. Vuelve a dejar `MODELO = "modelo_defecto.joblib"`.
## Reto

### 1 — Un dictamen que llega tarde

**La situación:** el automatismo espera el dictamen de cada carcasa un tiempo fijo, el **plazo**, antes de que la carcasa salga de la estación. Si el dictamen no ha llegado, no puede esperar más.

**Qué haces:** en tu banco de pruebas, añades al final un bloque que fija un plazo de 2 ms y cuenta, con los tiempos del paso 3, cuántos dictámenes llegarían tarde. Pruébalo con `MODELO = "modelo_defecto.joblib"` y con `MODELO = "mi_modelo.joblib"`.

**Pistas:** `(tiempos > PLAZO_MS).sum()` cuenta los que pasan del plazo.

**Lo que buscas:** cuántas carcasas se quedarían sin dictamen a tiempo con cada modelo, y qué hay que hacer con ellas.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: un plazo para cada dictamen; si no llega, la pieza va a revisión
PLAZO_MS = 2
tarde = int((tiempos > PLAZO_MS).sum())
print(f"plazo={PLAZO_MS} ms: dictámenes a tiempo={len(tiempos) - tarde}  tarde={tarde} -> {tarde} piezas a revisión por no tener dictamen")
```

```text
# MODELO = "modelo_defecto.joblib"
plazo=2 ms: dictámenes a tiempo=1000  tarde=0 -> 0 piezas a revisión por no tener dictamen
# MODELO = "mi_modelo.joblib"
plazo=2 ms: dictámenes a tiempo=999  tarde=1 -> 1 piezas a revisión por no tener dictamen
```

Con el árbol, todos a tiempo. Con la red, **una de mil llega tarde**: la del pico de 30 ms. Con un plazo de 2 ms, esa carcasa sale de la estación sin dictamen.

**Qué hacer con ella:** no se acepta sola. **Llegar tarde es no llegar**: la carcasa va a revisión, como la del puesto sin foto del M04-03. **La regla:** el plazo se fija con el peor caso medido y un margen, no con la media; y el automatismo tiene que tener decidido qué hace con una carcasa sin dictamen, porque tarde o temprano pasará.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: falta el modelo; pasa antes por M03-03` | no terminó M03-03 | lanza `m03-03` |
| `FALLO: la inferencia local va demasiado lenta` | el puesto está saturado | `docker compose stop llm` y repite |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/mi_modelo.joblib` | no hiciste «Constrúyelo tú» del M03-03 | usa `MODELO = "modelo_logreg.joblib"` |

## Conclusiones

### Qué es la inferencia en el edge

Es ejecutar el modelo **en el equipo que está junto a la máquina**, cargándolo desde su disco, sin llamar a ningún servidor. En el lab, ese equipo es tu puesto.

### Cómo debe medirse

| Requisito | En el lab |
|-----------|-----------|
| Medir la pieza siguiente, no el arranque | La primera predicción no cuenta |
| Medir varias veces | Media de 20 dictámenes |
| Comparar con el ciclo de la máquina | 0,35 ms por pieza frente a ~1 s de ciclo |
| Medir en el equipo real | El tiempo depende del puesto |

### Sus riesgos

| Riesgo | Qué provoca |
|--------|-------------|
| El equipo está cargado con otras cosas | El dictamen llega tarde (por eso se para el modelo generativo) |
| El modelo del equipo no es el aprobado | Se dictamina con una versión que nadie validó |
| El dictamen llega tarde | La pieza ya salió: debe ir a revisión |

### Cómo se asegura

- **Medir en el equipo real**, con la carga real, antes de llevarlo a la línea.
- **Controlar qué modelo y qué versión** hay en cada equipo edge (lo verás en M07).
- Definir qué pasa **si no hay dictamen a tiempo**: la pieza no se acepta sola.

### En una frase

> 🔑 El edge acerca el modelo a la máquina para que llegue a tiempo y no dependa de la red. Hay que medirlo en el equipo real, pieza a pieza.
