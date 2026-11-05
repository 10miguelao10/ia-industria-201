# M06 — Edge AI e integración industrial

[← Página anterior](../M05-ia-generativa/M05-04-agentes.md) · [Siguiente página →](M06-01-inferencia-edge.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Ejecutar una inferencia en el puesto, junto al proceso simulado.
- Medir que la respuesta no depende de un servicio externo.
- Devolver un evento al automatismo simulado sin tocar la lógica de seguridad.

## Teoría

Edge, aquí, quiere decir: el modelo responde en una máquina cercana a la línea, no en un centro de datos. En la clase esa máquina es el portátil. La latencia que importa es la que ve el ciclo, no la de una demo en otra red.

### Híbrido

Entrenar y vigilar puede vivir en otro sitio. Inferir, si el ciclo no espera, vive al lado. Si se corta la red de oficina, el borde sigue dictaminando con el último modelo que recibió.

### IA y OT

El modelo emite un evento: pieza a revisar, anomalía, confianza baja. El automatismo decide si ese evento cambia una ruta, enciende un aviso o no hace nada. No se escribe un modelo dentro del enclavamiento de seguridad.

Eso se prueba con el simulador: hay una cola de eventos que el «PLC» lee. No hay una escritura directa al registro que pararía la línea.

## Demostración guiada

Se carga el modelo ya entrenado en el propio puesto, se mide el tiempo por pieza y el dictamen se publica como evento para un automatismo que no cede su paro de seguridad.

Todo se lanza desde `infra/`, con mosquitto, sensor y modbus en marcha y el modelo de M03-03.

**1. Inferencia en el borde.**

```bash
docker compose stop llm     # no hace falta en este módulo
docker compose --profile lab run --rm --no-deps lab m06-01
```

📋 Ficha del comando [`m06-01`](../comandos-lab.md#m06-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
ms_por_pieza=0.39 fichero=modelo_defecto.joblib
OK m06-01: 0.39 ms por pieza, modelo en disco
```

**2. El dictamen como evento.** En una segunda terminal, el automatismo escucha:

```bash
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/dictamen' -v -C 1
```

En la primera, se dictamina y se publica:

```bash
docker compose --profile lab run --rm --no-deps lab m06-02
```

📋 Ficha del comando [`m06-02`](../comandos-lab.md#m06-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
linea/est01/dictamen {"pieza_id": "P0207", "decision": "seguir", "probabilidad": 0.08}
```

```text
OK m06-02: P0207 -> seguir; paro=0
```

No hay nube en ningún punto: cortar la red de la oficina no cambia el dictamen.

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M06-01 | [Inferencia en entornos edge](M06-01-inferencia-edge.md) | Dictaminar en el puesto, sin nube. |
| M06-02 | [Integración con sistemas industriales](M06-02-integracion-ot.md) | Entregar el dictamen como evento al automatismo simulado. |

→ Empieza por **[M06-01 — Inferencia en entornos edge](M06-01-inferencia-edge.md)**.

## Conclusiones del módulo

Al terminar los laboratorios de este módulo deberías tener claro que:

- El modelo se ejecuta junto a la máquina y llega a tiempo para cada pieza, sin depender de la red.
- El dictamen viaja como evento y el automatismo decide qué hacer con él.
- El paro de seguridad nunca depende del modelo.
