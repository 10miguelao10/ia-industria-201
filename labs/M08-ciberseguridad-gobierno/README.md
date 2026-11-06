# M08 — Ciberseguridad y gobierno de IA

[← Página anterior](../M07-mlops-observabilidad/M07-03-incidencias-agente.md) · [Siguiente página →](M08-01-evaluacion-riesgos.md)

> [!NOTE]
> **Cómo funciona este módulo.** Tiene dos bloques, uno por laboratorio. En cada bloque: primero la **teoría** y una **demostración** que se proyecta en clase, paso a paso; después **practicas tú** con el laboratorio, a tu ritmo.

## Qué aprenderás

- Cómo se **evalúan los riesgos** de una solución de IA industrial: qué expone, qué puede salir mal y qué medidas lo evitan.
- Cómo se comprueba que una medida **se cumple de verdad**, no solo que está escrita.
- Qué es **gobernar** un modelo: poder reconstruir cada decisión y clasificar su uso.

| Bloque | Concepto | Laboratorio |
|--------|----------|-------------|
| 1 | Evaluación de riesgos | [M08-01](M08-01-evaluacion-riesgos.md) |
| 2 | Gobierno y trazabilidad | [M08-02](M08-02-gobierno-trazabilidad.md) |

## Antes de empezar

```bash
cd infra
docker compose up -d mosquitto sensor archivador modbus api
```

## Introducción: lo que se ha construido, visto como un riesgo

A lo largo del curso has montado una arquitectura completa: estación, broker, histórico, protocolos OT, modelos, servicio de inferencia, modelo de lenguaje, agente, monitorización. Cada pieza es útil, y cada pieza es también **algo que se puede atacar, romper o usar mal**.

| Pregunta de seguridad | Pregunta de gobierno |
|-----------------------|----------------------|
| ¿Qué está expuesto? | ¿Quién decide qué, con qué modelo? |
| ¿Quién puede leer o escribir? | ¿Se puede reconstruir cada decisión? |
| ¿Qué pasa si alguien manda un dato falso? | ¿Qué tipo de sistema es frente al Reglamento de IA? |

---

## Bloque 1 — Evaluación de riesgos

### Teoría

Cada servicio que escucha en un puerto es una **superficie de ataque**. Evaluar riesgos es hacer el inventario de superficies, pensar qué puede salir mal en cada una y poner una **medida concreta** que se pueda **comprobar**.

En planta, lo más delicado es todo lo que toca **OT**: el PLC, el paro de seguridad y los canales por los que llegan órdenes o dictámenes.

### Demostración

**Qué se demuestra:** que en esta arquitectura cualquiera que llegue al broker puede publicar lo que quiera. En el laboratorio harás el inventario completo y aplicarás una medida.

#### Paso 1 — El broker acepta a cualquiera

**Qué vamos a ver:** la configuración del broker, en `infra/mosquitto/mosquitto.conf`.

```bash
cat mosquitto/mosquitto.conf
```

```text
listener 1883
allow_anonymous true
persistence false
log_dest stdout
```

**Cómo se lee:** `allow_anonymous true`: no pide usuario ni contraseña. Quien llegue al puerto 1883 puede publicar y suscribirse.

#### Paso 2 — Publicar un dictamen falso

**Qué vamos a ver:** se publica un dictamen que dice «seguir» para una pieza inventada, sin ser el modelo.

```bash
docker compose exec mosquitto mosquitto_pub -t 'linea/est01/dictamen' \
  -m '{"pieza_id": "P9999", "decision": "seguir", "probabilidad": 0.01, "origen": "desconocido"}' && echo publicado
```

```text
publicado
```

**Cómo se lee:** el broker lo ha aceptado y lo ha repartido. Un automatismo que se fiara de cualquier mensaje en `linea/est01/dictamen` dejaría pasar una pieza con este mensaje.

> **Qué señalar en pantalla:** «El riesgo no está en el modelo: está en el canal por el que viaja lo que dice el modelo. Y nadie lo había mirado hasta ahora».

#### Paso 3 — La pregunta que abre el laboratorio

> **¿Qué más está expuesto en esta arquitectura, y qué haríais para que solo pueda publicar quien debe?**

### Ahora tú: M08-01

→ **[M08-01 — Evaluación de riesgos](M08-01-evaluacion-riesgos.md)**

