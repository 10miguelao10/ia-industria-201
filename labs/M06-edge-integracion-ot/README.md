# M06 — Edge AI e integración industrial

[← Página anterior](../M05-ia-generativa/M05-05-modelos-abiertos.md) · [Siguiente página →](M06-01-inferencia-edge.md)

> [!NOTE]
> **Cómo funciona este módulo.** Tiene tres bloques, uno por laboratorio. En cada bloque: primero la **teoría** y una **demostración** que se proyecta en clase, paso a paso; después **practicas tú** con el laboratorio, a tu ritmo.

## Qué aprenderás

- Qué es ejecutar un modelo en el **[edge](../glosario/01-datos-arquitectura.md#edge)**, junto a la máquina, y cómo se mide si llega a tiempo.
- Cómo llega el [dictamen](../glosario/05-operacion-gobierno.md#dictamen) de un modelo al **automatismo** sin que el modelo toque el control.
- Cómo un modelo de **[comportamiento normal](../glosario/03-aprendizaje-automatico.md#banda-normal)** puede **predecir** una [anomalía](../glosario/03-aprendizaje-automatico.md#anomalia) antes de que salte la alarma, y qué supone dejarle **actuar**.

| Bloque | Concepto | Laboratorio |
|--------|----------|-------------|
| 1 | [Inferencia](../glosario/05-operacion-gobierno.md#inferencia) en el edge | [M06-01](M06-01-inferencia-edge.md) |
| 2 | Integración con [OT](../glosario/01-datos-arquitectura.md#ot) | [M06-02](M06-02-integracion-ot.md) |
| 3 | Predicción y actuación supervisada | [M06-03](M06-03-prediccion-actuacion.md) |

## Antes de empezar

Los bloques 1 y 2 usan el modelo de defecto del M03-03 (`infra/data/modelo_defecto.joblib`). El bloque 3 usa [Prometheus](../glosario/02-observabilidad.md#prometheus) (M01-03) con al menos 10 minutos de [métricas](../glosario/02-observabilidad.md#metrica) normales.

```bash
cd infra
docker compose up -d mosquitto sensor archivador modbus prometheus
docker compose stop llm      # el modelo de lenguaje no hace falta en este módulo
```

## Introducción: del modelo a la máquina

Hasta ahora, los modelos se entrenaban y se medían. En este módulo **se ponen junto a la línea**: el modelo tiene que dictaminar cada carcasa a tiempo, su dictamen tiene que llegar a quien actúa, y, en el último bloque, el sistema tiene que adelantarse a un problema.

```
 estación ──▶ equipo edge (modelo) ──▶ dictamen o previsión ──▶ automatismo / operario ──▶ acción
                                                                      │
                                              el paro de seguridad ───┘ sigue siendo del PLC
```

La frontera que no se cruza: **el modelo recomienda; el automatismo y las personas deciden**, con sus propias protecciones.

---

## Bloque 1 — Inferencia en el edge

### Teoría

El **edge** es el equipo que está junto a la máquina. Ejecutar el modelo ahí, cargándolo desde su disco, evita depender de la red de la oficina o de internet, y da la respuesta en el momento.

Lo que se mide es la **[latencia](../glosario/05-operacion-gobierno.md#latencia)**: cuánto tarda el dictamen de una pieza. Tiene que ser mucho menor que el [tiempo de ciclo](../glosario/01-datos-arquitectura.md#tiempo-ciclo) de la máquina (aquí, ~1 s).

### Demostración

**Qué se demuestra:** que un modelo clásico es un fichero pequeño que cabe en cualquier equipo. En el laboratorio medirás si llega a tiempo.

#### Paso 1 — Los modelos del curso, en disco

```bash
ls -l data/*.joblib
```

**Resultado esperado** (los que hayas generado):

```text
   823 … data/detector_anomalia.joblib
  2569 … data/modelo_defecto.joblib
  1279 … data/modelo_logreg.joblib
  2911 … data/modelo_vision.joblib
219108 … data/modelo_vision_red.joblib
```

**Cómo se lee:** el modelo de defecto que va a la línea ocupa **2,5 KB**. La red neuronal de visión, 214 KB. El [modelo de lenguaje](../glosario/04-ia-generativa.md#llm) del M05, [470 MB](../glosario/04-ia-generativa.md#cuantizacion).

| Modelo | Tamaño | Dónde cabe |
|--------|--------|------------|
| Árbol de defecto | 2,5 KB | En cualquier equipo, incluso en un PLC moderno |
| Red de visión | 214 KB | En cualquier equipo edge |
| Modelo de lenguaje | 470 MB | En un PC industrial con memoria suficiente |

> **Qué señalar en pantalla:** «Edge no significa un equipo especial. Con modelos como estos, el propio PC de la estación sirve».

#### Paso 2 — La pregunta que abre el laboratorio

> **¿Cuánto tarda este modelo en decidir sobre una carcasa? ¿Le da tiempo antes de que salga la siguiente?**

### Ahora tú: M06-01

→ **[M06-01 — Inferencia en entornos edge](M06-01-inferencia-edge.md)**

Medirás la latencia del modelo en el puesto, compararás dos modelos y verás qué parte del tiempo es el modelo y cuál todo lo demás.

---

## Bloque 2 — Integración con OT

### Teoría

El dictamen tiene que llegar al **automatismo** que desvía la pieza. La forma de hacerlo sin que el modelo toque el PLC es la misma que para los registros: se publica como **evento** en el [broker](../glosario/01-datos-arquitectura.md#broker), en el [tema](../glosario/01-datos-arquitectura.md#tema) `linea/est01/dictamen`, y el automatismo está suscrito. El **paro de seguridad** va por su camino determinista y nunca depende del modelo.

### Demostración

**Qué se demuestra:** que publicar un dictamen no cambia nada en el control. En el laboratorio lo publicará el modelo de verdad.

#### Paso 1 — Escuchar todo lo que pasa en la estación

En una terminal, nos suscribimos a todos los temas de la estación:

```bash
# El comodín # recoge todos los temas que cuelgan de linea/est01/
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/#' -v
```

Pasan los registros `linea/est01/ciclo` de cada carcasa.

#### Paso 2 — Publicar un dictamen a mano

En otra terminal, publicamos un dictamen como lo haría un modelo:

```bash
docker compose exec mosquitto mosquitto_pub -t 'linea/est01/dictamen' \
  -m '{"pieza_id": "P0100", "decision": "revisar", "probabilidad": 0.91}'
```

**Resultado esperado** en la primera terminal, entre los registros:

```text
linea/est01/dictamen {"pieza_id": "P0100", "decision": "revisar", "probabilidad": 0.91}
```

#### Paso 3 — El paro de seguridad no se ha movido

```bash
# Registro Modbus 10: el paro de seguridad
docker compose --profile lab run --rm --no-deps lab modbus 10 1
```

**Resultado esperado:**

```text
registro  valor_crudo
      10            0
OK modbus: 1 registros leídos desde el 10
```

**Cómo se lee:** el dictamen ha viajado por el broker para quien quiera escucharlo, y el paro de seguridad sigue en 0. Publicar un evento **no actúa** sobre la máquina: el automatismo decide qué hace con él.

> **Qué señalar en pantalla:** «Cualquiera puede publicar un dictamen en el broker, igual que acabo de hacer yo. ¿Debería el automatismo fiarse de cualquier mensaje? Lo veréis en el M08».

#### Paso 4 — La pregunta que abre el laboratorio

> **¿Qué tiene que llevar un dictamen para que el automatismo sepa a qué carcasa se refiere y si debe hacerle caso?**

### Ahora tú: M06-02

→ **[M06-02 — Integración con sistemas industriales](M06-02-integracion-ot.md)**

Dejarás que el modelo dictamine la carcasa que acaba de salir y publique el evento, comprobarás que el paro sigue en reposo y verás qué pasa con el flujo de piezas si el [umbral](../glosario/03-aprendizaje-automatico.md#umbral) está mal puesto.

---

## Bloque 3 — Predicción y actuación supervisada

### Teoría

Las [alertas](../glosario/02-observabilidad.md#alerta) del M01-03 son **reactivas**: saltan cuando la temperatura ya ha pasado de 70 °C, y para entonces ya se han fabricado piezas malas. Un modelo que conoce el **comportamiento normal** de la estación puede ver la **tendencia** antes y **predecir** cuándo se cruzará el margen.

```
 1. aprender lo normal (métricas de Prometheus) ──▶ 2. vigilar: ¿se sale de lo normal? ¿hacia dónde va?
                                                         │
                                                         ▼
                                3. prever cuándo llegará a 70 °C ──▶ 4. proponer (o aplicar) una acción
```

Que el sistema **actúe** solo es una decisión seria. Hay dos modos:

| Modo | Quién actúa | Uso real |
|------|-------------|----------|
| **Asistido** | El modelo propone; el operario confirma y actúa | Lo habitual en planta |
| **Automático con límites** | El modelo actúa, pero solo dentro de un rango que la máquina permite | Poco frecuente, con validación de seguridad |

### Demostración

**Qué se demuestra:** cómo es un fallo que va a más y lo tarde que avisa una alerta fija. En el laboratorio enseñarás a un modelo lo normal y verás si se adelanta.

#### Paso 1 — Provocar un fallo de refrigeración

**Qué vamos a ver:** la simulación permite provocar un fallo: la refrigeración deja de funcionar bien y el husillo se calienta poco a poco.

```bash
docker compose --profile lab run --rm --no-deps lab evento fallo-refrigeracion
```

```text
OK evento: enviado «fallo-refrigeracion» a la estación por linea/est01/evento
```

#### Paso 2 — Mirarlo subir

**Qué vamos a ver:** la temperatura en Prometheus. En <http://localhost:9090/graph>, pestaña **Graph**, rango de 15 minutos:

```promql
estacion_temperatura_husillo_celsius
```

Durante unos tres minutos, la curva sube a unos 3 °C por minuto. Mientras tanto, <http://localhost:9090/alerts> sigue en verde.

**Resultado esperado:** al pasar de 70 °C, `TemperaturaHusilloAlta` pasa a **pending** y, a los 5 segundos, a **firing**.

**Cómo se lee:** la alerta ha avisado **cuando el problema ya estaba ahí**. Durante los dos o tres minutos anteriores, la subida era evidente en la gráfica y nadie avisó, porque la regla solo mira si se pasa de 70.

> **Qué señalar en pantalla:** «Todas las carcasas de esos dos minutos se fabricaron con el husillo cada vez más caliente. ¿Podríamos haberlo visto venir?».

#### Paso 3 — Volver a la normalidad

```bash
docker compose --profile lab run --rm --no-deps lab evento fin
docker compose --profile lab run --rm --no-deps lab consigna 3   # más refrigeración para recuperar antes
# … cuando baje de 63 °C:
docker compose --profile lab run --rm --no-deps lab consigna 1
```

#### Paso 4 — La pregunta que abre el laboratorio

> **Si un sistema hubiera aprendido cómo se comporta la estación cuando va bien, ¿cuánto antes podría haber avisado? ¿Le dejaríais subir la refrigeración por su cuenta?**

### Ahora tú: M06-03

→ **[M06-03 — Predicción y actuación supervisada](M06-03-prediccion-actuacion.md)**

Exportarás métricas de Prometheus, enseñarás a un modelo cómo se comporta la estación cuando va bien, provocarás el fallo y verás cómo se adelanta a la alerta en modo asistido y en modo automático, y descubrirás qué pasa si lo entrenas con datos que ya incluían el fallo.

---

## Conclusiones del módulo

### Qué es llevar la IA a la máquina

Ejecutar el modelo donde se produce el dato, hacer llegar su resultado a quien actúa y, si se quiere, adelantarse a los problemas, **sin quitarle al automatismo el control de la seguridad**.

### Cómo debe hacerse

| Requisito | Dónde lo has trabajado |
|-----------|------------------------|
| Medir la latencia en el equipo real, frente al tiempo de ciclo | M06-01 |
| El dictamen como evento, con la pieza a la que se refiere | M06-02 |
| El paro de seguridad, siempre fuera del alcance del modelo | M06-02, M06-03 |
| Aprender lo normal con datos limpios y sin anomalías | M06-03 |
| Actuar solo dentro de los límites que impone la máquina | M06-03 |

### Lo que has visto romperse

| Fallo | Dónde | Qué enseña |
|-------|-------|------------|
| Un umbral mal puesto manda todas las piezas a revisión | M06-02 | El umbral es una decisión de proceso |
| Una alerta fija que avisa cuando ya es tarde | Demo del bloque 3 | Reaccionar no es prevenir |
| Un modelo entrenado con el fallo dentro que lo considera normal | M06-03 | Lo normal tiene que ser normal de verdad |

### En una frase

> 🔑 El modelo junto a la máquina puede adelantarse a los problemas, pero el control de la seguridad nunca pasa por él: propone, y si actúa, lo hace dentro de los límites que pone la máquina.
