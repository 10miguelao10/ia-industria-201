# M06-02 — Integración con sistemas industriales

[← Página anterior](M06-01-inferencia-edge.md) · [Siguiente página →](../M07-mlops-observabilidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **integra un modelo con los sistemas de planta (OT)**: cómo llega el dictamen al automatismo, cómo debe ser esa frontera, qué riesgos tiene y cómo se protege el control de la máquina.

### Prerrequisitos

- mosquitto, sensor y modbus en marcha.
- El modelo de M03-03.

### Qué está pasando

Un dictamen que se queda en el equipo edge no sirve de nada. Tiene que llegar al **automatismo de la línea**, que es quien desvía la carcasa a revisión o la deja seguir.

La forma de hacerlo es la misma que para los registros: el dictamen se publica como **evento** en el broker, en el tema `linea/est01/dictamen`, y el automatismo está suscrito. Así el modelo no necesita conocer el PLC ni escribir en él.

Hay una línea que no se cruza nunca: el **paro de seguridad** (registro Modbus 10) lo decide el automatismo con sus propias protecciones. El modelo recomienda; no para la máquina. En este lab se comprueba que el paro sigue en 0 después de publicar.

La presión no viaja en el registro en vivo, así que el dictamen usa la consigna nominal de 6 bar.

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

## Reto

### 1 — Confianza baja

La decisión pasa a `revisar` con una probabilidad de 0,5 o más. ¿Dónde está ese umbral, en el PLC o en el código?

<details>
<summary>Ver solución</summary>

En el código del paso, no en el PLC. Dudar manda a revisión: es una decisión de proceso, que el automatismo recibe como evento y aplica con sus propias protecciones.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el automatismo no recibió el dictamen` | mosquitto caído | `docker compose up -d mosquitto sensor modbus` |
| `FALLO: el registro de paro de seguridad cambió` | algo escribió el registro 10 | no debe ocurrir; `docker compose restart modbus` |

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
