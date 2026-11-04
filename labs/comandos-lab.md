# Fichas de los comandos `lab`

[← Volver al índice del curso](../README.md)

En los laboratorios, muchas comprobaciones se lanzan así:

```bash
docker compose --profile lab run --rm --no-deps lab m01-01
```

| Parte | Qué significa |
|-------|---------------|
| `docker compose run` | Arranca un contenedor para hacer **una tarea** y terminar |
| `--profile lab` | El servicio `lab` está oculto tras un perfil; esto lo activa |
| `--rm` | Borra el contenedor al terminar |
| `--no-deps` | No arranca otros servicios: usa los que ya estén en marcha |
| `lab` | El contenedor con Python, las librerías y el código del curso |
| `m01-01` | **Qué comprobación ejecuta**: una de las fichas de esta página |

Por dentro, `lab m01-01` ejecuta `python -m linea.cli m01-01`, es decir, la función `cmd_m01_01` de [`infra/linea/cli.py`](../infra/linea/cli.py). Todo lo que lee o escribe en `/data` aparece en `infra/data/` de tu equipo.

Cada ficha dice qué hace el comando en palabras, qué necesita en marcha, qué lee, qué deja escrito y cuándo da `OK` o `FALLO`. Debajo de cada una, el código comentado de su función (extracto: se omite lo que no cambia el sentido, marcado con `...`).

Funciones de apoyo que usan varias fichas:

```python
def ok(codigo, detalle):           # imprime "OK <paso>: …" y termina con código 0
    print(f"OK {codigo}: {detalle}")
    return 0

def fallo(mensaje):                # imprime "FALLO: …" y termina con código 1
    print(f"FALLO: {mensaje}")
    return 1

def consumir(topic, timeout=20):   # se suscribe a un tema MQTT y devuelve el primer mensaje (o None)
    ...

def esperar_filas(minimo=1, timeout=25):  # SELECT COUNT(*) FROM lecturas en historial.sqlite,
    ...                                   # repitiendo hasta que haya "minimo" filas o pase el tiempo

def leer_estado():                 # lee data/estado.json: lo último que escribió la estación
    ...

def _partir(df):                   # ordena por pieza_id y corta: 70 % entrenamiento, 30 % examen
    df = df.sort_values("pieza_id")
    corte = int(len(df) * 0.7)
    return df.iloc[:corte], df.iloc[corte:]

def _tasas(y_real, y_pred):        # matriz de confusión y sus dos tasas
    tn, fp, fn, tp = confusion_matrix(y_real, y_pred, labels=[0, 1]).ravel()
    recall = tp / (tp + fn)        # defectos encontrados / defectos reales
    fpr = fp / (fp + tn)           # falsas alarmas / piezas buenas
    ...
```

---

## M01 — Arquitectura y supervisión

### m01-01

**Qué hace:** comprueba que el registro de una pieza recorre los tres tramos (origen, transporte y almacén) y que no se pierde.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `archivador` |
| Lee | `historial.sqlite` (cuenta los registros guardados) · el tema MQTT `linea/est01/ciclo` (espera un registro hasta 15 s) · `estado.json` (lo último que la estación dice haber fabricado) |
| Escribe | Nada |
| `OK` si | Hay registros en el histórico, llega uno por MQTT y es de la misma estación y de una pieza cercana a la del estado |
| `FALLO` si | El histórico está vacío tras 25 s · no llega ningún registro por MQTT · el registro y el estado no cuadran |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m01_01</code>)</summary>

```python
def cmd_m01_01(_args):
    # ALMACÉN: cuenta los registros de historial.sqlite; espera hasta 25 s a que haya al menos 1
    n = esperar_filas(1)
    if n < 1:
        return fallo("el archivador no tiene ciclos; ¿están mosquitto, sensor y archivador en marcha?")

    # TRANSPORTE: se suscribe a linea/est01/ciclo y espera un registro hasta 15 s
    payload = consumir(TOPIC_CICLO, 15)
    if not payload:
        return fallo("no llega ningún ciclo por MQTT")
    ciclo = json.loads(payload)                 # el registro es un JSON

    # ORIGEN: lo último que la estación escribió en estado.json
    estado = leer_estado()
    # mismo pieza_id, o como mucho 2 piezas de diferencia
    if ciclo["pieza_id"] != estado["pieza_id"] and abs(ciclo["secuencia"] - estado["secuencia"]) > 2:
        return fallo("el ciclo MQTT y el estado en disco no son de la misma estación")

    print(json.dumps({"mqtt": ciclo, "archivadas": n}))
    return ok("m01-01", f"ciclo {ciclo['pieza_id']} archivado; total={n}")
```

</details>

Se usa en [M01-01](M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md).

### m01-02

**Qué hace:** comprueba que el panel del turno responde y cuenta, directamente en el histórico, cuántas lecturas pasan de 70 °C.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `archivador`, `panel` |
| Lee | La página del panel (`http://panel:8501`) · las temperaturas de `historial.sqlite` |
| Escribe | Nada |
| `OK` si | El panel contesta sin error y hay al menos 2 registros en el histórico |
| `FALLO` si | El panel no responde o el histórico tiene menos de 2 registros |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m01_02</code>)</summary>

