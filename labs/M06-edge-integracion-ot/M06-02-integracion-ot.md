# M06-02 — Integración con sistemas industriales

[← Página anterior](M06-01-inferencia-edge.md) · [Siguiente página →](M06-03-prediccion-actuacion.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **integra un modelo con los sistemas de planta ([OT](../glosario/01-datos-arquitectura.md#ot))**: cómo llega el [dictamen](../glosario/05-operacion-gobierno.md#dictamen) al automatismo, cómo debe ser esa frontera, qué riesgos tiene y cómo se protege el control de la máquina.

### Prerrequisitos

- mosquitto, sensor y modbus en marcha.
- El modelo de M03-03.

### Qué está pasando

Un dictamen que se queda en el equipo [edge](../glosario/01-datos-arquitectura.md#edge) no sirve de nada. Tiene que llegar al **automatismo de la línea**, que es quien desvía la carcasa a revisión o la deja seguir.

La forma de hacerlo es la misma que para los registros: el dictamen se publica como **evento** en el [broker](../glosario/01-datos-arquitectura.md#broker), en el [tema](../glosario/01-datos-arquitectura.md#tema) `linea/est01/dictamen`, y el automatismo está suscrito. Así el modelo no necesita conocer el PLC ni escribir en él.

Hay una línea que no se cruza nunca: el **paro de seguridad** (registro [Modbus](../glosario/01-datos-arquitectura.md#modbus) 10) lo decide el automatismo con sus propias protecciones. El modelo recomienda; no para la máquina. En este lab se comprueba que el paro sigue en 0 después de publicar.

La presión no viaja en el registro en vivo, así que el dictamen usa la [consigna](../glosario/05-operacion-gobierno.md#consigna) nominal de 6 bar.

### 1 — Asegurar la línea

Vas a comprobar que están en marcha el transporte, el origen y el automatismo simulado.

```bash
docker compose up -d mosquitto sensor modbus
```

### 2 — Escuchar el tema de dictámenes

Vas a abrir una segunda terminal que haga de automatismo: se queda escuchando los dictámenes que se publiquen.

```bash
# Terminal 2 (también en infra/): espera un dictamen y sale
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/dictamen' -v -C 1
```

Déjala esperando y vuelve a la primera terminal.

### 3 — Publicar el dictamen sin tocar el paro

Vas a dictaminar la pieza actual de la estación, publicar el resultado como evento y leer el registro de paro. OT lee eventos; no obedece a un modelo en el enclavamiento.

```bash
# Terminal 1
docker compose --profile lab run --rm --no-deps lab m06-02
```

📋 Ficha del comando [`m06-02`](../comandos-lab.md#m06-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** en la terminal 1 (cambia la pieza):

```text
{"evento": {"pieza_id": "P0048", "decision": "seguir", "probabilidad": 0.08}, "paro_seguridad": 0}
OK m06-02: P0048 -> seguir; paro=0
```

**Resultado esperado** en la terminal 2:

```text
linea/est01/dictamen {"pieza_id": "P0048", "decision": "seguir", "probabilidad": 0.08}
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
estado = leer_estado()                                   # la pieza actual
proba = modelo.predict_proba(fila)[0, 1]
dictamen = "revisar" if proba >= 0.5 else "seguir"
cliente.publish(TOPIC_DICTAMEN, json.dumps(evento))      # evento MQTT para el automatismo

paro = mb.read_holding_registers(10, 1, slave=1)         # solo se LEE el paro
if paro.registers[0] != 0:
    return fallo("el registro de paro de seguridad cambió")
```

</details>

## Comprueba tu entendimiento

**Evento completo**

¿La pieza del evento es una pieza real de la estación?

→ Sí: el `pieza_id` sale de `estado.json` en el momento del dictamen.

## Experimenta: un umbral mal puesto

**Qué ocurre:** el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) que convierte la probabilidad en `revisar` está en el código del modelo, no en el PLC. Vas a ponerlo en 0,05, como si alguien lo hubiera bajado «por precaución».

```bash
docker compose --profile lab run --rm --no-deps lab m06-02 umbral=0.05
```

**Resultado esperado:**

```text
{"evento": {"pieza_id": "P0072", "decision": "revisar", "probabilidad": 0.08}, "paro_seguridad": 0}
OK m06-02: P0072 -> revisar; paro=0
```

**Cómo se lee:** una carcasa normal, con un 8 % de probabilidad de defecto, va a **revisión**. Con ese umbral, **casi todas** irían. El automatismo desviaría la producción entera a un puesto de revisión que no da abasto. El modelo es el mismo; el cambio de una cifra en una configuración ha parado la línea en la práctica. Por eso el umbral se versiona y se cambia con el mismo cuidado que el modelo.

## Mejora: un dictamen que se pueda rastrear

**Qué ocurre:** el evento actual dice la pieza, la decisión y la probabilidad. Le falta **cuándo** se fabricó la pieza (para no confundirla con otra del mismo nombre, M01-01) y **qué versión del modelo** decidió. Lo añades en el código.

Abre `infra/linea/cli.py` en VS Code, busca la función `cmd_m06_02` y esta línea:

```python
    evento = {"pieza_id": estado["pieza_id"], "decision": dictamen, "probabilidad": round(proba, 3)}
```

Cámbiala por:

```python
    evento = {"pieza_id": estado["pieza_id"], "decision": dictamen, "probabilidad": round(proba, 3),
              "ts": estado["ts"], "version": (DATA / "VERSION").read_text().strip()}
```

No hace falta reiniciar nada: `lab` lee el código cada vez.

```bash
docker compose --profile lab run --rm --no-deps lab m06-02
```

**Resultado esperado:**

```text
{"evento": {"pieza_id": "P0145", "decision": "seguir", "probabilidad": 0.08, "ts": "2026-11-06T02:50:25+00:00", "version": "defecto-0.1"}, "paro_seguridad": 0}
OK m06-02: P0145 -> seguir; paro=0
```

**Cómo se lee:** ahora el automatismo, y cualquiera que escuche el tema, sabe **qué carcasa exacta** (pieza + hora) y **qué modelo** la dictaminó. Si mañana se reclama esa pieza, el dictamen se puede rastrear. Es la base de la [trazabilidad](../glosario/05-operacion-gobierno.md#trazabilidad) del M08-02.

## Constrúyelo tú: tu propio publicador de dictámenes

**Qué está pasando:** `lab m06-02` lee la carcasa actual, decide y publica el dictamen para el automatismo, sin tocar el paro. Ahora lo construyes tú, con la mejora del lab incorporada desde el principio: cada dictamen sale con su hora, la versión y la [huella](../glosario/05-operacion-gobierno.md#version-huella) del modelo. Al final lo pones a funcionar sobre varias carcasas seguidas, como funcionaría en la línea, y miras una suposición escondida en sus datos de entrada.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** saber exactamente qué modelo va a dictaminar, antes de que dictamine nada.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m06_02_mi_dictamen.py`](../../infra/construye/m06_02_mi_dictamen.py). Arriba están las **decisiones** (`UMBRAL`, `PRESION_BAR`, `CARCASAS`); debajo, el paso 1 ya escrito: carga el modelo del M03-03, su versión y su **huella**, un código calculado del propio fichero. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m06_02_mi_dictamen.py
```

**Resultado esperado:**

```text
modelo defecto-0.1, huella 69a897cdf955
```

**Cómo se lee:** la versión es la etiqueta que escribió `lab m03-03`; la huella cambia si cambia un solo byte del modelo. Las dos irán en cada dictamen. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Decidir sobre la carcasa actual

**Para qué:** obtener el dictamen de la carcasa que está ahora en la estación.

**Qué ocurre:** lees la última carcasa, montas la fila con las cuatro señales que espera el modelo y le pides la probabilidad de defecto. Con el `UMBRAL`, decides «seguir» o «revisar».

Pega debajo de `# --- PASO 2`:

```python
def dictaminar():
    e = leer()
    fila = pd.DataFrame([{"temperatura_c": e["temperatura_c"], "vibracion_mm_s": e["vibracion_mm_s"],
                          "corriente_a": e["corriente_a"], "presion_bar": PRESION_BAR}])
    p = float(modelo.predict_proba(fila)[0, 1])
    return {"pieza_id": e["pieza_id"], "decision": "revisar" if p >= UMBRAL else "seguir", "probabilidad": round(p, 3),
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "version": VERSION, "huella": HUELLA}

dictamen = dictaminar()
print("dictamen:", json.dumps(dictamen))
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (línea nueva; cambian la carcasa y la probabilidad):

```text
dictamen: {"pieza_id": "P2414", "decision": "seguir", "probabilidad": 0.08, "ts": "2026-11-06T15:04:11+00:00", "version": "defecto-0.1", "huella": "69a897cdf955"}
```

**Cómo se lee:** un dictamen completo: qué carcasa, qué decisión, con qué probabilidad, cuándo y con qué modelo. Es lo que en el lab añadiste en «Mejora» para que se pueda rastrear; aquí va desde el principio.

### 3 — Publicarlo para el automatismo

**Para qué:** entregar el dictamen al automatismo sin entrar en él.

**Qué ocurre:** conectas un cliente [MQTT](../glosario/01-datos-arquitectura.md#mqtt), te suscribes tú mismo al tema de dictámenes (para comprobar que llega, como haría el automatismo) y publicas el dictamen en `linea/est01/dictamen`.

Pega debajo de `# --- PASO 3`:

```python
recibidos = []
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.on_message = lambda c, d, m: recibidos.append(json.loads(m.payload))
cliente.connect("mosquitto", 1883)
cliente.subscribe("linea/est01/dictamen")
cliente.loop_start()
time.sleep(0.5)

def publicar(d):
    cliente.publish("linea/est01/dictamen", json.dumps(d)).wait_for_publish()

publicar(dictamen)
time.sleep(0.5)
print(f"recibido en linea/est01/dictamen: {recibidos[-1]['pieza_id']} -> {recibidos[-1]['decision']}")
```

**Resultado esperado** (línea nueva; cambia la carcasa):

```text
recibido en linea/est01/dictamen: P2414 -> seguir
```

**Cómo se lee:** el dictamen ha viajado por el broker como un evento más. El modelo **no conoce el autómata** ni escribe en él: publica, y quien esté suscrito decide qué hacer. Si el día de mañana cambia el autómata, tu código no cambia.

### 4 — Comprobar que el paro no se ha tocado

**Para qué:** demostrar que el modelo está fuera del control de seguridad de la máquina.

**Qué ocurre:** lees por Modbus el registro 10, el paro de seguridad, y compruebas que sigue a 0.

Pega debajo de `# --- PASO 4`:

```python
plc = ModbusTcpClient("modbus", port=1502)
plc.connect()
paro = plc.read_holding_registers(10, 1, slave=1).registers[0]
plc.close()
print(f"registro de paro de seguridad = {paro}", "(sin tocar)" if paro == 0 else "(¡CAMBIADO!)")
```

**Resultado esperado** (líneas nuevas):

```text
registro de paro de seguridad = 0 (sin tocar)
```

**Cómo se lee:** sigue a 0. Tu código ha leído el registro, no lo ha escrito: la frontera es que el modelo **publica una recomendación** y el automatismo **decide y actúa con sus propias protecciones**. Es la comprobación que hace `lab m06-02`.

### 5 — Dictaminar carcasas seguidas

**Para qué:** ver el publicador funcionando como en la línea, carcasa tras carcasa.

**Qué ocurre:** cada segundo, durante `CARCASAS` carcasas, dictaminas la que haya en la estación y lo publicas, sin repetir una carcasa ya dictaminada.

Pega debajo de `# --- PASO 5`:

```python
hechas = {dictamen["pieza_id"]}
while len(hechas) < CARCASAS + 1:
    d = dictaminar()
    if d["pieza_id"] not in hechas:                  # una carcasa nueva
        publicar(d)
        hechas.add(d["pieza_id"])
        print(f"{d['pieza_id']}: {d['decision']:7s} probabilidad={d['probabilidad']}")
    time.sleep(0.3)
cliente.loop_stop()
print(f"dictámenes publicados en esta ejecución: {len(recibidos)}")
```

**Resultado esperado** (líneas nuevas; cambian las carcasas):

```text
P2415: seguir  probabilidad=0.08
P2416: seguir  probabilidad=0.08
P2417: seguir  probabilidad=0.08
P2418: seguir  probabilidad=0.08
P2419: seguir  probabilidad=0.08
dictámenes publicados en esta ejecución: 6
```

**Cómo se lee:** un dictamen por carcasa nueva, ninguno repetido, y todas «seguir»: la estación trabaja bien. La probabilidad sale siempre 0,08 porque el modelo es un árbol: da la misma probabilidad a todas las carcasas que caen en la misma hoja. Si tienes abierto un `mosquitto_sub` sobre `linea/est01/dictamen`, los ves pasar en directo.

### 6 — Decide tú: la presión que nadie mide

**Para qué:** descubrir una suposición escondida en las entradas del modelo.

**Qué ocurre:** el modelo aprendió con cuatro señales, pero el registro de la estación no trae la presión: tu código pone siempre `PRESION_BAR = 6.0`, la nominal. Cambias a `PRESION_BAR = 5.6`, una presión baja pero posible, y ejecutas.

**Resultado esperado** (líneas del paso 5):

```text
P2423: revisar probabilidad=0.723
P2424: revisar probabilidad=0.723
P2425: revisar probabilidad=0.723
P2426: revisar probabilidad=0.723
P2427: revisar probabilidad=0.723
```

**Cómo se lee:** **todas las carcasas pasan a «revisar»**, con 0,72 de probabilidad, sin que haya cambiado nada en la estación: solo un número que pusiste tú. El árbol del M03-03 pregunta por la presión, y con 5,6 bar cae en una hoja de defecto. En la línea, el modelo decide con una presión [inventada](../glosario/04-ia-generativa.md#alucinacion): si la presión real bajara, no se enteraría, y si la nominal estuviera mal puesta, mandaría a revisar media producción. **La regla:** todas las entradas de un modelo en producción tienen que medirse en vivo; si una no se mide, o se quita del modelo o se instala el sensor. Vuelve a dejar `PRESION_BAR = 6.0`.
## Reto

### 1 — Que el automatismo compruebe el dictamen

**La situación:** el umbral que convierte la probabilidad en «revisar» está en tu código, no en el autómata. El autómata recibe un dictamen y lo aplica. Pero el broker no tiene [autenticación](../glosario/05-operacion-gobierno.md#autenticacion): cualquiera que llegue a él puede publicar un dictamen falso en `linea/est01/dictamen`.

**Qué haces:** en tu publicador, añades al final un bloque que hace de **automatismo prudente**: escucha 15 s los dictámenes que llegan y, para cada uno, comprueba que viene del modelo instalado (su huella) y que la decisión cuadra con la probabilidad y el umbral. Mientras escucha, publica tú un dictamen falso desde otra terminal:

```bash
docker compose exec mosquitto mosquitto_pub -t linea/est01/dictamen \
  -m '{"pieza_id": "P0001", "decision": "revisar", "probabilidad": 0.08}'
```

**Pistas:** `d.get("huella")` devuelve `None` si el mensaje no trae huella; la decisión esperada es `"revisar" if d["probabilidad"] >= UMBRAL else "seguir"`; publica antes de escuchar un dictamen legítimo con `publicar(dictaminar())` para tener con qué comparar.

**Lo que buscas:** que el automatismo distinga el dictamen de tu modelo del falso.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: el automatismo comprueba cada dictamen antes de hacerle caso
def coherente(d):
    if d.get("huella") != HUELLA:
        return "NO: el modelo no es el instalado"
    esperada = "revisar" if d["probabilidad"] >= UMBRAL else "seguir"
    return "sí" if d["decision"] == esperada else f"NO: con {d['probabilidad']} tocaba {esperada}"

recibidos.clear()
cliente.loop_start()
publicar(dictaminar())                                  # un dictamen legítimo, de tu modelo
time.sleep(15)                                          # mientras, publica el dictamen falso en otra terminal
cliente.loop_stop()
for d in recibidos:
    print(f"{d['pieza_id']}: {d['decision']:7s} p={d['probabilidad']}  ¿coherente? {coherente(d)}")
```

```text
P2486: seguir  p=0.08  ¿coherente? sí
P0001: revisar p=0.08  ¿coherente? NO: el modelo no es el instalado
```

El dictamen de tu modelo pasa; el falso **no trae la huella del modelo instalado** y se rechaza. Si el falso la copiara, todavía lo delataría la incoherencia: «revisar» con una probabilidad de 0,08.

**La regla:** el consumidor de un dictamen no debe aplicarlo a ciegas. Comprobar de dónde viene (la huella) y si es coherente (la probabilidad frente al umbral) cuesta unas líneas y frena tanto los errores como los mensajes falsos. La protección de verdad es que el broker exija autenticación, que verás en el M08-01.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el automatismo no recibió el dictamen` | mosquitto caído | `docker compose up -d mosquitto sensor modbus` |
| `FALLO: el registro de paro de seguridad cambió` | algo escribió el registro 10 | no debe ocurrir; `docker compose restart modbus` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/VERSION` | no hiciste el M03-03 | lanza `lab m03-03`, que deja el modelo y su versión |

## Conclusiones

### Qué es integrar el modelo con OT

Es hacer que el dictamen del modelo **llegue al automatismo** que actúa sobre la pieza. Aquí se publica como evento en el broker y el automatismo está suscrito:

```
 estado de la pieza ──▶ modelo ──▶ dictamen (seguir / revisar) ──▶ broker ──▶ automatismo ──▶ desvía o deja pasar
```

### Cómo debe ser la frontera

| Requisito | En el lab |
|-----------|-----------|
| El modelo no conoce el PLC ni escribe en él | Publica en `linea/est01/dictamen` |
| El dictamen identifica la pieza | Lleva `pieza_id`, decisión y probabilidad |
| El paro de seguridad no depende del modelo | El registro 10 siguió en 0 |
| El umbral es una decisión de proceso | Está en el código del modelo, no en el PLC |

### Sus riesgos

| Riesgo | Qué provoca |
|--------|-------------|
| El dictamen no llega | El automatismo tiene que decidir sin él (por seguridad, revisión) |
| Llega el dictamen de otra pieza | Se desvía la carcasa equivocada |
| Datos incompletos | La presión no viaja en vivo y se usa la consigna de 6 bar: el modelo no ve la presión real |
| El modelo actúa sobre el control | Un error de software pararía o arrancaría la máquina |

### Cómo se protege el control de la máquina

- El modelo **recomienda** por evento; el automatismo **decide** con sus propias protecciones.
- El paro y los enclavamientos van por su **camino determinista** (bus de campo), nunca por el broker.
- Cada dictamen lleva **la pieza a la que se refiere** y el automatismo comprueba que coincide.

### En una frase

> 🔑 El modelo recomienda; el automatismo decide con sus propias protecciones. Esa frontera no se cruza.
