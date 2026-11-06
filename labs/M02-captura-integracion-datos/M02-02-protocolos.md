# M02-02 — Integración mediante protocolos industriales

[← Página anterior](M02-01-telemetria.md) · [Siguiente página →](M02-03-preparacion-datos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **integrar mediante protocolos industriales**: cómo se accede al mismo dato por [MQTT](../glosario/01-datos-arquitectura.md#mqtt), [OPC-UA](../glosario/01-datos-arquitectura.md#opcua) y [Modbus](../glosario/01-datos-arquitectura.md#modbus), qué te cuenta cada uno, cómo se detecta un error de integración que no da ningún fallo, y cómo se construye una [pasarela](../glosario/01-datos-arquitectura.md#pasarela) que traduce un protocolo a otro.

### Prerrequisitos

- `mosquitto` y `sensor` en marcha; en este lab se añaden `opcua` y `modbus`.
- Puertos 4840 y 1502 libres. RAM conjunta ~0,7 GB.
- Dos terminales en `infra/` para la mejora.

### Qué está pasando

En una planta, la misma máquina se lee de varias formas según quién pregunte. El [SCADA](../glosario/01-datos-arquitectura.md#scada) la lee por **OPC-UA**. Un PLC antiguo o un equipo de otro fabricante solo habla **Modbus**. La plataforma de datos recibe los registros por **MQTT**. Integrar es conseguir que todos cuenten lo mismo.

Aquí los tres caminos exponen la misma estación:

| Protocolo | Cómo se pide el dato | Qué te devuelve |
|-----------|----------------------|-----------------|
| MQTT | Te suscribes al [tema](../glosario/01-datos-arquitectura.md#tema) `linea/est01/ciclo` | El registro entero, en JSON, con nombres |
| OPC-UA | Navegas hasta el objeto `Estacion` y lees sus variables | El valor con su nombre y su tipo |
| Modbus | Lees registros por su número | Enteros sin nombre ni unidad |

Con Modbus, el significado de cada registro y su escala vienen en el **manual del equipo**, no en el dato. No hay tres sensores: `opcua` y `modbus` leen el mismo estado que escribe la estación (`infra/data/estado.json`). El puerto Modbus del laboratorio es el 1502, no el 502 habitual en planta.

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Servidor OPC-UA del PLC o del SCADA | Contenedor `opcua`, código en `infra/linea/opcua_server.py` |
| PLC o equipo con Modbus TCP | Contenedor `modbus`, código en `infra/linea/modbus_server.py` |
| Manual con el [mapa de registros](../glosario/01-datos-arquitectura.md#mapa-registros) | La tabla de este lab, sacada del código |
| Pasarela de protocolos en el [edge](../glosario/01-datos-arquitectura.md#edge) | El comando `lab pasarela` (en la mejora) |

### 1 — Abrir las otras dos puertas

**Qué ocurre:** arrancas el servidor OPC-UA y el esclavo Modbus. Hasta que no escuchan, no hay nada que integrar.

```bash
# Servidor OPC-UA (4840) y esclavo Modbus TCP (1502)
docker compose up -d opcua modbus

docker compose ps opcua modbus --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
```

**Resultado esperado:**

```text
SERVICE   STATUS         PORTS
modbus    Up 5 seconds   0.0.0.0:1502->1502/tcp, [::]:1502->1502/tcp
opcua     Up 5 seconds   0.0.0.0:4840->4840/tcp, [::]:4840->4840/tcp
```

### 2 — OPC-UA por dentro

**Qué ocurre:** primero miras cómo está construido el servidor, y después lo lees como lo haría un cliente.

Abre `infra/linea/opcua_server.py` en VS Code. El servidor declara un objeto y sus variables:

```python
obj = await server.nodes.objects.add_object(idx, "Estacion")    # el objeto «Estacion»
temp = await obj.add_variable(idx, "Temperatura", 0.0)          # variables con nombre y tipo
vib = await obj.add_variable(idx, "Vibracion", 0.0)
cur = await obj.add_variable(idx, "Corriente", 0.0)
pieza = await obj.add_variable(idx, "Pieza", "P0000")
```

Ahora léelo como un cliente. No hay un cliente OPC-UA gráfico en el puesto, así que el curso trae un comando de ayuda, `lab opcua`, que se conecta, recorre el objeto `Estacion` y enseña cada variable:

```bash
docker compose --profile lab run --rm --no-deps lab opcua
```

📋 Ficha del comando [`opcua`](../comandos-lab.md#opcua).

**Resultado esperado** (cambian los valores):

```text
nodo                  valor          tipo
Estacion.Temperatura  62.33          Double
Estacion.Vibracion    0.265          Double
Estacion.Corriente    4.06           Double
Estacion.Pieza        P0123          String
OK opcua: 4 variables en el objeto Estacion
```

**Cómo se lee:** el cliente no necesita ningún documento: el servidor le dice qué variables hay, cómo se llaman y de qué tipo son. Es lo que hace un SCADA al «descubrir» un equipo OPC-UA.

### 3 — Modbus por dentro

**Qué ocurre:** lees los registros del esclavo Modbus en crudo con el comando de ayuda `lab modbus`, que hace de cliente Modbus.

```bash
# Lee los registros 0 a 3
docker compose --profile lab run --rm --no-deps lab modbus
```

📋 Ficha del comando [`modbus`](../comandos-lab.md#modbus).

**Resultado esperado:**

```text
registro  valor_crudo
       0          630
       1          220
       2          403
       3          125
OK modbus: 4 registros leídos desde el 0
```

**Cómo se lee:** cuatro enteros. Nada dice qué son. Para saberlo hay que abrir el «manual», que aquí es `infra/linea/modbus_server.py`:

```python
bloque.setValues(1, [
    int(round(estado["temperatura_c"] * 10)),     # registro 0: temperatura × 10
    int(round(estado["vibracion_mm_s"] * 1000)),  # registro 1: vibración × 1000
    int(round(estado["corriente_a"] * 100)),      # registro 2: corriente × 100
    int(estado["secuencia"]) % 10000,             # registro 3: secuencia de la estación
])
```

| Registro | Valor crudo | Escala | Valor real |
|----------|-------------|--------|------------|
| 0 | 630 | ÷ 10 | 63,0 °C |
| 1 | 220 | ÷ 1000 | 0,22 mm/s |
| 2 | 403 | ÷ 100 | 4,03 A |
| 3 | 125 | — | carcasa 125 |

Modbus solo transporta enteros: por eso los decimales se guardan multiplicando por 10, 100 o 1000.

### 4 — Comprobar que los tres cuentan lo mismo

**Qué ocurre:** usas un comando de ayuda que, en el mismo instante, lee la temperatura del estado de la estación, del nodo OPC-UA y del registro Modbus 0 (aplicando la escala), y comprueba que cuadran.

```bash
docker compose --profile lab run --rm --no-deps lab m02-02
```

📋 Ficha del comando [`m02-02`](../comandos-lab.md#m02-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambia la temperatura; los tres valores quedan a menos de 1,5 °C):

```text
estado=63.22 opcua=63.22 modbus=63.2
OK m02-02: MQTT, OPC-UA y Modbus leen la misma temperatura
```

**Cómo se lee:** OPC-UA da los dos decimales; Modbus, uno, porque el registro guarda décimas. Integrar bien es saber que 63,2 y 63,22 son la misma lectura con distinta precisión.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
# OPC-UA: se navega por nombres (objeto Estacion → variable Temperatura)
nodo = await estacion.get_child([f"{indice}:Temperatura"])
opc = float(await nodo.read_value())

# Modbus: se lee un registro por número y se aplica la escala
rr = cliente.read_holding_registers(0, 4, slave=1)
modbus_c = rr.registers[0] / 10        # 632 → 63,2 °C
```

</details>

## Comprueba tu entendimiento

**La escala**

Si el registro 2 devuelve 411, ¿qué corriente es?

→ 4,11 A. El registro 2 guarda centésimas de amperio.

## Investiga: el mapa completo de registros

**Qué ocurre:** un esclavo Modbus tiene más registros de los que usas. Lees los doce primeros para ver qué más expone.

```bash
# Desde el registro 0, doce registros
docker compose --profile lab run --rm --no-deps lab modbus 0 12
```

**Resultado esperado:**

```text
registro  valor_crudo
       0          680
       1          250
       2          411
       3          297
       4            0
       5            0
       6            0
       7            0
       8            0
       9            0
      10            0
      11            0
OK modbus: 12 registros leídos desde el 0
```

**Cómo se lee:** del 0 al 3, las señales de la estación. Del 4 al 11, ceros. Pero no todos los ceros significan lo mismo: el comentario de `modbus_server.py` dice que **el registro 10 es el paro de seguridad**. Un cero en el registro 10 es «paro en reposo»; un cero en el 7 es «registro sin uso». Sin el manual, son idénticos.

## Experimenta: preguntar frente a recibir

**Qué ocurre:** MQTT te **avisa** cuando hay una carcasa nueva. Con Modbus, tienes que **preguntar** cada vez. Lees el registro 3 (la secuencia) tres veces seguidas, con medio segundo entre lecturas.

```bash
for i in 1 2 3; do
  docker compose --profile lab run --rm --no-deps lab modbus 3 1 | grep -v OK
  sleep 0.5
done
```

**Resultado esperado:** la secuencia sube en algunas lecturas y se repite o salta en otras.

**Cómo se lee:** si preguntas más rápido de lo que la estación fabrica, lees dos veces la misma carcasa; si preguntas más despacio, te saltas alguna. Con Modbus, quien integra tiene que decidir **cada cuánto preguntar**, igual que hace [Prometheus](../glosario/02-observabilidad.md#prometheus) con sus muestras (M01-03). Con MQTT, cada carcasa llega una vez.

## Mejora: una pasarela Modbus → MQTT

**Qué ocurre:** en planta, una **pasarela** (un equipo edge o un programa) lee los equipos que solo hablan Modbus y publica sus datos en MQTT, **ya con nombre y unidad**. Así, el resto de sistemas no tiene que conocer el mapa de registros. El comando `lab pasarela` hace de pasarela durante unos segundos.

En la **terminal 2**, escucha el tema donde publicará la pasarela:

```bash
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/pasarela' -v
```

En la **terminal 1**, lanza la pasarela 10 segundos:

```bash
# Lee los registros 0-3 cada segundo, aplica el mapa y publica en linea/est01/pasarela
docker compose --profile lab run --rm --no-deps lab pasarela 10
```

📋 Ficha del comando [`pasarela`](../comandos-lab.md#pasarela).

**Resultado esperado** en la terminal 2:

```text
linea/est01/pasarela {"fuente": "modbus", "ts": "2026-11-06T02:32:06+00:00", "temperatura_c": 62.0, "vibracion_mm_s": 0.265, "corriente_a": 4.03, "secuencia": 3}
linea/est01/pasarela {"fuente": "modbus", "ts": "2026-11-06T02:32:07+00:00", "temperatura_c": 62.4, "vibracion_mm_s": 0.28, "corriente_a": 4.13, "secuencia": 4}
...
```

**Cómo se lee:** lo que salió del equipo como cuatro enteros llega a MQTT como un JSON con nombres, en grados y con hora. El mapa de registros se aplica **una sola vez**, en la pasarela, y nadie más tiene que conocerlo. Es el componente que en el M01 dijimos que la estación simulada lleva dentro.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_pasarela</code>)</summary>

```python
for _ in range(segundos):
    rr = mb.read_holding_registers(0, 4, slave=1)          # pregunta al PLC por Modbus
    mensaje = {
        "fuente": "modbus",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "temperatura_c": rr.registers[0] / 10,              # el mapa de registros, aplicado aquí
        "vibracion_mm_s": rr.registers[1] / 1000,
        "corriente_a": rr.registers[2] / 100,
        "secuencia": rr.registers[3],
    }
    cliente.publish("linea/est01/pasarela", json.dumps(mensaje))   # y lo publica en MQTT
    time.sleep(1)
```

</details>

## Constrúyelo tú: tu propia pasarela Modbus → MQTT

**Qué está pasando:** en «Mejora» lanzaste una pasarela ya hecha con `lab pasarela`. Ahora la escribes tú: lees los registros del autómata en crudo, les aplicas el mapa de registros, compruebas que cuentan lo mismo que el MQTT de la estación y publicas el resultado con nombres y unidades. Al final la conviertes en un bucle que pregunta cada cierto tiempo, y eliges ese tiempo: es la decisión central de cualquier integración por Modbus.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que tu código llega al autómata antes de escribir nada.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m02_02_mi_pasarela.py`](../../infra/construye/m02_02_mi_pasarela.py). Arriba están las **decisiones**: el `MAPA` de registros (el mismo de «Investiga»), `PERIODO_S` y `LECTURAS`. Debajo, el paso 1 ya escrito: abre una conexión Modbus TCP con el contenedor `modbus`. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_02_mi_pasarela.py
```

**Resultado esperado:**

```text
Modbus conectado: True
```

**Cómo se lee:** `True`: hay conexión con el autómata. Modbus no pide usuario ni contraseña: basta con llegar al puerto. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Leer los registros en crudo

**Para qué:** ver exactamente lo que da el autómata, sin interpretar nada.

**Qué ocurre:** pides los registros 0 a 3 y los enseñas tal cual llegan: números enteros, sin nombre ni unidad.

Pega debajo de `# --- PASO 2`:

```python
def leer_crudo():
    respuesta = plc.read_holding_registers(0, 4, slave=1)      # 4 registros desde el 0
    return respuesta.registers

crudo = leer_crudo()
print("registros 0-3 en crudo:", crudo)
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (línea nueva; cambian los números):

```text
registros 0-3 en crudo: [611, 235, 397, 931]
```

**Cómo se lee:** cuatro enteros. Sin el mapa no se sabe que 621 son 62,1 °C ni que el último es la secuencia: el protocolo no lo dice. Es la diferencia con OPC-UA, que entrega cada variable con nombre y tipo.

### 3 — Aplicar el mapa de registros

**Para qué:** convertir números sin significado en señales con nombre y unidad.

**Qué ocurre:** recorres el `MAPA`: para cada registro, su nombre y su escala. Divides el valor crudo por la escala y guardas el resultado con su nombre.

Pega debajo de `# --- PASO 3`:

```python
def interpretar(crudo):
    return {nombre: crudo[registro] / escala for registro, (nombre, escala) in MAPA.items()}

senales = interpretar(crudo)
print("con el mapa:", senales)
```

**Resultado esperado** (línea nueva; cambian los números):

```text
con el mapa: {'temperatura_c': 61.1, 'vibracion_mm_s': 0.235, 'corriente_a': 3.97, 'secuencia': 931.0}
```

**Cómo se lee:** ahora sí: grados, milímetros por segundo, amperios y el número de carcasa (sale con decimal, `931.0`, porque la división siempre da un número con decimales). Toda la integración depende de que este mapa esté bien; un error aquí no da ningún fallo, solo números falsos (lo pruebas en el reto 1).

### 4 — Comprobar contra el MQTT de la estación

**Para qué:** saber si lo que lees por Modbus es lo mismo que publica la estación por MQTT.

**Qué ocurre:** escuchas una carcasa en `linea/est01/ciclo`, lees el autómata justo después y comparas las dos temperaturas.

Pega debajo de `# --- PASO 4`:

```python
llegado = []
oyente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
oyente.on_message = lambda c, d, m: llegado.append(json.loads(m.payload))
oyente.connect("mosquitto", 1883)
oyente.subscribe("linea/est01/ciclo")
oyente.loop_start()
while not llegado:                       # espera a que llegue una carcasa
    time.sleep(0.1)
oyente.loop_stop()
por_modbus = interpretar(leer_crudo())
print(f"MQTT:   {llegado[0]['pieza_id']}  {llegado[0]['temperatura_c']} °C")
print(f"Modbus: secuencia {por_modbus['secuencia']:.0f}  {por_modbus['temperatura_c']} °C")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
MQTT:   P0932  61.3 °C
Modbus: secuencia 932  61.3 °C
```

**Cómo se lee:** la misma carcasa (el número de la pieza coincide con la secuencia) y la misma temperatura. Fíjate en que por Modbus la temperatura tiene **un solo decimal**: el registro guarda la temperatura × 10 en un entero, así que si la estación mide 62,06 °C, por Modbus llega 62,0. Si alguna vez la secuencia no coincide, es que la estación terminó otra carcasa entre las dos lecturas.

### 5 — Publicar en MQTT con nombres y unidades

**Para qué:** dejar el dato listo para cualquier consumidor, sin que tenga que conocer el mapa.

**Qué ocurre:** creas el cliente MQTT de la pasarela y publicas en `linea/est01/pasarela` un registro con la hora, el origen (`modbus`) y las señales ya convertidas.

Pega debajo de `# --- PASO 5`:

```python
salida = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
salida.connect("mosquitto", 1883)
salida.loop_start()

def publicar(senales):
    registro = {"fuente": "modbus", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **senales}
    salida.publish("linea/est01/pasarela", json.dumps(registro)).wait_for_publish()
    return registro

print("publicado:", json.dumps(publicar(por_modbus)))
```

**Resultado esperado** (línea nueva; cambian los números):

```text
publicado: {"fuente": "modbus", "ts": "2026-11-06T14:38:40+00:00", "temperatura_c": 61.3, "vibracion_mm_s": 0.25, "corriente_a": 4.07, "secuencia": 932.0}
```

**Cómo se lee:** un registro que cualquiera entiende: dice de dónde viene, cuándo y qué es cada número. Es lo que hace una pasarela en planta: traducir un protocolo de máquina a uno que use el resto de sistemas.

### 6 — El bucle de la pasarela

**Para qué:** convertir la lectura suelta en un servicio que pregunta sin parar, y medir cuánto aprovecha cada pregunta.

**Qué ocurre:** preguntas `LECTURAS` veces, una cada `PERIODO_S`. Solo publicas si la secuencia ha cambiado, es decir, si hay carcasa nueva. Cuentas las lecturas repetidas (misma carcasa que la anterior) y las carcasas saltadas (la secuencia avanzó más de uno).

Pega debajo de `# --- PASO 6`:

```python
publicadas = repetidas = saltadas = 0
ultima = None
for _ in range(LECTURAS):
    senales = interpretar(leer_crudo())
    secuencia = int(senales["secuencia"])
    if secuencia == ultima:
        repetidas += 1                                  # preguntaste y no había nada nuevo
    else:
        if ultima is not None and secuencia > ultima + 1:
            saltadas += secuencia - ultima - 1          # hubo carcasas que no llegaste a leer
        publicar(senales)
        publicadas += 1
        ultima = secuencia
    time.sleep(PERIODO_S)
salida.loop_stop()
print(f"cada {PERIODO_S} s: lecturas={LECTURAS} publicadas={publicadas} repetidas={repetidas} carcasas_saltadas={saltadas}")
```

**Resultado esperado** (línea nueva; cambian los números):

```text
cada 1.0 s: lecturas=10 publicadas=10 repetidas=0 carcasas_saltadas=0
```

**Cómo se lee:** preguntando cada segundo, al ritmo de la estación, cada lectura trae una carcasa nueva. Como el ciclo varía alrededor de 1 s, en otra ejecución puede salir alguna repetida o saltada. Por MQTT no pasa: la estación avisa cuando hay carcasa. Por Modbus, eres tú quien decide cada cuánto preguntar.

### 7 — Decide tú: preguntar más deprisa o más despacio

**Para qué:** elegir el periodo de lectura sabiendo lo que se gana y lo que se pierde.

**Qué ocurre:** pruebas `PERIODO_S = 0.3` y después `PERIODO_S = 2.5`, con `LECTURAS = 20`, y comparas la última línea.

**Resultado esperado** (última línea de cada prueba; cambian los números):

```text
cada 0.3 s: lecturas=20 publicadas=7 repetidas=13 carcasas_saltadas=0
cada 2.5 s: lecturas=20 publicadas=20 repetidas=0 carcasas_saltadas=29
```

**Cómo se lee:** cada 0,3 s, **13 de 20 preguntas no traen nada nuevo**: cargas al autómata y a la red para nada. Cada 2,5 s, **se escapan 29 carcasas** en 50 s: no las ves nunca. Ningún periodo da justo una lectura por carcasa, porque el ciclo de la máquina varía. Es la diferencia entre preguntar (Modbus) y recibir (MQTT) de «Experimenta». Vuelve a dejar `PERIODO_S = 1.0` y `LECTURAS = 10`.
## Reto

Los dos retos usan tu pasarela de «Constrúyelo tú» o un script del mismo directorio.

### 1 — La escala olvidada

**La situación:** un integrador copia el mapa de registros de memoria y se olvida de que la temperatura viene multiplicada por 10.

**Qué haces:** en tu pasarela, cambias la escala del registro 0 en el `MAPA`, de `("temperatura_c", 10)` a `("temperatura_c", 1)`, y ejecutas. Mira la línea `publicado:`. Después, haz que la pasarela **se niegue** a publicar un valor imposible: añade al final del fichero una función que compruebe, antes de publicar, que cada señal está dentro de lo físicamente posible.

**Pistas:** un diccionario `RANGOS = {"temperatura_c": (0, 150), …}` con el mínimo y el máximo de cada señal; recorrerlo con `for nombre, (minimo, maximo) in RANGOS.items()`; si una señal no cumple `minimo <= valor <= maximo`, imprimir un aviso y no llamar a `publicar`.

**Lo que buscas:** saber si una escala mal puesta da algún error, y conseguir que tu pasarela lo detecte.

<details>
<summary>Ver solución</summary>

Con la escala olvidada:

```text
publicado: {"fuente": "modbus", "ts": "2026-11-06T14:40:22+00:00", "temperatura_c": 626.0, "vibracion_mm_s": 0.28, "corriente_a": 4.03, "secuencia": 1034.0}
```

**626 °C publicados sin ningún error.** Para la pasarela es un número válido; el primer síntoma llegaría mucho después, en un panel o en un modelo que aprende que el husillo trabaja a 600 °C.

La comprobación, al final del fichero:

```python
RANGOS = {"temperatura_c": (0, 150), "vibracion_mm_s": (0, 5), "corriente_a": (0, 20)}   # lo físicamente posible

def publicar_si_es_posible(senales):
    for nombre, (minimo, maximo) in RANGOS.items():
        if not minimo <= senales[nombre] <= maximo:
            print(f"RECHAZADO: {nombre}={senales[nombre]} fuera de {minimo}-{maximo}; revisa el mapa de registros")
            return None
    return publicar(senales)

publicar_si_es_posible(interpretar(leer_crudo()))
```

```text
RECHAZADO: temperatura_c=611.0 fuera de 0-150; revisa el mapa de registros
```

Con la escala bien puesta no imprime nada y publica. **La regla:** una pasarela no puede saber si el mapa está bien, pero sí si el resultado es posible. Comprobar rangos en la entrada es la defensa más barata contra un error de integración silencioso. Vuelve a poner la escala 10 y quita el bloque del reto.

</details>

### 2 — Variables que se pueden escribir

**La situación:** en `infra/linea/opcua_server.py`, las variables de la estación se declaran con `await nodo.set_writable()`. Un SCADA lee esas variables para enseñarlas en pantalla.

**Qué haces:** ejecutas el script [`infra/construye/m02_02_escribir_opcua.py`](../../infra/construye/m02_02_escribir_opcua.py). Léelo antes: se conecta al servidor OPC-UA sin usuario ni contraseña, escribe 999 en la variable `Temperatura` y la vuelve a leer justo después y un segundo después.

```bash
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_02_escribir_opcua.py
```

**Lo que buscas:** saber si un cliente cualquiera puede cambiar lo que ve el SCADA, y cuánto dura el cambio.

<details>
<summary>Ver solución</summary>

```text
antes de escribir: 61.01
justo después:     999.0
un segundo después: 61.31
```

**Ha podido escribir**, sin [autenticarse](../glosario/05-operacion-gobierno.md#autenticacion). Durante ese instante, un SCADA que leyera la variable enseñaría 999 °C. Aquí dura menos de medio segundo porque el servidor del laboratorio vuelve a escribir el valor real dos veces por segundo; en un servidor que solo actualiza cuando cambia el proceso, el valor falso se quedaría.

**La regla:** las variables que reflejan el proceso deben ser **de solo lectura** para los clientes; solo se dejan escribir las que son órdenes ([consignas](../glosario/05-operacion-gobierno.md#consigna)), y con usuarios y permisos. Lo evaluarás en el M08-01.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: OPC-UA: …` | El servidor no arrancó | `docker compose logs opcua` |
| `FALLO: Modbus no conecta` | El esclavo no está en marcha | `docker compose up -d modbus` |
| La terminal 2 no recibe nada de la pasarela | La suscripción se abrió con otro tema | Copia el tema `linea/est01/pasarela` tal cual |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `Modbus conectado: False` | el contenedor `modbus` está parado | `docker compose up -d modbus` |
| el paso 4 se queda esperando | no llegan carcasas por MQTT: la estación está parada | `docker compose start sensor` |

## Conclusiones

### Qué es integrar con protocolos industriales

Conseguir que los sistemas que leen una misma magnitud obtengan el mismo valor, venga por el protocolo que venga. Cada protocolo cuenta más o menos sobre el dato:

| Protocolo | Lo que te dice el dato | Lo que tienes que saber tú |
|-----------|------------------------|----------------------------|
| MQTT (JSON) | Nombres, valores, hora | El tema |
| OPC-UA | Nombre, valor, tipo | Dónde está el servidor |
| Modbus | Un entero | Qué registro es, qué escala tiene y qué significa |

### Cómo debe ser una integración fiable

| Requisito | En el lab |
|-----------|-----------|
| Los caminos dan el mismo valor | `m02-02`: diferencia de menos de 1,5 °C |
| El mapa de registros está documentado | La tabla del paso 3, sacada del código |
| La traducción se hace una vez | La pasarela publica ya en grados |
| Se sabe qué no se debe escribir | El registro 10, el paro de seguridad |

### Sus riesgos y cómo los has visto

| Riesgo | Cómo lo has visto | Qué provoca |
|--------|-------------------|-------------|
| Escala olvidada | Reto 1: 630 en lugar de 63,0 | Un dato falso que no da error |
| Ceros que no significan lo mismo | Investiga: registro 10 frente a registro 7 | Confundir «paro en reposo» con «sin uso» |
| Preguntar a destiempo | Experimenta: secuencias repetidas o saltadas | Muestras duplicadas o perdidas |
| Variables escribibles | Reto 2: `set_writable()` | Cualquiera podría falsear lo que ve el SCADA |

### Cómo se mejora

- **Pasarela** que lee el equipo y publica con nombre y unidad (lo has hecho).
- **OPC-UA** cuando el equipo lo permite, con usuarios y variables de solo lectura.
- **Mapa de registros** bajo control de versiones, junto al código de la pasarela.
- **Solo lectura** hacia [OT](../glosario/01-datos-arquitectura.md#ot) para los sistemas de datos.

### En una frase

> 🔑 Integrar no es solo conectarse: es garantizar que todos leen el mismo dato, con la misma unidad, y que nadie puede tocar lo que no debe.