```python
def cmd_m01_02(_args):
    n = esperar_filas(2)                         # hacen falta al menos 2 registros para pintar una serie
    if n < 2:
        return fallo("hace falta histórico para el panel")

    respuesta = httpx.get(PANEL_URL, timeout=30)  # pide la página del panel (http://panel:8501)
    if respuesta.status_code >= 400:
        return fallo(f"el panel contestó {respuesta.status_code}")

    # cuenta en el histórico las lecturas por encima del margen (70 °C)
    df = pd.read_sql_query("SELECT temperatura_c FROM lecturas", con)
    fuera = int((df["temperatura_c"] > UMBRAL_TEMPERATURA).sum())

    print(f"panel_http={respuesta.status_code} lecturas={len(df)} fuera_de_margen={fuera} umbral={UMBRAL_TEMPERATURA}")
    return ok("m01-02", f"panel vivo, {len(df)} lecturas, {fuera} fuera de 70 C")
```

</details>

Se usa en [M01-02](M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md).

---

## M02 — Captura, integración y preparación de datos

### m02-01

**Qué hace:** se suscribe al tema de la estación, como haría cualquier sistema que quiere enterarse de cada pieza, y comprueba que el registro trae los campos necesarios.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor` |
| Lee | El tema MQTT `linea/est01/ciclo` (espera un registro hasta 15 s) |
| Escribe | Nada |
| `OK` si | Llega un registro con `pieza_id`, `temperatura_c`, `vibracion_mm_s` y `ts` |
| `FALLO` si | No llega nada o falta algún campo |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m02_01</code>)</summary>

```python
def cmd_m02_01(_args):
    payload = consumir(TOPIC_CICLO, 15)          # se suscribe y espera un registro hasta 15 s
    if not payload:
        return fallo("no hay telemetría")
    ciclo = json.loads(payload)

    # el registro tiene que traer, como mínimo, estos campos
    for campo in ("pieza_id", "temperatura_c", "vibracion_mm_s", "ts"):
        if campo not in ciclo:
            return fallo(f"falta {campo}")

    print(json.dumps(ciclo))
    return ok("m02-01", f"evento {ciclo['pieza_id']} en {TOPIC_CICLO}")
```

</details>

Se usa en [M02-01](M02-captura-integracion-datos/M02-01-telemetria.md).

### m02-01-pausa

**Qué hace:** escucha el tema durante 3 segundos con la estación parada. Comprueba que el silencio es silencio y que nada inventa lecturas.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, con `sensor` **parado** |
| Lee | El tema MQTT `linea/est01/ciclo` durante 3 s |
| Escribe | Nada |
| `OK` si | **No** llega ningún registro |
| `FALLO` si | Llega algún registro (la estación no estaba parada o hay otra publicando) |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m02_01_pausa</code>)</summary>

```python
def cmd_m02_01_pausa(_args):
    payload = consumir(TOPIC_CICLO, 3)           # escucha solo 3 segundos
    if payload:                                  # al revés que m02-01: aquí llegar algo es el error
        return fallo("seguían llegando ciclos con el sensor parado")
    return ok("m02-01-pausa", "hueco: ningún ciclo en 3 s")
```

</details>

Se usa en [M02-01](M02-captura-integracion-datos/M02-01-telemetria.md).

### m02-02

**Qué hace:** lee la temperatura del husillo por los tres caminos (el estado que publica MQTT, el nodo OPC-UA y el registro Modbus) y comprueba que dicen lo mismo.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `opcua`, `modbus` |
| Lee | `estado.json` · nodo OPC-UA `Estacion` → `Temperatura` · registro Modbus 0, dividido entre 10 |
| Escribe | Nada |
| `OK` si | OPC-UA y Modbus quedan a menos de 1,5 °C del estado |
| `FALLO` si | OPC-UA o Modbus no responden, o el valor no cuadra (por ejemplo, si no se divide entre 10) |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m02_02</code>)</summary>

```python
def cmd_m02_02(_args):
    estado = leer_estado()                       # la temperatura que publica la estación

    # OPC-UA: se conecta al servidor y navega por nombre: Estacion → Temperatura
    async with Client(url=OPCUA_ENDPOINT) as client:
        ...                                      # busca el objeto "Estacion"
        nodo = await estacion.get_child([f"{indice}:Temperatura"])
        opc = float(await nodo.read_value())

    # Modbus: se conecta al esclavo y lee registros por número (no por nombre)
    cliente = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    rr = cliente.read_holding_registers(0, 4, slave=1)   # registros 0 a 3 del esclavo 1
    modbus_c = rr.registers[0] / 10                      # registro 0 en décimas: 632 → 63,2 °C

    print(f"estado={estado['temperatura_c']} opcua={opc:.2f} modbus={modbus_c:.1f}")
    # los dos tienen que quedar a menos de 1,5 °C de lo que dice la estación
    if abs(opc - estado["temperatura_c"]) > 1.5:
        return fallo("OPC-UA no coincide con el estado")
    if abs(modbus_c - estado["temperatura_c"]) > 1.5:
        return fallo("Modbus no coincide con el estado (¿falta la escala /10?)")
    return ok("m02-02", "MQTT, OPC-UA y Modbus leen la misma temperatura")