Harás el inventario de superficies, comprobarás si las medidas declaradas se cumplen, encontrarás las variables OPC-UA escribibles y aplicarás una medida real: publicar el broker solo en el propio equipo.

---

## Bloque 2 — Gobierno y trazabilidad

### Teoría

**Gobernar** un modelo es poder responder, para cualquier pieza, **por qué se tomó esa decisión**: qué entró, qué se dictaminó, con qué modelo exacto y cuándo. Y saber **qué tipo de sistema** es: si asiste a una persona o decide solo, y sobre qué.

El **Reglamento europeo de IA** (AI Act) clasifica los sistemas por su riesgo y pide más controles cuanto más deciden solos sobre cosas importantes. Un sistema que **recomienda** y no toca la seguridad está muy lejos de uno que **decide** sobre personas o sobre la seguridad de una máquina.

### Demostración

**Qué se demuestra:** el registro que deja el servicio de inferencia de cada dictamen. En el laboratorio comprobarás que no se puede reescribir y reconstruirás la decisión de una pieza.

#### Paso 1 — El registro de predicciones

**Qué vamos a ver:** cada `POST /predecir` del M07 dejó una línea en `infra/data/predicciones.jsonl`. Se abre en VS Code y se mira la última:

```bash
tail -1 data/predicciones.jsonl
```

**Resultado esperado:**

```json
{"pieza_id": "SRV0001", "version": "defecto-0.1", "huella_modelo": "69a897cdf955", "entrada": {"pieza_id": "SRV0001", "temperatura_c": 61.39, "vibracion_mm_s": 0.286, "corriente_a": 4.07, "presion_bar": 5.96}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}
```

**Cómo se lee:**

| Pregunta de un auditor | Dónde está la respuesta |
|------------------------|-------------------------|
| ¿Qué pieza? | `pieza_id` y `ts` |
| ¿Con qué datos se decidió? | `entrada` |
| ¿Qué se decidió y con qué seguridad? | `dictamen` y `probabilidad` |
| ¿Con qué modelo exacto? | `version` y, sobre todo, `huella_modelo` |

> **Qué señalar en pantalla:** «Si esta línea no existiera, ante una reclamación solo podríamos decir "el modelo dijo que estaba bien". Con ella, podemos reconstruir la decisión».

#### Paso 2 — La pregunta que abre el laboratorio

> **Si alguien cambia el fichero de versión después de que se haya dictaminado una pieza, ¿cambia lo que dice el registro de esa pieza?**

### Ahora tú: M08-02

→ **[M08-02 — Gobierno y trazabilidad](M08-02-gobierno-trazabilidad.md)**

Dictaminarás dos piezas cambiando la versión entre medias, comprobarás que el rastro no se reescribe, verificarás que la huella del registro es la del modelo en disco y clasificarás el uso del sistema.

---

## Conclusiones del módulo

### Qué es la seguridad y el gobierno de una solución de IA

Saber qué se expone y protegerlo con medidas comprobables, y poder explicar cada decisión del modelo con un registro que nadie puede reescribir.

### Cómo debe hacerse

| Requisito | Dónde lo has trabajado |
|-----------|------------------------|
| Inventario de superficies y medidas concretas | M08-01 |
| Comprobar que las medidas se cumplen | M08-01 |
| Canales con autenticación y servicios solo donde hacen falta | M08-01 |
| Registro de cada decisión con entrada, dictamen, modelo y hora | M08-02 |
| Clasificar el uso: asiste o decide | M08-02 |

### Lo que has visto romperse

| Fallo | Dónde | Qué enseña |
|-------|-------|------------|
| Un dictamen falso aceptado por el broker | Demo del bloque 1 | El canal también es superficie |
| Una medida escrita que no se cumple | M08-01 | Hay que comprobar, no solo declarar |
| Variables OPC-UA que cualquiera puede escribir | M08-01 | Lo que lee el SCADA puede falsearse |
| La versión cambia y el modelo no | M07-01, M08-02 | La huella identifica el modelo; la etiqueta, no |

### Todo empieza en el M01

Sin un identificador de pieza único y una hora desde el origen, aquí no habría nada que reconstruir. La seguridad y la trazabilidad no se añaden al final: se diseñan desde la primera pieza de la arquitectura.

### En una frase

> 🔑 Una solución de IA en planta es tan segura como su canal más abierto y tan gobernable como su registro: si no puedes explicar por qué se aceptó una pieza, el modelo no está bajo control, por mucho que acierte.
