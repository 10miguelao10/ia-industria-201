# M02 — Captura, integración y preparación de datos

[← Página anterior](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [Siguiente página →](M02-01-telemetria.md)

> [!NOTE]
> **Cómo funciona este módulo.** Tiene cuatro bloques, uno por laboratorio. En cada bloque: primero la **teoría** y una **demostración** que se proyecta en clase, paso a paso; después **practicas tú** con el laboratorio, a tu ritmo.

## Qué aprenderás

- Consumir la telemetría de la estación como **eventos** y distinguir una microparada de una parada.
- Leer el mismo dato por **MQTT, OPC-UA y Modbus**, y entender qué te da cada protocolo.
- **Preparar** un histórico sucio para analítica sin esconder sus problemas.
- **Construir un dataset** propio uniendo las señales de la línea con el resultado de calidad.

| Bloque | Concepto | Laboratorio |
|--------|----------|-------------|
| 1 | Telemetría basada en eventos | [M02-01](M02-01-telemetria.md) |
| 2 | Integración por protocolos industriales | [M02-02](M02-02-protocolos.md) |
| 3 | Preparación del dato | [M02-03](M02-03-preparacion-datos.md) |
| 4 | Construcción de un dataset de producción | [M02-04](M02-04-dataset-linea.md) |

## Antes de empezar

Desde `infra/`, con la línea del M01 en marcha:

```bash
cd infra
docker compose up -d mosquitto sensor archivador
```

## Introducción: el modelo solo ve lo que la integración le entrega

En el M01 viste el camino del dato. En este módulo lo miras desde el otro lado: **qué tiene que pasarle al dato para que un modelo pueda aprender de él**. Si la hora está mal, la unidad cambia a mitad de turno, faltan piezas o el resultado de calidad se une con la pieza equivocada, el entrenamiento aprende ese desastre sin dar ningún error.

Calidad mínima de un dato de proceso antes de analizarlo:

| Requisito | Por qué |
|-----------|---------|
| Hora presente y ordenable | Para saber qué pasó antes y qué después |
| Unidad explícita | 61,4 °C y 614 décimas no son lo mismo |
| Identificador de pieza que no se repita | Para unir las señales con su resultado |
| Huecos visibles, no rellenados | Un sensor mudo no es una temperatura media |
| Valores imposibles apartados | 9999 °C es un sensor roto, no un pico de proceso |

---

## Bloque 1 — Telemetría basada en eventos

### Teoría

La estación **no espera a que le pregunten**: cuando termina una carcasa, publica su registro. Quien necesite enterarse se **suscribe** al tema y lo recibe en el momento. Es telemetría basada en eventos, el mismo modelo que un clic de usuario en una aplicación, pero producido por una máquina.

Un consumidor tiene que saber interpretar también **la ausencia de eventos**:

| Lo que llega | Qué puede significar |
|--------------|----------------------|
| Registros cada ~1 s | La estación produce normalmente |
| Unos segundos sin nada | **Microparada**: un atasco, un sensor de presencia, el operario |
| Silencio prolongado | **Parada**: avería, cambio de herramienta, fin de turno… o la comunicación caída |

El silencio no es un cero: no se puede rellenar con lecturas inventadas.

### Demostración

**Qué se demuestra:** el flujo de eventos en directo y cómo se ve un silencio. En el laboratorio comprobarás el consumo, provocarás una parada y aprenderás a distinguirla de una microparada con datos.

#### Paso 1 — Ver los eventos en directo

**Qué vamos a ver:** nos suscribimos al tema de la estación sin límite de mensajes. Los registros aparecen según la estación los produce.

```bash
# Sin -C: escucha sin fin (Ctrl+C para salir). -v enseña el tema delante de cada mensaje
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/ciclo' -v
```

**Resultado esperado** (una línea por carcasa; Ctrl+C tras unos segundos):

```text
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0051", "ts": "2026-11-06T02:12:29+00:00", …, "tiempo_ciclo_s": 0.99}
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0052", "ts": "2026-11-06T02:12:30+00:00", …, "tiempo_ciclo_s": 0.92}
linea/est01/ciclo {"estacion": "EST-01", "pieza_id": "P0053", "ts": "2026-11-06T02:12:31+00:00", …, "tiempo_ciclo_s": 1.03}
```

**Cómo se lee:** cada línea es un **evento**: «ha terminado una carcasa». No llegan a un ritmo fijo: `tiempo_ciclo_s` varía alrededor de 1.

> **Qué señalar en pantalla:** nadie le ha preguntado nada a la estación. Llega solo, cuando ocurre.

#### Paso 2 — Ver un silencio

**Qué vamos a ver:** con la suscripción abierta, se para la estación desde otra terminal.

```bash
# En otra terminal
docker compose stop sensor
```

**Resultado esperado:** en la primera terminal dejan de llegar líneas. No aparece ningún mensaje de error ni ninguna temperatura a 0: simplemente, nada.

```bash
# Se vuelve a arrancar
docker compose start sensor
```

Los mensajes vuelven, y la numeración empieza otra vez en `P0001`.

> **Qué señalar en pantalla:** el consumidor no sabe por qué no llega nada. Puede ser una parada, una microparada larga o un cable de red. Saberlo es trabajo de quien diseña el consumidor.

#### Paso 3 — La pregunta que abre el laboratorio

> **Si dejan de llegar registros durante 5 segundos, ¿hay que avisar de una parada?**

### Ahora tú: M02-01

→ **[M02-01 — Captura de telemetría industrial](M02-01-telemetria.md)**

Comprobarás qué trae cada registro, abrirás y cerrarás una parada, medirás con datos cuánto duran las microparadas para elegir un umbral de parada con criterio, y publicarás un estado retenido para que quien llegue tarde sepa cómo está la estación.

---

## Bloque 2 — Integración por protocolos industriales

### Teoría

En una planta, la misma máquina se lee de varias formas según quién pregunte:

| Protocolo | Idea | Qué te devuelve | Uso típico |
|-----------|------|-----------------|------------|
| MQTT | Se publica un mensaje en un tema; quien está suscrito lo recibe | El registro entero, con nombres | Plataforma de datos, IT |
| OPC-UA | Un servidor expone variables con nombre y tipo; un cliente navega y las lee | El valor con su nombre y su tipo | SCADA, MES |
| Modbus TCP | El equipo expone registros numerados; se leen por número | Un entero sin nombre ni unidad | PLC y equipos sencillos o antiguos |

No son tres verdades distintas: son tres puertas al mismo hecho de proceso. Integrar es conseguir que todas cuenten lo mismo.

### Demostración

**Qué se demuestra:** la misma estación vista por OPC-UA y por Modbus, y lo que cada uno te cuenta. En el laboratorio comprobarás que cuadran, descifrarás el mapa de registros y construirás una pasarela.

#### Paso 1 — Arrancar las otras dos puertas

```bash
# Servidor OPC-UA (puerto 4840) y esclavo Modbus TCP (puerto 1502)
docker compose up -d opcua modbus
```

#### Paso 2 — OPC-UA: datos con nombre

**Qué vamos a ver:** un cliente OPC-UA recorre el objeto `Estacion` del servidor y enseña cada variable. `lab opcua` es un comando de ayuda que hace de cliente.

```bash
docker compose --profile lab run --rm --no-deps lab opcua
```

**Resultado esperado** (cambian los valores):

```text
nodo                  valor          tipo
Estacion.Temperatura  62.33          Double
Estacion.Vibracion    0.265          Double
Estacion.Corriente    4.06           Double
Estacion.Pieza        P0123          String
OK opcua: 4 variables en el objeto Estacion
```

**Cómo se lee:** cada dato tiene **nombre** (`Temperatura`), **valor** y **tipo** (`Double`, un número con decimales; `String`, texto). Un cliente que no conoce la máquina puede navegar y entender qué hay.

#### Paso 3 — Modbus: números en posiciones

**Qué vamos a ver:** el mismo instante, leído por Modbus. `lab modbus` lee los registros en crudo.

```bash
docker compose --profile lab run --rm --no-deps lab modbus
```

**Resultado esperado:**

```text
registro  valor_crudo
       0          630
       1          220
       2          403
       3          125
OK modbus: 4 registros leídos desde el 0
```

**Cómo se lee:** cuatro enteros, sin nombre ni unidad. Para saber qué es cada uno hay que tener el **mapa de registros** del equipo. Aquí está en `infra/linea/modbus_server.py`:

```python
bloque.setValues(1, [
    int(round(estado["temperatura_c"] * 10)),     # registro 0: temperatura en décimas de °C
    int(round(estado["vibracion_mm_s"] * 1000)),  # registro 1: vibración en milésimas de mm/s
    int(round(estado["corriente_a"] * 100)),      # registro 2: corriente en centésimas de A
    int(estado["secuencia"]) % 10000,             # registro 3: secuencia de la estación
])
```

El 630 del registro 0 es 63,0 °C; el 220 del registro 1, 0,22 mm/s; el 403 del registro 2, 4,03 A; y el 125, la carcasa número 125.

> **Qué señalar en pantalla:** con OPC-UA, el dato se explica solo. Con Modbus, el significado está en un documento aparte. Si se pierde el mapa o alguien se equivoca de escala, el número sigue pareciendo válido.

#### Paso 4 — La pregunta que abre el laboratorio

> **¿Qué temperatura leería un sistema que se olvidara de dividir entre 10? ¿Se daría cuenta alguien?**

(Las dos lecturas de los pasos 2 y 3 son de instantes distintos, así que sus valores no coinciden: en el laboratorio las compararás en el mismo instante).

### Ahora tú: M02-02

→ **[M02-02 — Integración mediante protocolos industriales](M02-02-protocolos.md)**

Comprobarás que los tres caminos dan la misma temperatura, leerás todos los registros y los descifrarás con el mapa, encontrarás el registro del paro de seguridad y construirás una pasarela que lee Modbus y publica en MQTT, ya en grados.

---

## Bloque 3 — Preparación del dato

### Teoría

Un histórico real nunca viene limpio. Los problemas típicos tienen una causa en la máquina y una huella en el fichero:

| Problema | Qué pasó en la máquina | Huella en el fichero |
|----------|------------------------|----------------------|
| Hueco | Sensor desconectado en esa pieza | Valor vacío |
| Unidad distinta | Un equipo reporta en décimas | 614 en lugar de 61,4 |
| Sensor clavado | El sensor devuelve su valor de error | 9999 |
| Texto libre | El turno apunta incidencias a mano | Notas que no son tablas |

Preparar el dato es **decidir qué se queda, qué se corrige y qué se aparta**, y **dejarlo contado**.

### Demostración

**Qué se demuestra:** cómo se ve un histórico sucio y cómo se cuentan sus problemas antes de tocar nada. En el laboratorio lo limpiarás, compararás decisiones de limpieza y convertirás notas de texto en datos con IA.

#### Paso 1 — Un histórico de 800 piezas

**Qué vamos a ver:** el comando del laboratorio genera un histórico de ejemplo con los problemas típicos. Lo usamos solo para tener el fichero.

```bash
docker compose --profile lab run --rm --no-deps lab m02-03
```

Abre `infra/data/crudo.csv` en VS Code y desplázate: hay filas con la temperatura vacía, valores de 600 y pico y algún 9999.

#### Paso 2 — Contar los problemas

**Qué vamos a ver:** `lab sql` puede consultar también los CSV de `infra/data/` como si fueran tablas. Se cuenta cada tipo de problema.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS piezas,
          SUM(temperatura_c IS NULL) AS huecos,
          SUM(temperatura_c = 9999) AS clavados,
          SUM(temperatura_c > 150 AND temperatura_c < 9999) AS en_decimas
   FROM crudo"
```

**Resultado esperado:**

```text
 piezas  huecos  clavados  en_decimas
    800      26         6          12
```

**Cómo se lee:** de 800 piezas, 26 no tienen temperatura, 6 tienen el sensor clavado y 12 vienen en décimas. Las 12 en décimas se pueden **corregir** (dividiendo entre 10); las 32 restantes **no tienen una temperatura real** y no deberían entrar en un entrenamiento.

> **Qué señalar en pantalla:** antes de limpiar, se cuenta. Si no sabes cuántos problemas había, no sabrás si la limpieza los ha resuelto.

#### Paso 3 — La pregunta que abre el laboratorio

> **¿Qué pasa si, en lugar de quitar las 26 piezas sin temperatura, les ponemos la temperatura media?**

### Ahora tú: M02-03

→ **[M02-03 — Preparación de información para analítica](M02-03-preparacion-datos.md)**

Limpiarás el histórico, comprobarás el resultado con tus consultas, compararás qué le pasa al dato si rellenas los huecos con la media y usarás el modelo de lenguaje local para convertir notas de turno en datos, midiendo cuánto acierta.

---

## Bloque 4 — Construcción de un dataset de producción

### Teoría

Un modelo que predice defectos necesita, para cada pieza, **cómo se fabricó** y **cómo salió**. En planta, esas dos cosas están en sistemas distintos:

```
 estación ──▶ broker ──┬──▶ archivador ──▶ historial.sqlite   (señales de cada carcasa)
                       └──▶ calidad ─────▶ calidad.sqlite     (resultado de cada inspección)
```

Construir el dataset es **unir las dos fuentes, pieza a pieza**, con una clave que identifique de verdad cada carcasa.

### Demostración

**Qué se demuestra:** las dos fuentes por separado y una carcasa unida a mano. En el laboratorio construirás el dataset completo, caerás en la trampa de la clave y descubrirás el criterio de calidad.

#### Paso 1 — Arrancar el puesto de calidad

```bash
# Inspecciona cada carcasa que publica la estación y apunta si es defectuosa
docker compose up -d calidad
```

Se dejan pasar unos segundos.

#### Paso 2 — Una carcasa en las dos fuentes

**Qué vamos a ver:** se elige la última carcasa inspeccionada y se busca en las dos bases. `lab sql` tiene la de calidad disponible como `calidad.inspecciones`.

```bash
# El resultado de calidad de la última carcasa
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, ts_pieza, defecto FROM calidad.inspecciones ORDER BY id DESC LIMIT 1"
```

```text
pieza_id                  ts_pieza  defecto
   P0119 2026-11-06T02:34:01+00:00        0
```

```bash
# Sus señales en el histórico (cambia la pieza y la hora por las tuyas)
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, ts, temperatura_c, vibracion_mm_s, corriente_a FROM lecturas
   WHERE pieza_id = 'P0119' AND ts = '2026-11-06T02:34:01+00:00'"
```

```text
pieza_id                        ts  temperatura_c  vibracion_mm_s  corriente_a
   P0119 2026-11-06T02:34:01+00:00          60.87            0.28         4.07
```

**Cómo se lee:** la misma carcasa, con sus señales en una base y su resultado en otra. Unidas, forman **una fila de un dataset**: tres señales y una etiqueta (`defecto = 0`, buena).

> **Qué señalar en pantalla:** se ha unido por pieza **y hora**. ¿Por qué no basta con la pieza? Ya lo visteis en el M01.

#### Paso 3 — La pregunta que abre el laboratorio

> **Si en el histórico hay cuatro carcasas que se llaman P0119, ¿con cuál de ellas se queda el resultado de calidad si unimos solo por el nombre?**

### Ahora tú: M02-04

→ **[M02-04 — Construir un dataset con datos de la línea](M02-04-dataset-linea.md)**

Unirás las dos fuentes de las dos formas y verás cuántas filas falsas aparecen, construirás el dataset, descubrirás con consultas el criterio oculto de calidad y encontrarás las inspecciones que se equivocaron.

---

## Conclusiones del módulo

### Qué es preparar el dato para la IA

Llevarlo desde la máquina hasta una tabla en la que **cada fila es una pieza real**, con señales en unidades correctas y su resultado. Pasa por capturarlo bien (eventos), integrarlo (protocolos), limpiarlo (sin esconder problemas) y unirlo (con una clave fiable).

### Cómo debe quedar

| Requisito | Dónde lo has trabajado |
|-----------|------------------------|
| Distinguir silencio de cero, y microparada de parada | M02-01 |
| La misma magnitud, con la misma unidad, venga del protocolo que venga | M02-02 |
| Problemas contados y apartados, no rellenados | M02-03 |
| Una fila por pieza, unida por una clave que no se repite | M02-04 |

### Lo que has visto romperse

| Fallo | Dónde | Qué le haría al modelo |
|-------|-------|------------------------|
| Escala olvidada en Modbus | M02-02 | Aprender con temperaturas de 600 °C |
| Huecos rellenados con la media | M02-03 | Aprender un valor que nadie midió |
| Un modelo de lenguaje que inventa al extraer | M02-03 | Datos falsos con apariencia de reales |
| Unión solo por identificador | M02-04 | Señales de una pieza con el resultado de otra |
| Inspección que se equivoca | M02-04 | Un techo al acierto y etiquetas falsas |

### En una frase

> 🔑 Un dataset no se descarga: se construye. Cada decisión de captura, integración, limpieza y unión cambia lo que el modelo va a aprender.
