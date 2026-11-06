# M02-02 — Integración mediante protocolos industriales

[← Página anterior](M02-01-telemetria.md) · [Siguiente página →](M02-03-preparacion-datos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es **integrar mediante protocolos industriales**: cómo se accede al mismo dato por MQTT, OPC-UA y Modbus, qué te cuenta cada uno, cómo se detecta un error de integración que no da ningún fallo, y cómo se construye una pasarela que traduce un protocolo a otro.

### Prerrequisitos

- `mosquitto` y `sensor` en marcha; en este lab se añaden `opcua` y `modbus`.
- Puertos 4840 y 1502 libres. RAM conjunta ~0,7 GB.
- Dos terminales en `infra/` para la mejora.

### Qué está pasando

En una planta, la misma máquina se lee de varias formas según quién pregunte. El SCADA la lee por **OPC-UA**. Un PLC antiguo o un equipo de otro fabricante solo habla **Modbus**. La plataforma de datos recibe los registros por **MQTT**. Integrar es conseguir que todos cuenten lo mismo.

Aquí los tres caminos exponen la misma estación:

| Protocolo | Cómo se pide el dato | Qué te devuelve |
|-----------|----------------------|-----------------|
| MQTT | Te suscribes al tema `linea/est01/ciclo` | El registro entero, en JSON, con nombres |
| OPC-UA | Navegas hasta el objeto `Estacion` y lees sus variables | El valor con su nombre y su tipo |
| Modbus | Lees registros por su número | Enteros sin nombre ni unidad |

Con Modbus, el significado de cada registro y su escala vienen en el **manual del equipo**, no en el dato. No hay tres sensores: `opcua` y `modbus` leen el mismo estado que escribe la estación (`infra/data/estado.json`). El puerto Modbus del laboratorio es el 1502, no el 502 habitual en planta.

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Servidor OPC-UA del PLC o del SCADA | Contenedor `opcua`, código en `infra/linea/opcua_server.py` |
| PLC o equipo con Modbus TCP | Contenedor `modbus`, código en `infra/linea/modbus_server.py` |
| Manual con el mapa de registros | La tabla de este lab, sacada del código |
| Pasarela de protocolos en el edge | El comando `lab pasarela` (en la mejora) |

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

**Cómo se lee:** si preguntas más rápido de lo que la estación fabrica, lees dos veces la misma carcasa; si preguntas más despacio, te saltas alguna. Con Modbus, quien integra tiene que decidir **cada cuánto preguntar**, igual que hace Prometheus con sus muestras (M01-03). Con MQTT, cada carcasa llega una vez.

## Reto

### 1 — La escala olvidada

Un sistema lee el registro 0 y lo guarda tal cual como temperatura. ¿Qué pasa? ¿Da algún error?

<details>
<summary>Ver solución</summary>

Guarda 630 °C donde había 63,0 °C. No da ningún error: es un número válido. El primer síntoma aparecería mucho después, en un modelo que «aprende» que el husillo trabaja a 600 °C, o en un panel con una alarma que no salta nunca. Es exactamente el problema de las «décimas» que vas a limpiar en el M02-03.

</details>

### 2 — Variables que se pueden escribir

En `infra/linea/opcua_server.py`, busca la línea `await nodo.set_writable()`. ¿Qué permite? ¿Qué riesgo tiene?

<details>
<summary>Ver solución</summary>

Marca las variables como **escribibles**: cualquier cliente que llegue al puerto 4840 podría cambiar la temperatura o la pieza publicadas, y el SCADA mostraría un valor falso. En un servidor real, las variables de proceso son de solo lectura para quien no deba escribir, y el acceso va con usuario y cifrado. Lo retomarás en la evaluación de riesgos del M08-01.

</details>

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

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: OPC-UA: …` | El servidor no arrancó | `docker compose logs opcua` |
| `FALLO: Modbus no conecta` | El esclavo no está en marcha | `docker compose up -d modbus` |
| La terminal 2 no recibe nada de la pasarela | La suscripción se abrió con otro tema | Copia el tema `linea/est01/pasarela` tal cual |

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
- **Solo lectura** hacia OT para los sistemas de datos.

### En una frase

> 🔑 Integrar no es solo conectarse: es garantizar que todos leen el mismo dato, con la misma unidad, y que nadie puede tocar lo que no debe.