```

</details>

Se usa en [M02-02](M02-captura-integracion-datos/M02-02-protocolos.md).

### m02-03

**Qué hace:** genera un histórico de 800 piezas con los problemas típicos de planta (huecos, valores en décimas y sensores clavados en 9999), lo limpia y cuenta lo que se descarta.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Nada: el histórico lo genera el propio comando |
| Escribe | `crudo.csv` (tal cual) · `limpio.csv` (una fila por pieza, en grados) · `imposibles.csv` (los 9999). Los sobrescribe si ya existían |
| `OK` si | En el limpio hay una fila por pieza, todas las temperaturas están entre 40 y 120 °C y se apartaron los 9999 |
| `FALLO` si | Quedan piezas repetidas, temperaturas sin escalar o no se apartó ningún 9999 |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m02_03</code>)</summary>

```python
def cmd_m02_03(_args):
    # genera 800 piezas con huecos, décimas y 9999, y las guarda tal cual
    crudo = escribir_crudo(DATA / "crudo.csv")
    # limpia: quita huecos, divide las décimas, aparta los 9999 en imposibles.csv
    resumen = limpiar(crudo, DATA / "limpio.csv")
    limpio = pd.read_csv(DATA / "limpio.csv")

    # comprobaciones sobre el resultado limpio
    if resumen["piezas_unicas"] != len(limpio):
        return fallo("siguen duplicadas las piezas")             # una fila por pieza
    if limpio["temperatura_c"].max() > 120 or limpio["temperatura_c"].min() < 40:
        return fallo("la temperatura limpia no está en grados")  # ni 614 ni 9999
    if (DATA / "imposibles.csv").stat().st_size == 0:
        return fallo("no se apartaron los 9999")

    print(json.dumps(resumen))
    return ok("m02-03", f"crudo={resumen['filas_crudo']} limpio={resumen['filas_limpias']} huecos={resumen['huecos']}")
```

</details>

Se usa en [M02-03](M02-captura-integracion-datos/M02-03-preparacion-datos.md).

---

## M03 — Predicción y anomalías

### m03-01

**Qué hace:** entrena un modelo de regresión logística que relaciona las señales de cada pieza con el defecto que marcó calidad. Entrena con el 70 % más antiguo y lo examina con el 30 % más reciente.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `limpio.csv` (si falta, lo genera como `m02-03`) |
| Escribe | `modelo_logreg.joblib` |
| `OK` si | Encuentra al menos el 45 % de los defectos del tramo de examen |
| `FALLO` si | Encuentra menos del 45 % |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m03_01</code>)</summary>

```python
FEATURES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]   # entradas del modelo

def cmd_m03_01(_args):
    df = pd.read_csv(DATA / "limpio.csv")         # si no existe, antes lo genera como m02-03
    train, test = _partir(df)                     # ordena por pieza: 70 % antiguo / 30 % reciente

    # regresión logística; "balanced" da más peso a la clase rara (defecto)
    modelo = LogisticRegression(class_weight="balanced", max_iter=400)
    modelo.fit(train[FEATURES], train["defecto"])     # aprende: señales → defecto (0/1)
    pred = modelo.predict(test[FEATURES])             # predice las piezas recientes

    tasas = _tasas(test["defecto"], pred)             # tp, fp, fn, tn, recall y fpr
    print(json.dumps(tasas))
    if tasas["recall"] < 0.45:
        return fallo(f"recall de defecto demasiado bajo ({tasas['recall']:.2f})")

    joblib.dump(modelo, DATA / "modelo_logreg.joblib")   # guarda el modelo en disco
    return ok("m03-01", f"recall_defecto={tasas['recall']:.2f} falsas_alarmas={tasas['fpr']:.2f}")
```

</details>

Se usa en [M03-01](M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md).

### m03-02

**Qué hace:** aprende cómo es un ciclo normal con piezas sin defecto. Después revisa 200 ciclos nuevos, 20 de ellos con la vibración subida a propósito, y cuenta cuántos de esos 20 avisa.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Nada: genera sus propios ciclos normales (400) y los 200 de vigilancia |
| Escribe | `detector_anomalia.joblib` |
| `OK` si | Avisa al menos el 70 % de los ciclos alterados |
| `FALLO` si | Avisa menos del 70 % |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m03_02</code>)</summary>

```python
def cmd_m03_02(_args):
    base = generar_limpio(400, seed=3)            # 400 piezas propias de referencia
    normal = base[base["defecto"] == 0]           # solo las sanas: así es «lo normal»
    vig = vigilancia()                            # 200 ciclos nuevos, 20 con vibración subida

    escala = StandardScaler()                     # cada señal en su escala (media 0, desviación 1)
    base_z = escala.fit_transform(normal[FEATURES])
    detector = EmpiricalCovariance().fit(base_z)  # aprende cómo varían juntas las señales

    # distancia de Mahalanobis: cuánto se aleja cada ciclo de lo normal, con todas las señales a la vez
    distancias = detector.mahalanobis(escala.transform(vig[FEATURES]))
    marcas = np.where(distancias >= 13.3, -1, 1)  # -1 = aviso; 13,3 = percentil 99 con 4 señales

    # la columna "inyectada" solo se usa aquí, para contar aciertos
    raro = vig["inyectada"] == 1
    pillados = int(((marcas == -1) & raro).sum())
    total = int(raro.sum())
    print(f"inyectados={total} detectados={pillados}")
    if pillados / total < 0.7:
        return fallo("el detector no ve los ciclos inyectados")

    joblib.dump(detector, DATA / "detector_anomalia.joblib")
    return ok("m03-02", f"avisos sobre inyectados {pillados}/{total}")
