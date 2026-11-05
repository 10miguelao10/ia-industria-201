# M02-02 — Integración mediante protocolos industriales

[← Página anterior](M02-01-telemetria.md) · [Siguiente página →](M02-03-preparacion-datos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **integración mediante protocolos industriales**: cómo se accede al mismo dato por MQTT, OPC-UA y Modbus, cómo debe ser una integración fiable, qué riesgos tiene cada protocolo y cómo se reducen.

### Prerrequisitos

- mosquitto y sensor en marcha; en este lab se añaden `opcua` y `modbus`.
- Puertos 4840 y 1502 libres. RAM conjunta ~0,7 GB.

### Qué está pasando

En una planta, la misma máquina se lee de varias formas según quién pregunte. El SCADA moderno la lee por **OPC-UA**. Un PLC antiguo o un equipo de otro fabricante solo habla **Modbus**. La plataforma de datos recibe los registros por **MQTT**. Integrar es conseguir que los tres cuenten lo mismo.

Aquí los tres caminos exponen **la misma temperatura del husillo** de EST-01. Lo que cambia es cómo se pide y cuánto te cuenta cada uno:

| Protocolo | Cómo se pide el dato | Qué te devuelve |
|-----------|----------------------|-----------------|
| MQTT | Te suscribes al tema `linea/est01/ciclo` | El registro entero, en JSON, con nombres |
| OPC-UA | Navegas hasta el nodo `Estacion` → `Temperatura` | El valor con su nombre y su tipo |
| Modbus | Lees el registro número 0 | Un entero sin nombre ni unidad: 614 significa 61,4 °C |

Con Modbus, el significado de cada registro y su escala vienen en el manual del equipo, no en el dato. En este laboratorio, el registro 0 es la temperatura en décimas y el **registro 10 es el paro de seguridad**, que nadie escribe.

No hay tres sensores: `opcua` y `modbus` leen el mismo estado que escribe la estación. El puerto Modbus del laboratorio es el 1502, no el 502 habitual en planta.

### 1 — Abrir las otras dos puertas

Vas a arrancar el servidor OPC-UA y el esclavo Modbus. Hasta que esos procesos no escuchan, no hay interoperabilidad que enseñar.

```bash
# Servidor OPC-UA (4840) y esclavo Modbus TCP (1502)
docker compose up -d opcua modbus

docker compose ps --format 'table {{.Service}}\t{{.Status}}'
```

**Resultado esperado:**

```text
SERVICE      STATUS
archivador   Up About a minute
modbus       Up 5 seconds
mosquitto    Up About a minute
opcua        Up 5 seconds
sensor       Up 10 seconds
```

### 2 — Leer las tres a la vez

Vas a leer la temperatura por los tres caminos: el nodo OPC-UA `Estacion.Temperatura`, el registro Modbus 0 (dividido entre 10) y el JSON de estado. Los tres tienen que dar lo mismo.

```bash
docker compose --profile lab run --rm --no-deps lab m02-02
```

📋 Ficha del comando [`m02-02`](../comandos-lab.md#m02-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambia la temperatura; los tres valores deben quedar a menos de 1,5 °C):

```text
estado=63.22 opcua=63.22 modbus=63.2
OK m02-02: MQTT, OPC-UA y Modbus leen la misma temperatura
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
# OPC-UA: se navega por nombres (objeto Estacion → variable Temperatura)
async with Client(url=OPCUA_ENDPOINT) as client:
    ...
    nodo = await estacion.get_child([f"{indice}:Temperatura"])
    opc = float(await nodo.read_value())

# Modbus: se lee un registro por número y se aplica la escala
cliente = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
rr = cliente.read_holding_registers(0, 4, slave=1)
modbus_c = rr.registers[0] / 10        # 632 → 63,2 °C
```

OPC-UA da el dato con nombre y tipo. Modbus da un entero en una posición: la escala y el significado los tienes que saber tú.

</details>

## Comprueba tu entendimiento

**La escala**

Si Modbus devolviera 614, ¿qué temperatura es?

→ 61,4 °C. Sin dividir entre 10 no es una temperatura de husillo.

## Reto

### 1 — El registro 10

El registro 10 es el paro de seguridad y vale 0. ¿Significa que el proceso está parado?

<details>
<summary>Ver solución</summary>

No. 0 es «paro en reposo»: nadie lo ha activado. Este laboratorio lo lee pero nunca lo escribe.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: OPC-UA: …` | el servidor no arrancó | `docker compose logs opcua` |
| `FALLO: Modbus no conecta` | el esclavo no está en marcha | `docker compose up -d modbus` |

## Conclusiones

### Qué es integrar con protocolos industriales

En planta conviven equipos de épocas y fabricantes distintos, y cada uno habla un protocolo. Integrar es conseguir que todos los sistemas que leen una misma magnitud obtengan el mismo valor, venga por donde venga.

| Protocolo | Cómo se pide | Qué devuelve | Uso típico |
|-----------|--------------|--------------|------------|
| MQTT | Suscripción a un tema | El registro completo, con nombres | Plataforma de datos, IT |
| OPC-UA | Navegar hasta un nodo con nombre | Valor con nombre y tipo | SCADA, MES |
| Modbus | Leer un registro por número | Un entero sin nombre ni unidad | PLC y equipos antiguos |

### Cómo debe ser una integración fiable

- Los tres caminos dan **el mismo valor**: aquí, la temperatura del husillo con menos de 1,5 °C de diferencia.
- La **escala y el significado** de cada dato están documentados, sobre todo en Modbus (registro 0 en décimas; registro 10, paro de seguridad).
- Se distingue claramente **qué se puede leer y qué no se debe escribir nunca**.

### Sus riesgos y cómo los has visto

| Riesgo | Cómo lo has visto | Qué provoca |
|--------|-------------------|-------------|
| Escala olvidada en Modbus | El registro 0 vale 632, no 63,2 | Un modelo que reciba 632 °C aprende algo que no existe |
| Modbus no dice qué es cada registro | El significado está en el manual, no en el dato | Leer el registro equivocado da un número válido pero falso |
| Acceso de escritura a OT | El registro 10 es el paro de seguridad | Un error de integración podría actuar sobre la máquina |

### Cómo se mejora

- Preferir **OPC-UA**, que lleva nombre, tipo y unidad, cuando el equipo lo permite.
- Concentrar la traducción de Modbus en **una pasarela** con un mapa de registros documentado, y publicar desde ahí ya en grados.
- Dar a los sistemas de datos **acceso de solo lectura** a OT, y comprobar periódicamente que los tres caminos siguen cuadrando.

### En una frase

> 🔑 Integrar no es solo conectarse: es garantizar que todos leen el mismo dato, con la misma unidad, y que nadie puede tocar lo que no debe.
