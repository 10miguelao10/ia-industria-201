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

Cada servicio que escucha en un puerto es una **superficie**: algo a lo que se puede llegar desde la red. Los más delicados son los que tocan la parte OT, como el esclavo Modbus que tiene el registro del paro de seguridad.

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

**El broker.** Abre `infra/mosquitto/mosquitto.conf`:

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

**El servidor OPC-UA.** En `infra/linea/opcua_server.py`, las variables se declaran con `await nodo.set_writable()`: cualquier cliente podría escribirlas y falsear lo que ve un SCADA.

**El esclavo Modbus.** Modbus TCP no tiene autenticación: quien llegue al 1502 puede leer y **escribir** registros, incluido el 10, el paro de seguridad. En este laboratorio ningún componente lo escribe, pero el protocolo lo permitiría.

## Experimenta: actuar sin ser el modelo

**Qué ocurre:** publicas directamente en el broker una consigna de refrigeración, sin pasar por el modelo ni por `lab`, como lo haría cualquiera con acceso a la red.

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

## Reto

### 1 — ¿Basta con publicar en localhost?

Después de la mejora, el broker solo escucha en el propio equipo. ¿Ya no puede publicar nadie un dictamen falso?

<details>
<summary>Ver solución</summary>

No del todo. Cualquier programa que corra **en el mismo equipo** (o cualquier contenedor en la misma red de Docker) sigue pudiendo publicar sin usuario. Limitar la red reduce quién llega; para controlar quién publica qué hace falta **autenticación** (`allow_anonymous false` con usuarios) y **permisos por tema** (ACL): por ejemplo, que solo el servicio del modelo pueda escribir en `linea/est01/dictamen` y nadie más en `linea/est01/consigna`.

</details>

### 2 — El agente

¿Qué medida tomaste en M05-04 al no crear una herramienta de escritura?

<details>
<summary>Ver solución</summary>

Mínimo privilegio: el agente no puede escribir en el proceso porque no tiene con qué.

</details>

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

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: modbus no disponible para el cruce OT` | el esclavo está parado | `docker compose up -d modbus` |
| `FALLO: el paro de seguridad no está en reposo` | alguien escribió el registro | `docker compose restart modbus` |

## Conclusiones

### Qué es evaluar riesgos

Es responder a tres preguntas antes de llevar la solución a la red de planta: **qué está expuesto**, **qué puede salir mal** y **qué se ha hecho para evitarlo**. Cada servicio que escucha en un puerto es una superficie; los más delicados son los que tocan OT.

### Cómo deben ser las medidas

| Tipo | Medida declarada | ¿Concreta y comprobable? |
|------|------------------|--------------------------|
| Dato | El histórico y el procedimiento no salen del volumen local | Sí |
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
