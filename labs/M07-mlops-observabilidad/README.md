# M07 — Operación, MLOps y observabilidad

[← Página anterior](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [Siguiente página →](M07-01-servicio-inferencia.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Exponer el modelo como un servicio que otra aplicación puede llamar.
- Guardar una versión identificable del modelo.
- Detectar que el servicio empeora cuando los datos ya no se parecen a los del entrenamiento.

## Teoría

Entrenar en un cuaderno no es operar. Operar es que otra pieza del sistema pueda pedir un dictamen, que se sepa qué versión contestó y que alguien note si esa versión deja de servir.

### Qué vigilar

| Señal | Pregunta |
|-------|----------|
| El servicio responde | ¿Hay errores y tiempos raros? |
| La entrada cambia | ¿Las señales de hoy se parecen a las del entrenamiento? |
| La salida cambia | ¿De repente casi todo es defecto, o casi nada lo es? |
| La versión | ¿Qué fichero de modelo contestó esta pieza? |

Reentrenar es la respuesta cuando el proceso ha cambiado (utillaje, material, receta), no un reflejo semanal. Primero se ve la degradación; después se decide.

Contenerizar —empaquetar servicio y dependencias para llevarlo a otra máquina— es parte de este relato. En el laboratorio el servicio es un proceso del puesto, con versión y contrato claros, que es lo que la operación necesita aunque el paquete final sea otro.

## Demostración guiada

Se publica el modelo de defecto como servicio local y se le alimenta con datos desplazados para ver la degradación antes de hablar de reentrenar.

Todo se lanza desde `infra/`, con el modelo de M03-03.

**1. El modelo como servicio, con versión.**

```bash
docker compose up -d api
curl -s http://localhost:8000/salud
curl -s -X POST http://localhost:8000/predecir -H 'Content-Type: application/json' \
  -d '{"pieza_id": "DEMO1", "temperatura_c": 61.4, "vibracion_mm_s": 0.25, "corriente_a": 4.1, "presion_bar": 6.0}'
```

```json
{"estado":"ok","version":"defecto-0.1"}
{"pieza_id":"DEMO1","version":"defecto-0.1","entrada":{…},"dictamen":"seguir","probabilidad":0.0798,"ts":"…"}
```

**2. La misma pieza, 8 °C más caliente.**

```bash
curl -s -X POST http://localhost:8000/predecir -H 'Content-Type: application/json' \
  -d '{"pieza_id": "DEMO2", "temperatura_c": 69.4, "vibracion_mm_s": 0.25, "corriente_a": 4.1, "presion_bar": 6.0}'
```

```json
{"pieza_id":"DEMO2","version":"defecto-0.1","entrada":{…},"dictamen":"revisar","probabilidad":1.0,"ts":"…"}
```

**3. La deriva en un lote.**

```bash
docker compose --profile lab run --rm --no-deps lab m07-02
```

📋 Ficha del comando [`m07-02`](../comandos-lab.md#m07-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
tasa_base=0.08 tasa_desplazada=0.96
OK m07-02: base=0.08 desplazada=0.96
```

Si la estación «se ha ido» 8 °C, casi todo va a revisión. El modelo no avisa de que ya no sirve: hay que vigilar la tasa.

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M07-01 | [Publicación de servicios de inferencia](M07-01-servicio-inferencia.md) | Dejar el modelo llamable por otras aplicaciones. |
| M07-02 | [Monitorización y seguimiento operacional](M07-02-monitorizacion.md) | Ver rendimiento y degradación del modelo desplegado. |

→ Empieza por **[M07-01 — Publicación de servicios de inferencia](M07-01-servicio-inferencia.md)**.

## Conclusiones del módulo

Al terminar los laboratorios de este módulo deberías tener claro que:

- Un modelo en operación se publica como servicio, con versión en cada respuesta y registro de cada consulta.
- Un modelo no avisa de que ha dejado de servir: hay que vigilar su comportamiento frente a una línea base.
- Que el servicio esté caído y que el modelo esté desfasado son problemas distintos, con soluciones distintas.