```

</details>

Se usa en [M03-02](M03-ml-prediccion-anomalias/M03-02-anomalias.md).

### m03-03

**Qué hace:** entrena dos modelos candidatos (regresión logística y árbol de decisión) con las mismas piezas, elige uno con la regla acordada (más defectos encontrados y, si empatan, menos falsas alarmas) y lo deja listo para la línea.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `limpio.csv` |
| Escribe | `modelo_defecto.joblib` (el ganador) · `VERSION` (`defecto-0.1`) · `modelo_elegido.txt` (`arbol` o `logreg`) |
| `OK` si | Siempre que termine: no tiene umbral mínimo |
| `FALLO` si | Falta `limpio.csv` (sale un error de Python, no un `FALLO`) |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m03_03</code>)</summary>

```python
def cmd_m03_03(_args):
    df = pd.read_csv(DATA / "limpio.csv")
    train, test = _partir(df)                     # el mismo corte 70/30 para los dos

    candidatos = {
        "logreg": LogisticRegression(class_weight="balanced", max_iter=400),
        "arbol": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=7),
    }
    informe = {}
    for nombre, modelo in candidatos.items():
        modelo.fit(train[FEATURES], train["defecto"])
        informe[nombre] = _tasas(test["defecto"], modelo.predict(test[FEATURES]))
        informe[nombre]["modelo"] = modelo
    print(json.dumps(...))                        # las tasas de los dos

    # la regla: mayor recall; si empatan, menor tasa de falsas alarmas
    def clave(item):
        nombre, datos = item
        return (datos["recall"], -datos["fpr"])
    ganador, datos = max(informe.items(), key=clave)

    joblib.dump(datos["modelo"], DATA / "modelo_defecto.joblib")    # el modelo de la línea
    (DATA / "VERSION").write_text("defecto-0.1\n")                  # su versión
    (DATA / "modelo_elegido.txt").write_text(ganador + "\n")        # cuál ganó
    return ok("m03-03", f"elegido={ganador} recall={datos['recall']:.2f} fpr={datos['fpr']:.2f}")
