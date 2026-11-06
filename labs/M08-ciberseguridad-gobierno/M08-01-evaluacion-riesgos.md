# M08-01 — Evaluación de riesgos

[← Página anterior](README.md) · [Siguiente página →](M08-02-gobierno-trazabilidad.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es una **evaluación de riesgos** de una solución de IA industrial: qué superficies expone, cómo deben definirse las medidas, cómo se comprueba que se cumplen y cómo se corrige lo que no.

### Prerrequisitos

- `modbus` en marcha, para leer el registro de paro.
- El inventario es el de [infra/README.md](../../infra/README.md).

### Qué está pasando

Antes de llevar esta solución a la red de la planta, el responsable de **ciberseguridad** pregunta: ¿qué estáis exponiendo, qué puede salir mal y qué habéis hecho para evitarlo?

Cada servicio que escucha en un puerto es una **superficie**: algo a lo que se puede llegar desde la red. Los más delicados son los que tocan la parte [OT](../glosario/01-datos-arquitectura.md#ot), como el esclavo [Modbus](../glosario/01-datos-arquitectura.md#modbus) que tiene el registro del paro de seguridad.

En este lab haces el inventario de superficies y dejas escrita una medida para cada tipo de riesgo: el dato, el modelo y el acceso. Y compruebas si lo que está escrito se cumple de verdad.

### 1 — Ver qué está expuesto

Vas a listar qué contenedores están en marcha y qué puertos publican en el puesto. No se protege lo que no está escrito.

```bash
docker compose ps --format 'table {{.Service}}\t{{.Ports}}'
```

**Resultado esperado** (depende de lo que tengas arrancado):

```text
SERVICE      PORTS
api          0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
archivador   0.0.0.0:9101->9101/tcp, [::]:9101->9101/tcp
modbus       0.0.0.0:1502->1502/tcp, [::]:1502->1502/tcp
mosquitto    0.0.0.0:1883->1883/tcp, [::]:1883->1883/tcp
opcua        0.0.0.0:4840->4840/tcp, [::]:4840->4840/tcp
sensor       0.0.0.0:9102->9102/tcp, [::]:9102->9102/tcp
```

`0.0.0.0` (y `[::]` en IPv6) significa que el puerto escucha en todas las interfaces del equipo, no solo en `localhost`. En una red de planta, cualquiera que llegue a ese equipo llegaría a esos servicios.

### 2 — Inventariar y mirar el paro

Vas a generar el inventario de superficies con una medida para cada riesgo, y a comprobar que el paro de seguridad sigue en reposo.

```bash
docker compose --profile lab run --rm --no-deps lab m08-01
```

📋 Ficha del comando [`m08-01`](../comandos-lab.md#m08-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
superficies:
  mosquitto puerto=1883 — transporte MQTT de los ciclos
  sensor puerto=9102 — origen: publica el estado de EST-01 (y sus métricas)
  archivador puerto=9101 — almacén SQLite de ciclos (y sus métricas)
  calidad puerto=- — inspección de calidad, con su propia base de datos
  opcua puerto=4840 — la misma señal, como servidor OPC-UA
  modbus puerto=1502 — la misma señal, como esclavo Modbus TCP
  panel puerto=8501 — indicadores del operario
  llm puerto=8088 — inferencia del modelo generativo, solo en M05
  api puerto=8000 — servicio de inferencia del clasificador, desde M07
  prometheus puerto=9090 — métricas y alertas de la arquitectura
medida_dato: el histórico y el procedimiento se quedan en el volumen local; no hay URL externa
medida_modelo: el fichero joblib y el GGUF están en disco y la respuesta lleva versión
medida_acceso: los puertos del laboratorio solo se publican en localhost del puesto
OK m08-01: inventario escrito; paro de seguridad en 0
```

## Investiga: quién puede escribir

**Qué ocurre:** el inventario dice qué escucha; ahora buscas **qué se puede escribir** y sin pedir permiso. Miras tres sitios.

**El [broker](../glosario/01-datos-arquitectura.md#broker).** Abre `infra/mosquitto/mosquitto.conf`:

```text
listener 1883
allow_anonymous true
```

Cualquiera que llegue al 1883 puede publicar en **cualquier tema**. Y entre los temas de la estación hay dos que **actúan** sobre ella (M06-03):

| Tema | Qué hace |
|------|----------|
| `linea/est01/dictamen` | Lo lee el automatismo para desviar o dejar pasar piezas |
| `linea/est01/consigna` | Cambia la refrigeración de la estación |
| `linea/est01/evento` | Provoca fallos en la simulación (solo existe en el laboratorio) |

**El servidor [OPC-UA](../glosario/01-datos-arquitectura.md#opcua).** En `infra/linea/opcua_server.py`, las variables se declaran con `await nodo.set_writable()`: cualquier cliente podría escribirlas y falsear lo que ve un [SCADA](../glosario/01-datos-arquitectura.md#scada).

**El esclavo Modbus.** Modbus TCP no tiene [autenticación](../glosario/05-operacion-gobierno.md#autenticacion): quien llegue al 1502 puede leer y **escribir** registros, incluido el 10, el paro de seguridad. En este laboratorio ningún componente lo escribe, pero el protocolo lo permitiría.

## Experimenta: actuar sin ser el modelo

**Qué ocurre:** publicas directamente en el broker una [consigna](../glosario/05-operacion-gobierno.md#consigna) de refrigeración, sin pasar por el modelo ni por `lab`, como lo haría cualquiera con acceso a la red.

```bash
# Terminal 2: mira la estación
docker compose logs -f --tail=0 sensor
```

```bash
# Terminal 1: una consigna publicada «a mano»
docker compose exec mosquitto mosquitto_pub -t 'linea/est01/consigna' -m '{"refrigeracion": 3, "origen": "desconocido"}'
```

**Resultado esperado** en la terminal 2:

```text
sensor-1  | sensor: consigna refrigeración pedida=3 aplicada=3
```

**Cómo se lee:** la estación ha cambiado su refrigeración por un mensaje que nadie ha autenticado. Lo que la protege es que **acepta solo niveles de 1 a 3** (M06-03): el daño posible está acotado por la máquina. Sin ese límite, cualquier mensaje en el broker sería una orden. Vuelve al nivel normal:

```bash
docker compose --profile lab run --rm --no-deps lab consigna 1
```

## Comprueba tu entendimiento

**La medida de acceso**

Compara `medida_acceso` con lo que viste en el paso 1.

→ No cuadra: el paso 1 enseña `0.0.0.0`, no `127.0.0.1`. La medida escrita no se está cumpliendo. Eso es justo lo que busca una evaluación de riesgos: la diferencia entre lo que se dice y lo que hay.

## Mejora: el broker, solo en el propio equipo

**Qué ocurre:** aplicas la medida de acceso al broker. Docker Compose lee automáticamente un fichero `docker-compose.override.yml` junto al principal y aplica sus cambios por encima, sin tocar el original.

Crea `infra/docker-compose.override.yml` en VS Code con este contenido (`!override` necesita Docker Compose 2.24 o superior; compruébalo con `docker compose version`):

```yaml
# Cambios locales sobre docker-compose.yml: el broker solo escucha en el propio equipo
services:
  mosquitto:
    ports: !override
      - "127.0.0.1:1883:1883"
```

Recrea el broker y comprueba:

```bash
docker compose up -d mosquitto
docker compose ps mosquitto --format 'table {{.Service}}\t{{.Ports}}'
```

**Resultado esperado:**

```text
SERVICE     PORTS
mosquitto   127.0.0.1:1883->1883/tcp
```

**Cómo se lee:** ya no aparece `0.0.0.0`: el broker solo acepta conexiones desde el propio equipo. Desde otro ordenador de la red, la conexión se rechaza. La medida `medida_acceso` empieza a ser verdad, al menos para el broker. Los contenedores de la línea siguen funcionando, porque hablan con el broker por dentro de la red de Docker. Recrea la estación y el archivador por si perdieron la conexión:

```bash
docker compose restart sensor archivador
```

Para volver a dejarlo como estaba, borra `infra/docker-compose.override.yml` y vuelve a lanzar `docker compose up -d mosquitto`.

## Constrúyelo tú: tu propio inventario de riesgos

**Qué está pasando:** en este lab has mirado a mano qué escucha cada servicio y quién puede escribir. Ahora escribes tú un programa que lo **comprueba**: recorre los servicios de la línea, mira si contestan, si el broker acepta a cualquiera, si el autómata se deja leer sin credenciales y si las variables OPC-UA se pueden escribir. Todo **sin cambiar nada**: solo lee. Al final convierte lo encontrado en una tabla de riesgos con su medida, y la vuelve a pasar después de la mejora del lab.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** tener la lista de lo que hay que revisar, que es el inventario del paso 2 del lab.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m08_01_mi_inventario.py`](../../infra/construye/m08_01_mi_inventario.py). El paso 1 ya está escrito: los servicios de la línea, cada uno con su nombre de contenedor y su puerto, y una lista vacía donde irás apuntando lo que encuentres. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m08_01_mi_inventario.py
```

**Resultado esperado:**

```text
servicios a revisar: 7
```

**Cómo se lee:** siete servicios. Un inventario empieza así: saber qué hay antes de decidir qué proteger. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**, desde dentro de la red de la línea.

### 2 — ¿Quién contesta?

**Para qué:** saber qué servicios están accesibles desde un programa cualquiera de la red.

**Qué ocurre:** intentas abrir una conexión a cada servicio, con un segundo de plazo, y apuntas si contesta.

Pega debajo de `# --- PASO 2`:

```python
def contesta(host, puerto):
    try:
        socket.create_connection((host, puerto), timeout=1).close()
        return True
    except OSError:
        return False

for nombre, (host, puerto) in SERVICIOS.items():
    print(f"{nombre:20s} {host}:{puerto}  {'CONTESTA' if contesta(host, puerto) else 'no contesta'}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas; depende de qué servicios tengas en marcha):

```text
broker MQTT          mosquitto:1883  CONTESTA
autómata Modbus      modbus:1502  CONTESTA
servidor OPC-UA      opcua:4840  CONTESTA
modelo de lenguaje   llm:8088  CONTESTA
API de inferencia    api:8000  CONTESTA
Prometheus           prometheus:9090  CONTESTA
panel                panel:8501  CONTESTA
```

**Cómo se lee:** todo lo que esté en marcha contesta: dentro de la red de la línea, cualquier programa llega a cualquier servicio. Cada «CONTESTA» es una puerta. Que esté abierta no es un fallo en sí; lo es si detrás no se pide quién eres.

### 3 — ¿El broker acepta a cualquiera?

**Para qué:** comprobar si se puede publicar en el broker sin usuario ni contraseña.

**Qué ocurre:** te conectas al broker **sin credenciales** y publicas un mensaje inofensivo en un tema de prueba que nadie usa. Si el broker lo acepta, cualquiera podría publicar también en los temas que actúan sobre la estación.

Pega debajo de `# --- PASO 3`:

```python
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
codigo = cliente.connect("mosquitto", 1883)          # sin usuario ni contraseña
cliente.loop_start()
aceptado = cliente.publish("pruebas/inventario", "solo una prueba").wait_for_publish(timeout=5) is None
cliente.loop_stop()
cliente.disconnect()
anonimo = codigo == 0
print(f"broker sin credenciales: {'ACEPTA' if anonimo else 'rechaza'} la conexión y la publicación")
if anonimo:
    hallazgos.append(("broker MQTT", "acepta a cualquiera", "dictámenes y consignas falsos", "usuarios y permisos por tema"))
```

**Resultado esperado** (líneas nuevas):

```text
broker sin credenciales: ACEPTA la conexión y la publicación
```

**Cómo se lee:** **acepta**: es el `allow_anonymous true` de `mosquitto.conf`. Lo has comprobado con un tema de prueba; con el mismo acceso, alguien podría publicar en `linea/est01/consigna` o `linea/est01/dictamen`, como en «Experimenta».

### 4 — ¿El autómata se deja leer sin credenciales?

**Para qué:** comprobar si el registro de paro de seguridad es accesible desde la red.

**Qué ocurre:** te conectas por Modbus y **lees** (no escribes) el registro 10, el paro de seguridad.

Pega debajo de `# --- PASO 4`:

```python
plc = ModbusTcpClient("modbus", port=1502)
plc.connect()
paro = plc.read_holding_registers(10, 1, slave=1)
plc.close()
if not paro.isError():
    print(f"registro de paro leído sin credenciales: {paro.registers[0]}")
    hallazgos.append(("autómata Modbus", "se lee sin credenciales; Modbus tampoco protege la escritura",
                      "alguien podría escribir el paro", "red de control separada y cortafuegos"))
```

**Resultado esperado** (líneas nuevas):

```text
registro de paro leído sin credenciales: 0
```

**Cómo se lee:** se lee sin pedir nada. Modbus TCP no tiene autenticación: si se puede leer, también se puede escribir. **No lo pruebes escribiendo**: en una planta, escribir un registro de paro para «ver si se puede» es un incidente. Por eso este programa solo lee y apunta el riesgo.

### 5 — ¿Las variables OPC-UA se pueden escribir?

**Para qué:** saber si un cliente podría cambiar lo que ve el SCADA, sin necesidad de intentarlo.

**Qué ocurre:** te conectas al servidor OPC-UA y **lees el permiso** de escritura de cada variable de la estación, sin escribir ninguna.

Pega debajo de `# --- PASO 5`:

```python
async def permisos_opcua():
    async with Client(url="opc.tcp://opcua:4840/linea/server") as c:
        estacion = await c.nodes.objects.get_child(["2:Estacion"])
        resultado = {}
        for var in await estacion.get_children():
            nivel = (await var.read_attribute(18)).Value.Value      # atributo 18: nivel de acceso del usuario
            resultado[(await var.read_browse_name()).Name] = bool(nivel & 2)   # el bit 2 es «se puede escribir»
        return resultado

escribibles = [n for n, w in asyncio.run(permisos_opcua()).items() if w]
print(f"variables OPC-UA que cualquiera puede escribir: {escribibles}")
if escribibles:
    hallazgos.append(("servidor OPC-UA", f"{len(escribibles)} variables escribibles sin usuario",
                      "valores falsos en el SCADA", "variables de proceso en solo lectura; usuarios"))
```

**Resultado esperado** (líneas nuevas):

```text
variables OPC-UA que cualquiera puede escribir: ['Temperatura', 'Vibracion', 'Corriente', 'Pieza']
```

**Cómo se lee:** las cuatro variables de la estación son escribibles, y lo sabes sin haber escrito nada: el propio servidor lo declara. Es lo que en el reto 2 del M02-02 comprobaste escribiendo 999 °C; aquí basta con preguntar el permiso.

### 6 — La tabla de riesgos

**Para qué:** convertir lo que has visto en una lista de decisiones: qué riesgo hay y qué medida lo reduce.

**Qué ocurre:** imprimes los hallazgos como una tabla: servicio, qué se ha visto, qué riesgo supone y qué medida lo reduce.

Pega debajo de `# --- PASO 6`:

```python
print(f"\n{'servicio':18s} | {'visto':45s} | {'riesgo':33s} | medida")
for servicio, visto, riesgo, medida in hallazgos:
    print(f"{servicio:18s} | {visto[:45]:45s} | {riesgo:33s} | {medida}")
```

**Resultado esperado** (líneas nuevas):

```text
servicio           | visto                                         | riesgo                            | medida
broker MQTT        | acepta a cualquiera                           | dictámenes y consignas falsos     | usuarios y permisos por tema
autómata Modbus    | se lee sin credenciales; Modbus tampoco prote | alguien podría escribir el paro   | red de control separada y cortafuegos
servidor OPC-UA    | 4 variables escribibles sin usuario           | valores falsos en el SCADA        | variables de proceso en solo lectura; usuarios
```

**Cómo se lee:** es la evaluación del lab, pero **comprobada** por un programa en lugar de escrita de memoria. Se puede volver a pasar cada vez que cambie la instalación, y es lo que se adjunta a una evaluación de riesgos: no «creemos que», sino «hemos comprobado que». Cada medida de la última columna está en la tabla de defensa por capas del glosario.
## Reto

Los dos retos se hacen después de «Mejora» y de «Constrúyelo tú».

### 1 — ¿Basta con publicar en localhost?

**La situación:** después de la mejora, el broker solo está publicado en `127.0.0.1` del equipo. Parece que ya nadie puede publicar un [dictamen](../glosario/05-operacion-gobierno.md#dictamen) falso.

**Qué haces:** compruebas el broker desde dos sitios. Desde tu equipo, si contesta por la dirección de red del equipo (la que usaría otro ordenador de la planta) y por `127.0.0.1`. Y desde dentro, volviendo a pasar tu inventario de «Constrúyelo tú».

```bash
# Desde el equipo: ¿contesta por la red? Cambia 192.168.1.149 por la dirección de tu equipo (ip -4 addr)
timeout 3 bash -c 'echo > /dev/tcp/192.168.1.149/1883' && echo "por la red: abierto" || echo "por la red: cerrado"
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/1883' && echo "en el propio equipo: abierto" || echo "en el propio equipo: cerrado"

# Desde dentro: tu inventario
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m08_01_mi_inventario.py
```

**Lo que buscas:** desde dónde se puede seguir publicando en el broker después de la mejora.

<details>
<summary>Ver solución</summary>

```text
por la red: cerrado
en el propio equipo: abierto
```

```text
broker MQTT          mosquitto:1883  CONTESTA
...
broker sin credenciales: ACEPTA la conexión y la publicación
```

**Desde otro ordenador de la planta, ya no se llega.** Pero desde el propio equipo, sí, y desde cualquier contenedor de la línea, también: tu inventario sigue viendo el broker abierto y aceptando a cualquiera, porque los contenedores hablan entre ellos por la red interna de Docker, que la mejora no toca.

**La regla:** limitar la red reduce **quién llega**; no controla **quién publica qué**. Para eso hace falta autenticación en el broker (usuarios) y permisos por tema (solo el modelo puede publicar dictámenes; solo el operario, consignas). Cada capa de la defensa en profundidad cubre un hueco que las otras dejan.

</details>

### 2 — ¿Qué componentes pueden actuar sobre la estación?

**La situación:** en el curso hay tres programas que hablan con la estación en nombre de la IA: el [agente](../glosario/04-ia-generativa.md#agente) del M05-04, el vigilante predictivo del M06-03 en modo automático y el agente de incidencias del M07-03.

**Qué haces:** abres sus herramientas y buscas cuáles **escriben**: `HERRAMIENTAS` en tu `infra/construye/m05_04_mi_agente.py`, la función `cmd_m06_03` y el diccionario `HERRAMIENTAS` del M07-03 en `infra/linea/cli.py`. Para encontrarlos rápido:

```bash
grep -n "HERRAMIENTAS\|TOPIC_CONSIGNA\|write_register" linea/cli.py construye/m05_04_mi_agente.py
```

**Lo que buscas:** qué componentes pueden cambiar algo en la estación, y qué los limita.

<details>
<summary>Ver solución</summary>

- **Los dos agentes (M05-04 y M07-03) no tienen ninguna herramienta que escriba**: solo leen. Es **mínimo privilegio**: no pueden actuar porque no tienen con qué.
- **El vigilante del M06-03 sí actúa en modo automático**: publica una consigna de refrigeración (`TOPIC_CONSIGNA`). Lo limita la **máquina**: la estación solo acepta niveles de 1 a 3, venga la orden de quien venga.
- Nadie escribe registros Modbus (`write_register` no aparece): el paro queda fuera del alcance de la IA.

**La regla:** cada componente con IA tiene que tener por escrito qué puede hacer y qué lo limita, y el límite tiene que estar **fuera** del componente (en la máquina, en el broker), no en que el componente «se porte bien».

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: modbus no disponible para el cruce OT` | el esclavo está parado | `docker compose up -d modbus` |
| `FALLO: el paro de seguridad no está en reposo` | alguien escribió el registro | `docker compose restart modbus` |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `asyncua` se queda esperando o da `TimeoutError` | el contenedor `opcua` está parado | `docker compose up -d opcua` |
| el inventario dice que el broker no contesta | lanzas el script con el Python de tu equipo, fuera de la red de Docker | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |

## Conclusiones

### Qué es evaluar riesgos

Es responder a tres preguntas antes de llevar la solución a la red de planta: **qué está expuesto**, **qué puede salir mal** y **qué se ha hecho para evitarlo**. Cada servicio que escucha en un puerto es una superficie; los más delicados son los que tocan OT.

### Cómo deben ser las medidas

| Tipo | Medida declarada | ¿Concreta y comprobable? |
|------|------------------|--------------------------|
| Dato | El [histórico](../glosario/01-datos-arquitectura.md#historico) y el procedimiento no salen del volumen local | Sí |
| Modelo | Los modelos están en disco y cada respuesta lleva versión | Sí |
| Acceso | Los puertos solo se publican en localhost | Sí, y se puede comprobar |

### Cómo se comprueba que se cumplen

Comparando lo escrito con lo real. En el paso 1, `docker compose ps` enseña `0.0.0.0:1883`: el puerto está abierto **en todas las interfaces**, no solo en localhost. La medida de acceso **no se cumple**, y el comando `m08-01` no lo detecta porque solo imprime el texto.

### Cómo se corrige

- **Cumplir la medida**: publicar los puertos solo en `127.0.0.1` (solución del reto 1).
- **Mínimo privilegio** también en los agentes: sin herramientas de escritura (M05-04).
- **Separar redes**: la de OT no debería ser accesible desde la de oficina sin pasar por un punto controlado.
- **Repetir la comprobación** cada vez que cambie la arquitectura.

### En una frase

> 🔑 Una evaluación de riesgos no termina cuando se escriben las medidas, sino cuando se comprueba que se cumplen.
