# M08 — Ciberseguridad y gobierno de IA

[← Página anterior](../M07-mlops-observabilidad/M07-02-monitorizacion.md) · [Siguiente página →](M08-01-evaluacion-riesgos.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Señalar exposiciones de la arquitectura que ya has montado.
- Separar riesgos del dato, del modelo y del acceso.
- Dejar una traza mínima: versión, datos de entrada y dictamen.

## Teoría

La arquitectura de los módulos anteriores ya está conectada: eventos, un servicio, un modelo generativo, un agente con una herramienta. Cada conexión es un sitio donde algo puede entrar o salir de más.

### Dónde mirar

| Capa | Riesgo típico en este curso |
|------|------------------------------|
| IT / OT | Un puesto de oficina que llega de más al automatismo, o un evento de IA que se confunde con una orden de seguridad |
| Datos | Históricos o procedimientos que salen del puesto hacia un servicio externo |
| Modelo | Un fichero de modelo sin versión, o un generativo que inventa un paso de seguridad |
| Identidad | Un servicio de inferencia abierto a cualquiera en la red del aula |
| Gobierno | No poder explicar qué versión dictaminó una pieza concreta |

El reglamento europeo de IA (AI Act) trata con más exigencia los sistemas que influyen en seguridad de productos y en decisiones relevantes. En este curso basta con saber clasificar el caso: un asistente que sugiere no es lo mismo que un modelo que rechaza piezas sin persona de por medio. No es una opinión jurídica.

### Qué sí hacer

Segmentar de palabra y de hecho: el modelo propone, el automatismo de seguridad no le obedece. Trazar versión y dictamen. No dar al agente herramientas de escritura sobre el proceso.

## Demostración guiada

Se recorre la arquitectura levantada y se marca qué está expuesto. Después se pide el rastro de una pieza ya dictaminada. Si no se puede reconstruir, no hay gobierno aunque el modelo acierte.

Todo se lanza desde `infra/`, con `api` y `modbus` en marcha.

**1. Qué está expuesto.**

```bash
docker compose ps --format 'table {{.Service}}\t{{.Ports}}'
```

Cada `0.0.0.0:…` es un servicio accesible desde cualquier equipo que llegue a este.

**2. Inventario y medidas.**

```bash
docker compose --profile lab run --rm --no-deps lab m08-01
```

La medida de acceso dice «solo en localhost». Compárala con el paso 1: no se cumple.

**3. El rastro de una pieza.**

```bash
docker compose --profile lab run --rm --no-deps lab m08-02
grep AUD0007 data/predicciones.jsonl
```

```text
{"pieza_id": "AUD0007", "version": "defecto-0.1", "entrada": {"pieza_id": "AUD0007", "temperatura_c": 63.19, "vibracion_mm_s": 0.246, "corriente_a": 3.88, "presion_bar": 6.1}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}
```

Entrada, dictamen, versión y hora: con eso se responde a «por qué se aceptó esta pieza».

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M08-01 | [Evaluación de riesgos](M08-01-evaluacion-riesgos.md) | Marcar exposiciones de la arquitectura conectada. |
| M08-02 | [Gobierno y trazabilidad](M08-02-gobierno-trazabilidad.md) | Reconstruir qué modelo dictaminó una pieza. |

→ Empieza por **[M08-01 — Evaluación de riesgos](M08-01-evaluacion-riesgos.md)**.