```

</details>

Se usa en [M03-03](M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md). Los comandos de M06, M07 y M08 usan el modelo que deja.

---

## M04 — Visión

### m04-01

**Qué hace:** genera 80 fotos de carcasas (40 buenas y 40 con un rayón), entrena un modelo que las distingue y lo examina con fotos que no ha visto.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `imagenes/manifiesto.csv` (si falta, genera las fotos) |
| Escribe | `imagenes/buenas/*.png` · `imagenes/defectuosas/*.png` · `imagenes/manifiesto.csv` · `modelo_vision.joblib` |
| `OK` si | Acierta al menos el 85 % de las fotos de examen |
| `FALLO` si | Acierta menos del 85 % |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m04_01</code>)</summary>

```python
def _features_imagen(ruta):
    img = Image.open(ruta).convert("L").resize((16, 16))          # gris y 16×16 píxeles
    return np.asarray(img, dtype=np.float32).reshape(-1) / 255.0  # 256 números entre 0 y 1

def cmd_m04_01(_args):
    # genera las 80 fotos si no existen; separa 70 % de cada clase para entrenar y 30 % para examen
    modelo, _tabla, acierto = _entrenar_vision()
    #   dentro: X = una fila de 256 números por foto
    #           LogisticRegression(max_iter=400).fit(X, defecto)
    #           acierto = fotos de examen bien clasificadas / total de examen

    joblib.dump(modelo, DATA / "modelo_vision.joblib")
    print(f"acierto_prueba={acierto:.2f}")
    if acierto < 0.85:
        return fallo("el clasificador visual no separa las piezas")
    return ok("m04-01", f"acierto={acierto:.2f} en imágenes no usadas al entrenar")
```

</details>

Se usa en [M04-01](M04-vision-control-calidad/M04-01-clasificacion-componentes.md).

### m04-02

**Qué hace:** busca en 5 fotos defectuosas la fila donde está el rayón (la más brillante) y la compara con la fila real. Después mira 3 fotos buenas para ver si alguna tendría una fila igual de brillante.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Las fotos y `imagenes/manifiesto.csv` (si faltan, las genera) |
| Escribe | Nada |
| `OK` si | En las 5 defectuosas acierta la fila con un margen de 2 filas |
| `FALLO` si | Falla la fila en alguna defectuosa. Las buenas con marca se cuentan, pero no hacen fallar |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m04_02</code>)</summary>

```python
def _fila_brillante(ruta):
    img = np.asarray(Image.open(ruta).convert("L"), dtype=np.float32)
    return int(img.mean(axis=1).argmax())         # brillo medio de cada fila → la más clara

def cmd_m04_02(_args):
    tabla = pd.read_csv(DATA / "imagenes" / "manifiesto.csv")   # el manifiesto sabe la fila real del rayón
    malas = tabla[tabla["defecto"] == 1].head(5)
    buenas = tabla[tabla["defecto"] == 0].head(3)

    errores = 0
    for _, fila in malas.iterrows():              # ¿la fila más clara es la del rayón? (±2 filas)
        if abs(_fila_brillante(fila["ruta"]) - int(fila["y"])) > 2:
            errores += 1

    falsos = 0
    for _, fila in buenas.iterrows():             # en una buena, ninguna fila debería pasar de 230 de brillo
        img = np.asarray(Image.open(fila["ruta"]).convert("L"), dtype=np.float32)
        if img.mean(axis=1).max() > 230:
            falsos += 1

    print(f"errores_zona={errores} falsos_en_buenas={falsos}")
    if errores:                                   # solo fallan los errores de zona
        return fallo("la zona no cae sobre el rayón")
    return ok("m04-02", f"zona correcta en {len(malas)} defectos; buenas sin marca={falsos}")
```

</details>

Se usa en [M04-02](M04-vision-control-calidad/M04-02-deteccion-defectos.md).

### m04-03

**Qué hace:** simula el puesto de inspección. Copia 6 fotos (3 buenas y 3 malas) a una carpeta de entrada, da a cada una su probabilidad de defecto y deja un registro con `aceptar` o `revisar`.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_vision.joblib` (si falta, lo entrena como `m04-01`) · las fotos |
| Escribe | `lote_entrada/*.png` · `lote_resultado.csv` |
| `OK` si | Hay una fila por foto (6) y al menos una va a `revisar` |
| `FALLO` si | Faltan filas o ninguna pieza va a revisión |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m04_03</code>)</summary>

```python
def cmd_m04_03(_args):
    modelo = joblib.load(DATA / "modelo_vision.joblib")          # el de m04-01 (lo entrena si falta)
    lote = pd.concat([tabla[tabla.defecto == 0].head(3),          # 3 buenas
                      tabla[tabla.defecto == 1].head(3)])         # 3 malas

    filas = []
    for _, pieza in lote.iterrows():
        destino = DATA / "lote_entrada" / Path(pieza["ruta"]).name
        destino.write_bytes(Path(pieza["ruta"]).read_bytes())     # «llega la foto de la cámara»
        x = _features_imagen(destino).reshape(1, -1)
        proba = float(modelo.predict_proba(x)[0, 1])              # probabilidad de defecto
        dictamen = "aceptar" if proba < 0.5 else "revisar"        # umbral 0,5
        filas.append({"imagen": destino.name, "probabilidad_defecto": round(proba, 3), "decision": dictamen})

    salida = pd.DataFrame(filas)
    salida.to_csv(DATA / "lote_resultado.csv", index=False)      # el registro del puesto
    if len(salida) != 6:
        return fallo("el registro no tiene una fila por imagen")
    if not (salida["decision"] == "revisar").any():
        return fallo("ninguna pieza fue a revisión")
    print(salida.to_string(index=False))
    return ok("m04-03", f"registro={len(salida)} revisar={(salida.decision == 'revisar').sum()}")
```

</details>

Se usa en [M04-03](M04-vision-control-calidad/M04-03-inspeccion-camara.md).

---

## M05 — IA generativa

### m05-01

**Qué hace:** comprueba que el modelo de lenguaje del puesto está listo, le pide que diga «hola» y mide cuánto tarda.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | `http://llm:8088/salud` · la respuesta del modelo |
| Escribe | Nada |
| `OK` si | El servicio local responde y devuelve un texto no vacío |
| `FALLO` si | El servicio no responde o la respuesta llega vacía |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m05_01</code>)</summary>

```python
def _chat(contenido, sistema=None, max_tokens=60):
    # llamada HTTP al servicio local, con el formato de chat estándar
    mensajes = ([{"role": "system", "content": sistema}] if sistema else []) \
               + [{"role": "user", "content": contenido}]
    respuesta = httpx.post(f"{LLM_URL}/v1/chat/completions",
                           json={"messages": mensajes, "max_tokens": max_tokens}, timeout=180)
    return respuesta.json()["choices"][0]["message"]["content"].strip()

def cmd_m05_01(_args):
    salud = httpx.get(f"{LLM_URL}/salud", timeout=10)   # ¿está cargado el modelo? (http://llm:8088)
    t0 = time.time()
    texto = _chat("Responde exactamente: hola")         # una pregunta mínima
    dt = time.time() - t0                               # segundos que tardó
    print(f"respuesta={texto!r} segundos={dt:.1f} url={LLM_URL}")
    if not texto:
        return fallo("respuesta vacía")
    return ok("m05-01", f"inferencia local en {dt:.1f}s via {LLM_URL}")
```

</details>

Se usa en [M05-01](M05-ia-generativa/M05-01-modelo-local.md).

### m05-02

**Qué hace:** hace de aplicación. Pide un texto al modelo por HTTP y luego llama a un servicio que no existe, para comprobar que el fallo se ve como un error de red.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | La respuesta de `http://llm:8088/v1/chat/completions` |
| Escribe | Nada |
| `OK` si | Hay respuesta del modelo y la llamada al servicio inexistente da error de red |
| `FALLO` si | La respuesta llega vacía o el servicio inexistente contesta |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m05_02</code>)</summary>

```python
def cmd_m05_02(_args):
    texto = _chat("Di solo la palabra estacion")   # la «aplicación» pide texto por HTTP
    print(f"aplicacion: {texto}")
    if not texto:
        return fallo("la aplicación no mostró respuesta")

    # ahora llama a un servicio que no existe: tiene que dar error de red, no un texto
    try:
        httpx.get("http://servicio-inexistente:9/salud", timeout=2)
    except httpx.HTTPError as exc:
        print(f"servicio caído: {type(exc).__name__}")   # p. ej. ConnectError
    else:
        return fallo("un host inventado no debía responder")
    return ok("m05-02", "la aplicación habla con el servicio local y avisa si no está")
```

</details>

Se usa en [M05-02](M05-ia-generativa/M05-02-integracion-aplicacion.md).

### m05-03

**Qué hace:** pregunta el par de apriete del tornillo de la brida. Primero busca el párrafo del procedimiento que más palabras comparte con la pregunta, y después pide al modelo que conteste usando solo ese párrafo.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | `linea/docs/procedimiento-est01.md` · la respuesta del modelo |
| Escribe | Nada |
| `OK` si | El párrafo encontrado contiene 12 y la respuesta del modelo también (lo intenta hasta 3 veces) |
| `FALLO` si | No encuentra el párrafo del par o el modelo no da el 12 en 3 intentos |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m05_03</code>)</summary>

```python
def _fragmento(pregunta):
    texto = Path("/opt/linea/docs/procedimiento-est01.md").read_text()
    partes = [p.strip() for p in texto.split("\n\n") if p.strip()]   # el documento en párrafos
    palabras = set(pregunta.lower().split())
    # RECUPERAR: el párrafo que más palabras comparte con la pregunta
    return max(partes, key=lambda p: len(palabras & set(p.lower().split())))

def cmd_m05_03(_args):
    pregunta = "¿A qué par de apriete se aprieta el tornillo de la brida?"
    fragmento = _fragmento(pregunta)
    print("fragmento:"); print(fragmento)
    if "12" not in fragmento:
        return fallo("el recuperador no encontró el párrafo del par")

    # GENERAR: el párrafo va dentro del mensaje, con la orden de no inventar.
    # Repite hasta 3 veces si la respuesta no contiene "12"
    texto = _chat_hasta(
        f"Texto:\n{fragmento}\n\nPregunta: {pregunta}\nResponde solo con el valor, por ejemplo 12 N·m.",
        "Usa únicamente el texto. No inventes otro número. Copia el 12.",
        "12",
    )
    print(f"respuesta={texto!r}")
    if "12" not in texto:
        return fallo("la respuesta no contiene el 12 del procedimiento")
    return ok("m05-03", "responde 12 a partir del procedimiento")
```

</details>

Se usa en [M05-03](M05-ia-generativa/M05-03-asistente-documentacion.md).

### m05-03-ausente

**Qué hace:** busca en el procedimiento un párrafo sobre el color del tornillo de recambio, un tema que el documento no trata.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`). **No llama al modelo** |
| Lee | `linea/docs/procedimiento-est01.md` |
| Escribe | Nada |
| `OK` si | El párrafo más parecido no habla de color ni de recambio, así que no hay nada que pasar al modelo |
| `FALLO` si | Aparece un párrafo sobre ese tema |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m05_03_ausente</code>)</summary>

```python
def cmd_m05_03_ausente(_args):
    # solo RECUPERAR: no se llama al modelo
    fragmento = _fragmento("color del tornillo de recambio")
    # si el párrafo más parecido hablara de color y recambio, el documento sí tendría el dato
    if "color" in fragmento.lower() and "recambio" in fragmento.lower():
        return fallo("no debería haber un párrafo de color")
    print("sin_dato: el procedimiento no habla del color del tornillo")
    return ok("m05-03-ausente", "no hay fragmento; no se inventa el dato")
```

</details>

Se usa en [M05-03](M05-ia-generativa/M05-03-asistente-documentacion.md). Comprueba la recuperación del documento, no lo que diría el modelo.

### m05-04

**Qué hace:** simula un agente con una única herramienta, `leer_estacion`. El código lee la temperatura actual, la apunta en una traza y pide al modelo una frase con ese número. Después rechaza una petición de escritura en el automatismo.

| | |
|--|--|
| Necesita en marcha | `llm`, `sensor` |
| Lee | `estado.json` · la respuesta del modelo |
| Escribe | `traza_agente.jsonl` (herramienta usada y valor leído) |
| `OK` si | La frase del modelo contiene el número leído (lo intenta hasta 3 veces) y queda la traza |
| `FALLO` si | El modelo cambia el número en los 3 intentos o no queda traza |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m05_04</code>)</summary>

```python
def cmd_m05_04(_args):
    # HERRAMIENTA leer_estacion: la llama el código, no el modelo
    estado = leer_estado()
    valor = estado["temperatura_c"]
    # TRAZA: qué herramienta se usó y qué devolvió
    traza.write_text(json.dumps({"herramienta": "leer_estacion", "temperatura_c": valor}) + "\n")

    # el modelo solo redacta la frase; tiene que copiar el número (hasta 3 intentos)
    buscado = f"{valor:.2f}"
    texto = _chat_hasta(
        f"La herramienta leer_estacion devolvió {buscado} °C. Responde una frase que contenga exactamente el número {buscado}.",
        "No cambies el número de la herramienta. Cópialo tal cual.",
        buscado,
    )
    print(f"agente: {texto}")
    if buscado not in texto and str(valor) not in texto:
        return fallo(f"la frase no incluye el valor medido {valor}")

    # ESCRITURA: no existe ninguna herramienta que escriba; la respuesta es un texto fijo
    print("escritura: No puedo modificar el automatismo: no existe una herramienta de escritura.")
    return ok("m05-04", f"usó leer_estacion={valor} y rechazó escribir")
```

</details>

Se usa en [M05-04](M05-ia-generativa/M05-04-agentes.md). El rechazo de escritura es un texto fijo del código: el agente no puede escribir porque no existe esa herramienta, no porque el modelo decida negarse.

---

## M06 — Edge e integración OT

### m06-01

**Qué hace:** carga el modelo de defecto desde el disco del puesto, dictamina la misma pieza 20 veces seguidas y calcula el tiempo medio por pieza. La primera predicción, que incluye la carga, no cuenta.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_defecto.joblib` · la primera pieza de `limpio.csv` |
| Escribe | Nada |
| `OK` si | Tarda menos de 200 ms por pieza |
| `FALLO` si | Falta el modelo o tarda 200 ms o más |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m06_01</code>)</summary>

```python
def cmd_m06_01(_args):
    if not (DATA / "modelo_defecto.joblib").exists():
        return fallo("falta el modelo; pasa antes por M03-03")
    modelo = joblib.load(DATA / "modelo_defecto.joblib")       # del disco, sin red
    fila = pd.read_csv(DATA / "limpio.csv").head(1)[FEATURES]  # una pieza

    modelo.predict_proba(fila)                    # calentamiento: la primera no se mide

    t0 = time.perf_counter()
    for _ in range(20):                           # 20 dictámenes seguidos
        modelo.predict_proba(fila)
    ms = (time.perf_counter() - t0) * 1000 / 20   # media en milisegundos

    print(f"ms_por_pieza={ms:.2f} fichero=modelo_defecto.joblib")
    if ms > 200:
        return fallo("la inferencia local va demasiado lenta para un ciclo")
    return ok("m06-01", f"{ms:.2f} ms por pieza, modelo en disco")
```

</details>

Se usa en [M06-01](M06-edge-integracion-ot/M06-01-inferencia-edge.md).

### m06-02

**Qué hace:** dictamina la pieza que acaba de salir de la estación, publica el dictamen como evento para el automatismo y comprueba que el paro de seguridad no se ha tocado.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `modbus` |
| Lee | `modelo_defecto.joblib` · `estado.json` (la presión se fija en 6 bar) · el tema `linea/est01/dictamen` · registro Modbus 10 |
| Escribe | Publica un evento en `linea/est01/dictamen` |
| `OK` si | El evento llega, es de la misma pieza y el registro 10 sigue en 0 |
| `FALLO` si | El evento no llega, es de otra pieza o el paro cambió |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m06_02</code>)</summary>

```python
def cmd_m06_02(_args):
    modelo = joblib.load(DATA / "modelo_defecto.joblib")
    estado = leer_estado()                        # la pieza que acaba de salir
    fila = pd.DataFrame([{"temperatura_c": estado["temperatura_c"],
                          "vibracion_mm_s": estado["vibracion_mm_s"],
                          "corriente_a": estado["corriente_a"],
                          "presion_bar": 6.0}])   # la presión no viaja en vivo: consigna nominal

    proba = float(modelo.predict_proba(fila)[0, 1])
    dictamen = "revisar" if proba >= 0.5 else "seguir"
    evento = {"pieza_id": estado["pieza_id"], "decision": dictamen, "probabilidad": round(proba, 3)}

    # hace de automatismo (se suscribe a linea/est01/dictamen) y de modelo (publica el evento)
    cliente.subscribe(TOPIC_DICTAMEN)
    cliente.publish(TOPIC_DICTAMEN, json.dumps(evento))
    ...                                           # espera hasta 10 s a recibirlo
    if "payload" not in recibido_mqtt:
        return fallo("el automatismo no recibió el dictamen")

    # el paro de seguridad (registro Modbus 10) solo se LEE
    paro = mb.read_holding_registers(10, 1, slave=1)
    if paro.isError() or paro.registers[0] != 0:
        return fallo("el registro de paro de seguridad cambió")

    print(json.dumps({"evento": recibido, "paro_seguridad": 0}))
    if recibido["pieza_id"] != estado["pieza_id"]:
        return fallo("el evento no es de esta pieza")
    return ok("m06-02", f"{recibido['pieza_id']} -> {recibido['decision']}; paro=0")
```

</details>

Se usa en [M06-02](M06-edge-integracion-ot/M06-02-integracion-ot.md).

---

## M07 — Operación y observabilidad

### m07-01

**Qué hace:** llama al servicio de inferencia como lo haría una aplicación de planta. Primero manda una pieza completa, `SRV0001`, y después una sin señales.

| | |
|--|--|
| Necesita en marcha | `api` |
| Lee | `http://api:8000/salud` · la respuesta de `POST /predecir` · la primera pieza de `limpio.csv` |
| Escribe | Lo escribe el servicio, no el comando: una línea en `predicciones.jsonl` |
| `OK` si | La respuesta trae la misma versión que `/salud` y la pieza sin señales se rechaza con un error |
| `FALLO` si | El servicio no está, la versión no coincide o acepta la pieza incompleta |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m07_01</code>)</summary>

```python
def cmd_m07_01(_args):
    salud = httpx.get(f"{API_URL}/salud", timeout=10).json()     # {"estado": "ok", "version": "defecto-0.1"}

    # una pieza completa: las señales de la primera fila de limpio.csv, como SRV0001
    cuerpo = _cuerpo("SRV0001", pd.read_csv(DATA / "limpio.csv").iloc[0])
    respuesta = httpx.post(f"{API_URL}/predecir", json=cuerpo, timeout=15)
    datos = respuesta.json()                      # dictamen, probabilidad, versión y hora
    print(json.dumps(datos))
    if datos["version"] != salud["version"]:
        return fallo("la versión de la respuesta no es la del servicio")

    # una pieza sin señales: el servicio tiene que rechazarla (código 4xx)
    incompleta = httpx.post(f"{API_URL}/predecir", json={"pieza_id": "X"}, timeout=15)
    if incompleta.status_code < 400:
        return fallo("aceptó una pieza sin señales")
    return ok("m07-01", f"version={datos['version']} dictamen={datos['dictamen']}")
```

</details>

Se usa en [M07-01](M07-mlops-observabilidad/M07-01-servicio-inferencia.md).

### m07-02

**Qué hace:** calcula qué parte de las piezas de examen mandaría el modelo a revisión con los datos tal cual (la base) y con esas mismas piezas 8 °C más calientes (la deriva).

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_defecto.joblib` · `limpio.csv` |
| Escribe | `seguimiento.json` (tasa base y tasa desplazada) |
| `OK` si | La tasa desplazada supera a la base en al menos 0,10 |
| `FALLO` si | No se aprecia la deriva |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m07_02</code>)</summary>

```python
def _tasa_alerta(modelo, df):
    proba = modelo.predict_proba(df[FEATURES])[:, 1]
    return float((proba >= 0.5).mean())           # fracción de piezas que irían a revisión

def cmd_m07_02(_args):
    modelo = joblib.load(DATA / "modelo_defecto.joblib")
    _, test = _partir(pd.read_csv(DATA / "limpio.csv"))   # las piezas de examen de M03
    base = _tasa_alerta(modelo, test)             # BASE: el proceso tal cual

    movido = test.copy()
    movido["temperatura_c"] = movido["temperatura_c"] + 8 # el husillo 8 °C más caliente
    deriva = _tasa_alerta(modelo, movido)         # DERIVA: el mismo modelo, otro proceso

    print(f"tasa_base={base:.2f} tasa_desplazada={deriva:.2f}")
    if deriva < base + 0.1:
        return fallo("no se ve la deriva al subir 8 °C")
    (DATA / "seguimiento.json").write_text(json.dumps({"tasa_base": base, "tasa_desplazada": deriva}))
    return ok("m07-02", f"base={base:.2f} desplazada={deriva:.2f}")
```

</details>

Se usa en [M07-02](M07-mlops-observabilidad/M07-02-monitorizacion.md).

---

## M08 — Seguridad y gobierno

### m08-01

**Qué hace:** imprime el inventario de servicios de la arquitectura con su puerto y su función, y las tres medidas de seguridad declaradas. Después lee el registro del paro de seguridad.

| | |
|--|--|
| Necesita en marcha | `modbus` |
| Lee | Registro Modbus 10 |
| Escribe | Nada |
| `OK` si | El paro de seguridad está en 0 |
| `FALLO` si | `modbus` no responde o el paro no está en 0 |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m08_01</code>)</summary>

```python
def cmd_m08_01(_args):
    mb = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    if not mb.connect():
        return fallo("modbus no disponible para el cruce OT")
    paro = mb.read_holding_registers(10, 1, slave=1)   # registro 10: paro de seguridad

    # INVENTARIO: lista fija de servicios definida en linea/config.py (no mira Docker)
    for servicio in SERVICIOS:
        print(f"  {servicio['nombre']} puerto={servicio['puerto'] or '-'} — {servicio['para']}")

    # MEDIDAS: textos fijos; el comando NO comprueba que se cumplan
    medidas = {
        "dato": "el histórico y el procedimiento se quedan en el volumen local; no hay URL externa",
        "modelo": "el fichero joblib y el GGUF están en disco y la respuesta lleva versión",
        "acceso": "los puertos del laboratorio solo se publican en localhost del puesto",
    }
    for clave, texto in medidas.items():
        print(f"medida_{clave}: {texto}")

    if paro.isError() or paro.registers[0] != 0:
        return fallo("el paro de seguridad no está en reposo")
    return ok("m08-01", "inventario escrito; paro de seguridad en 0")
```

</details>

Se usa en [M08-01](M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md). El inventario y las medidas son textos fijos del código: **no comprueba** que se cumplan. Comprobarlo es el ejercicio del lab.

### m08-02

**Qué hace:** simula una auditoría. Dictamina `AUD0007`, cambia el fichero `VERSION` a `defecto-0.2` sin reiniciar el servicio, dictamina `AUD0008` y comprueba en el registro que las dos piezas conservan la versión que de verdad contestó.

| | |
|--|--|
| Necesita en marcha | `api` |
| Lee | Las respuestas de `POST /predecir` · `predicciones.jsonl` |
| Escribe | Cambia `VERSION` a `defecto-0.2` y, al terminar bien, la devuelve a su valor. El servicio añade dos líneas a `predicciones.jsonl` |
| `OK` si | Las dos piezas aparecen en el registro con la versión original |
| `FALLO` si | Falta alguna pieza o cambió la versión. Si falla, `VERSION` puede quedarse en `defecto-0.2` |

<details>
<summary>Código (<code>infra/linea/cli.py</code>, función <code>cmd_m08_02</code>)</summary>

```python
def cmd_m08_02(_args):
    cuerpo = _cuerpo("AUD0007", pd.read_csv(DATA / "limpio.csv").iloc[10])
    primera = httpx.post(f"{API_URL}/predecir", json=cuerpo).json()   # dictamen de AUD0007

    version_vista = (DATA / "VERSION").read_text().strip()             # p. ej. defecto-0.1
    (DATA / "VERSION").write_text("defecto-0.2\n")                     # «alguien» cambia el fichero

    segunda = httpx.post(f"{API_URL}/predecir", json={**cuerpo, "pieza_id": "AUD0008"}).json()

    # AUDITORÍA: busca las dos piezas en el registro del servicio
    lineas = (DATA / "predicciones.jsonl").read_text().strip().splitlines()
    suyas = [json.loads(l) for l in lineas if json.loads(l)["pieza_id"] in {"AUD0007", "AUD0008"}]
    print(json.dumps(suyas))
    if len(suyas) < 2:
        return fallo("no hay rastro de las dos piezas")
    if any(item["version"] != version_vista for item in suyas):
        return fallo("el rastro cambió de versión sin reiniciar el servicio")
    if segunda["version"] != primera["version"]:
        return fallo("las dos llamadas no comparten la versión cargada al arrancar")

    print("asistencia: el dictamen recomienda seguir o revisar; no escribe el paro")
    (DATA / "VERSION").write_text(version_vista + "\n")                # deja el fichero como estaba
    return ok("m08-02", f"rastro de AUD0007 con version={primera['version']} aunque el fichero cambió")
```

</details>

Se usa en [M08-02](M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md).
