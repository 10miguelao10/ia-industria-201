# M06-02 — Integración con sistemas industriales

[← Página anterior](M06-01-inferencia-edge.md) · [Siguiente página →](../M07-mlops-observabilidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Publicas el dictamen como evento y compruebas que el registro de paro de seguridad sigue en cero.

### Prerrequisitos

- mosquitto, sensor y modbus en marcha.
- El modelo de M03-03.

### En qué consiste

Cada dictamen va al tema `linea/est01/dictamen` con la pieza, la decisión (`seguir` o `revisar`) y la probabilidad. El automatismo se entera por el evento. El registro Modbus 10 es el paro de seguridad, y este flujo no lo escribe. La presión no viaja en el ciclo vivo; el laboratorio usa la consigna nominal de 6 bar.

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
