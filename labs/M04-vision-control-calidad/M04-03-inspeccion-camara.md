# M04-03 — Sistema de inspección basado en cámara

[← Página anterior](M04-02-deteccion-defectos.md) · [Siguiente página →](M04-04-red-neuronal.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo funciona un **puesto de inspección**: cómo pasa una pieza de foto a decisión, cómo debe ser el registro que deja, qué papel tiene el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) y cómo se decide dónde ponerlo.

### Prerrequisitos

- `modelo_vision.joblib` de M04-01.
- Escribe `data/lote_entrada/` y `data/lote_resultado.csv`.

### Qué está pasando

Así trabaja un puesto de inspección en la línea: las fotos de las carcasas llegan a una **carpeta de entrada** y el sistema deja un **registro** con una decisión por cada una, `aceptar` o `revisar`.

Llega un lote de 6 carcasas: 3 buenas y 3 con rayón. El modelo del M04-01 da a cada una una probabilidad de defecto. Con 0,5 o más va a revisión; por debajo se acepta. No se vuelve a entrenar nada: inspeccionar es usar el modelo que ya hay.

### 1 — Pasar el lote

Vas a inspeccionar un lote con el modelo ya entrenado. Inspeccionar es dar un [dictamen](../glosario/05-operacion-gobierno.md#dictamen) por imagen, no volver a entrenar.

```bash
# Copia 6 imágenes a lote_entrada, las puntúa y escribe lote_resultado.csv
docker compose --profile lab run --rm --no-deps lab m04-03
```

📋 Ficha del comando [`m04-03`](../comandos-lab.md#m04-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493  aceptar
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=2
```

Fíjate en `ko_00.png`: es defectuosa, pero con 0,493 queda justo por debajo del umbral y se acepta. Es un defecto que se escapa.

### 2 — Leer el registro

Vas a abrir el registro que quedaría en el puesto de inspección.

```bash
cat data/lote_resultado.csv
ls data/lote_entrada
```

**Resultado esperado:**

```text
imagen,probabilidad_defecto,decision
ok_00.png,0.345,aceptar
ok_01.png,0.269,aceptar
ok_02.png,0.314,aceptar
ko_00.png,0.493,aceptar
ko_01.png,0.657,revisar
ko_02.png,0.714,revisar
```

```text
ko_00.png  ko_01.png  ko_02.png  ok_00.png  ok_01.png  ok_02.png
```

## Comprueba tu entendimiento

**El registro cuadra**

Cuenta filas del CSV (sin la cabecera) y ficheros en `lote_entrada`.

→ Seis y seis: cada imagen tiene su dictamen.

## Experimenta: mover el umbral

**Qué ocurre:** `ko_00.png` se escapa por 0,007. Vas a bajar el umbral de revisión de 0,5 a 0,4.

```bash
docker compose --profile lab run --rm --no-deps lab m04-03 umbral=0.4
```

**Resultado esperado:**

```text
umbral=0.4 duda=±0.0
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493  revisar
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=3
```

**Cómo se lee:** las tres defectuosas van a revisión y las tres buenas siguen aceptándose. Con este lote, 0,4 es mejor. Pero la buena con más probabilidad está en 0,345: con un umbral de 0,3 empezarías a parar piezas buenas. El margen entre «la mala más baja» (0,493) y «la buena más alta» (0,345) es estrecho, y con miles de piezas habrá solapes.

## Mejora: una zona de duda

**Qué ocurre:** en lugar de obligar al umbral a decidir siempre, defines una **[zona de duda](../glosario/03-aprendizaje-automatico.md#zona-duda)**: las piezas cuya probabilidad esté a menos de 0,1 del umbral no se aceptan ni se rechazan: van a una persona. El parámetro `duda` lo activa.

```bash
docker compose --profile lab run --rm --no-deps lab m04-03 duda=0.1
```

**Resultado esperado:**

```text
umbral=0.5 duda=±0.1
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493   dudosa
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=2
```

**Cómo se lee:** `ko_00.png` ya no se acepta: queda como **dudosa**, para que la mire un operario. Las claras siguen decidiéndose solas. Es el diseño habitual de los puestos de inspección con IA: el modelo resuelve lo evidente y la persona, lo dudoso. El tamaño de la zona de duda se ajusta según cuántas piezas puede revisar el turno.

## Constrúyelo tú: tu propio puesto de inspección

**Qué está pasando:** `lab m04-03` pasa un lote de seis fotos por el modelo y deja un registro. Ahora montas tú el puesto completo: para cada carcasa que llega, calculas la probabilidad de defecto, decides con un umbral y una zona de duda, y escribes una línea de registro que permita saber después **qué se decidió, cuándo y con qué modelo**. Lo pruebas con las 24 fotos de examen del M04-01, las que el modelo no vio al aprender.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que el puesto tiene su modelo y las carcasas que tiene que inspeccionar.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m04_03_mi_puesto.py`](../../infra/construye/m04_03_mi_puesto.py). Arriba están las **decisiones** (`UMBRAL`, `DUDA`); debajo, el paso 1 ya escrito: carga el modelo que guardó `lab m04-01` y elige las 24 fotos de examen, las mismas que en el M04-01. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_03_mi_puesto.py
```

**Resultado esperado:**

```text
carcasas que llegan al puesto: 24 (12 con rayón, que el puesto no sabe)
```

**Cómo se lee:** 24 carcasas, la mitad con rayón. El puesto no ve la columna `defecto`: solo la usarás al final para contar aciertos. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — La probabilidad de cada carcasa

**Para qué:** obtener del modelo lo que de verdad da: una probabilidad, no una decisión.

**Qué ocurre:** preparas cada foto igual que en el M04-01 (gris, 16 × 16, de 0 a 1) y pides al modelo la probabilidad de defecto. Enseñas cuántas carcasas caen en cada tramo.

Pega debajo de `# --- PASO 2`:

```python
def probabilidad(ruta):
    numeros = np.asarray(Image.open(ruta).convert("L").resize((16, 16)), dtype=np.float32).reshape(1, -1) / 255.0
    return float(modelo.predict_proba(numeros)[0, 1])

llegan = llegan.assign(probabilidad=[probabilidad(r) for r in llegan["ruta"]])
tramos = pd.cut(llegan["probabilidad"], [0, 0.2, 0.4, 0.6, 0.8, 1.0], include_lowest=True)
print(tramos.value_counts().sort_index().to_string())
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
probabilidad
(-0.001, 0.2]     0
(0.2, 0.4]       11
(0.4, 0.6]        9
(0.6, 0.8]        4
(0.8, 1.0]        0
```

**Cómo se lee:** **ninguna carcasa por debajo de 0,2 ni por encima de 0,8**: este modelo nunca está muy seguro, y 9 de 24 caen entre 0,4 y 0,6, cerca del umbral. Con esas, cualquier umbral es casi tirar una moneda. Es lo esperable en un modelo sencillo sobre [píxeles](../glosario/03-aprendizaje-automatico.md#vision-pixeles), y es lo que hace necesaria la zona de duda.

### 3 — Decidir con el umbral y la zona de duda

**Para qué:** convertir la probabilidad en lo que hace el puesto con la carcasa.

**Qué ocurre:** si la probabilidad está a menos de `DUDA` del umbral, la carcasa es **dudosa** y la mira una persona; si no, se **acepta** o se manda a **revisar**. Cuentas cuántas van a cada sitio y cuántos rayones se aceptan sin querer.

Pega debajo de `# --- PASO 3`:

```python
def decidir(p):
    if abs(p - UMBRAL) < DUDA:
        return "dudosa"                                  # la decide una persona
    return "revisar" if p >= UMBRAL else "aceptar"

llegan = llegan.assign(decision=[decidir(p) for p in llegan["probabilidad"]])
print(dict(Counter(llegan["decision"])))
escapan = int(((llegan["decision"] == "aceptar") & (llegan["defecto"] == 1)).sum())
paradas = int(((llegan["decision"] == "revisar") & (llegan["defecto"] == 0)).sum())
print(f"rayones aceptados={escapan}  buenas mandadas a revisar={paradas}")
```

**Resultado esperado** (líneas nuevas):

```text
{'aceptar': 15, 'revisar': 9}
rayones aceptados=3  buenas mandadas a revisar=0
```

**Cómo se lee:** sin zona de duda, todas las carcasas se deciden solas, y el puesto se equivoca en tres: es el 88 % de acierto del M04-01. Y los tres errores son del peor tipo: **rayones aceptados**, que llegarían al cliente. Ninguna buena se manda a revisar sin motivo.

### 4 — Escribir el registro

**Para qué:** poder saber después qué se decidió con cada carcasa, cuándo y con qué modelo.

**Qué ocurre:** calculas la **huella** del fichero del modelo (un código que cambia si cambia un solo byte) y escribes `mi_registro.csv`: una línea por carcasa con la hora, la foto, la huella, la probabilidad y la decisión.

Pega debajo de `# --- PASO 4`:

```python
huella = hashlib.sha256(open(RUTA_MODELO, "rb").read()).hexdigest()[:12]
ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
with open("/data/mi_registro.csv", "w", newline="") as f:
    escritor = csv.writer(f)
    escritor.writerow(["hora", "foto", "huella_modelo", "probabilidad", "decision"])
    for _, c in llegan.iterrows():
        escritor.writerow([ahora, c["ruta"].split("/")[-1], huella, round(c["probabilidad"], 3), c["decision"]])
print(f"mi_registro.csv: {len(llegan)} líneas, modelo {huella}")
```

**Resultado esperado** (línea nueva; cambia la huella si reentrenaste el modelo):

```text
mi_registro.csv: 24 líneas, modelo aa2da58a4660
```

**Cómo se lee:** ábrelo en VS Code (`infra/data/mi_registro.csv`): una línea por carcasa. Si mañana alguien reclama por una pieza, este fichero dice qué probabilidad le dio el modelo, qué decidió el puesto y **qué modelo exacto** estaba instalado. Es lo que verás en el M07 y el M08 con el nombre de [trazabilidad](../glosario/05-operacion-gobierno.md#trazabilidad).

### 5 — Decide tú: el tamaño de la zona de duda

**Para qué:** elegir cuántas carcasas manda el puesto a una persona, sabiendo lo que se gana.

**Qué ocurre:** pruebas `DUDA = 0.05`, `DUDA = 0.1` y `DUDA = 0.2`, y miras las líneas del paso 3.

**Resultado esperado** (líneas del paso 3 con cada valor):

```text
# DUDA = 0.05
{'aceptar': 13, 'dudosa': 4, 'revisar': 7}
rayones aceptados=2  buenas mandadas a revisar=0
# DUDA = 0.1
{'aceptar': 11, 'dudosa': 9, 'revisar': 4}
rayones aceptados=1  buenas mandadas a revisar=0
# DUDA = 0.2
{'dudosa': 22, 'aceptar': 1, 'revisar': 1}
rayones aceptados=0  buenas mandadas a revisar=0
```

**Cómo se lee:** | Zona de duda | Dudosas (a una persona) | Rayones aceptados |
|--------------|-------------------------|-------------------|
| ninguna | 0 de 24 | 3 |
| ± 0,05 | 4 de 24 | 2 |
| ± 0,1 | 9 de 24 | 1 |
| ± 0,2 | 22 de 24 | 0 |

Cuanto más ancha es la zona, **menos rayones se escapan**, porque las carcasas en las que el modelo dudaba van a una persona. Pero con ± 0,2 el puesto manda a revisar casi todo: ya no automatiza nada. El tamaño se elige con dos números que no da el modelo: **cuántas carcasas puede revisar el turno** y **cuánto cuesta un rayón que llega al cliente**. Con este modelo, que duda tanto, la mejora de verdad es un modelo más seguro, como la red del M04-04. Vuelve a dejar `DUDA = 0.0`.
## Reto

Los dos retos se hacen con tu puesto de «Constrúyelo tú», añadiendo un bloque al final.

### 1 — Quién decide la zona de duda

**La situación:** calidad te da sus números: un rayón que llega al cliente cuesta **500 €**; que una persona revise una carcasa dudosa cuesta **5 €**; y el turno solo puede revisar **10 de cada 24** carcasas que llegan.

**Qué haces:** escribes un bucle que, para varias zonas de duda (0, 0,05, 0,1 y 0,2), cuente las dudosas y los rayones aceptados, calcule el coste y diga si las dudosas caben en el turno.

**Pistas:** la misma decisión del paso 3, pero con `duda` como variable del bucle; `coste = 500 × rayones + 5 × dudosas`; «cabe» si las dudosas no pasan de 10.

**Lo que buscas:** la zona de duda más barata que cabe en el turno.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: elegir la zona de duda con los costes y la capacidad del turno
COSTE_RAYON, COSTE_PERSONA, CAPACIDAD = 500, 5, 10       # € por rayón aceptado, € por dudosa, dudosas que caben en el turno
print("duda  dudosas  rayones_aceptados  coste   cabe_en_el_turno")
for duda in (0.0, 0.05, 0.1, 0.2):
    dec = ["dudosa" if abs(p - UMBRAL) < duda else "revisar" if p >= UMBRAL else "aceptar" for p in llegan["probabilidad"]]
    dudosas = dec.count("dudosa")
    rayones = sum(d == "aceptar" and r == 1 for d, r in zip(dec, llegan["defecto"]))
    coste = COSTE_RAYON * rayones + COSTE_PERSONA * dudosas
    print(f"{duda:4.2f}  {dudosas:7d}  {rayones:17d}  {coste:5d} €  {'sí' if dudosas <= CAPACIDAD else 'NO'}")
```

```text
duda  dudosas  rayones_aceptados  coste   cabe_en_el_turno
0.00        0                  3   1500 €  sí
0.05        4                  2   1020 €  sí
0.10        9                  1    545 €  sí
0.20       22                  0    110 €  NO
```

**La más barata es ± 0,2, pero no cabe en el turno**: 22 dudosas de 24. La más barata que cabe es **± 0,1**: 545 €, un rayón aceptado y 9 dudosas. **La regla:** el umbral y la zona de duda no los decide quien entrena el modelo, sino calidad y producción, con el coste de cada error y la capacidad real del turno. Tu trabajo es darles esta tabla.

</details>

### 2 — Una carcasa sin foto

**La situación:** la cámara falla un instante y una carcasa llega al puesto sin foto. Prueba qué hace tu puesto:

```python
print(probabilidad("/data/imagenes/no_existe.png"))
```

```text
FileNotFoundError: [Errno 2] No such file or directory: '/data/imagenes/no_existe.png'
```

El puesto entero se para con un error. En planta, eso detiene la línea o, peor, alguien lo cambia para que «siga adelante» y la carcasa pasa sin inspeccionar.

**Qué haces:** haces que el puesto trate una carcasa sin foto como una decisión más: mandarla a revisar, con el motivo.

**Pistas:** `try:` … `except FileNotFoundError:` captura el error de un fichero que no existe; devuelve `None` como probabilidad y, al decidir, convierte `None` en `"revisar (sin foto)"`.

**Lo que buscas:** que una carcasa sin foto vaya a revisión y que una normal se siga decidiendo igual.

<details>
<summary>Ver solución</summary>

```python
# Reto 2: una carcasa llega sin foto
def probabilidad_segura(ruta):
    try:
        return probabilidad(ruta)
    except FileNotFoundError:
        return None                                     # sin foto no hay probabilidad

def decidir_seguro(p):
    return "revisar (sin foto)" if p is None else decidir(p)

for ruta in ["/data/imagenes/buenas/ok_30.png", "/data/imagenes/no_existe.png"]:
    print(ruta.split("/")[-1], "->", decidir_seguro(probabilidad_segura(ruta)))
```

```text
ok_30.png -> aceptar
no_existe.png -> revisar (sin foto)
```

**La regla:** cuando falta un dato, el puesto no se para ni acepta: decide lo prudente, que es revisar, y lo deja escrito con su motivo en el registro. Una carcasa sin dictamen nunca debe pasar como buena.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el registro no tiene una fila por imagen` | el lote no se copió | repite `m04-03` |
| `FALLO: ninguna pieza fue a revisión` | el modelo no se cargó bien | lanza antes `m04-01` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/modelo_vision.joblib` | no has entrenado el modelo de visión | lanza `lab m04-01` |

## Conclusiones

### Qué es un puesto de inspección

Es el flujo completo: **entra la foto de cada pieza y sale una decisión con su registro**. No se entrena nada: se usa el modelo que ya existe.

```
 cámara ──▶ lote_entrada/ ──▶ modelo ──▶ probabilidad ──▶ umbral ──▶ aceptar / revisar ──▶ lote_resultado.csv
```

### Cómo debe ser el registro

| Requisito | En `lote_resultado.csv` |
|-----------|-------------------------|
| Una fila por pieza | 6 fotos, 6 filas |
| La decisión y su motivo | Decisión y probabilidad de defecto |
| Sin pieza sin dictamen | Si falta la foto, la pieza no se acepta |

### El papel del umbral

| Imagen | Probabilidad | Decisión | ¿Correcta? |
|--------|--------------|----------|------------|
| `ok_00.png` – `ok_02.png` | 0,27 – 0,35 | aceptar | Sí |
| `ko_00.png` | **0,493** | aceptar | **No: defecto que se escapa** |
| `ko_01.png`, `ko_02.png` | 0,66 – 0,71 | revisar | Sí |

Con el umbral en 0,5, una pieza defectuosa pasa. Con 0,4, se habría parado, y las buenas seguirían pasando.

### Cómo se decide el umbral

- No lo decide el modelo: lo decide **calidad**, según qué error cuesta más, si dejar pasar un defecto o revisar una pieza buena.
- Se revisa con **datos reales** del puesto, contando cuántos defectos se escapan y cuántas piezas buenas se paran con cada umbral.
- Las piezas **dudosas** (cerca del umbral) pueden ir a una revisión manual en lugar de decidirse solas.

### En una frase

> 🔑 Ningún modelo es perfecto: el umbral es una decisión de calidad sobre qué error se acepta, y tiene que estar escrita.
