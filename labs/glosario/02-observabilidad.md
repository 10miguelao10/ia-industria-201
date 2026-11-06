# Glosario 2 — Observabilidad y alertas

[← Hoja anterior](01-datos-arquitectura.md) · [Índice del glosario](README.md) · [Siguiente hoja →](03-aprendizaje-automatico.md)

Cómo se sabe, desde fuera, si la línea y sus sistemas están haciendo su trabajo. Lo usas en el M01 y vuelve en el M06 y el M07.

---

<a id="observabilidad"></a>
### Observabilidad

**Qué es:** la capacidad de saber **qué está pasando dentro** de un sistema mirando lo que publica hacia fuera: métricas, registros y trazas. No basta con saber que un servicio está **vivo**: hay que saber si está **haciendo su trabajo**.

**En la línea:** el archivador puede estar vivo (`up = 1`) y no guardar nada (M01-03). Solo una métrica de su trabajo, la hora del último registro, lo delata.

**Lo usas en:** <!--usos:observabilidad-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md)<!--/usos-->

<a id="metrica"></a>
### Métrica: contador e indicador

**Qué es:** un número con nombre que un servicio publica y que se lee cada cierto tiempo. Hay dos tipos básicos:

| Tipo | Qué hace | Ejemplo en la línea | Cómo se lee |
|------|----------|---------------------|-------------|
| **Contador** (*counter*) | Solo sube; vuelve a 0 si el servicio se reinicia | `estacion_piezas_fabricadas_total` | Lo que importa es **cuánto sube** en un intervalo |
| **Indicador** (*gauge*) | Sube y baja | `estacion_temperatura_husillo_celsius` | Lo que importa es **su valor ahora** |

**En la línea:** la estación las publica en el puerto 9102 y el archivador en el 9101, en `/metrics`.

**Lo usas en:** <!--usos:metrica-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md)<!--/usos-->

<a id="prometheus"></a>
### Prometheus y scrape

**Qué es:** una base de datos de **series temporales** para métricas. No espera a que le manden datos: **va a buscarlos** (*scrape*) a cada servicio cada cierto tiempo y guarda cada valor con su hora.

**En la línea:** puerto 9090; lee la estación y el archivador **cada 5 s**. Si un servicio no contesta, su serie `up` pasa a 0.

**Familia:**

| Herramienta | Modelo | Cuándo se elige |
|-------------|--------|-----------------|
| **Prometheus** (el del curso) | Va a buscar las métricas | Servicios propios, contenedores, equipos edge |
| InfluxDB, TimescaleDB | Le mandan los datos | Telemetría de sensores a alta frecuencia |
| Historian industrial (PI, etc.) | Lo alimenta el SCADA | Planta con SCADA ya instalado |

**Lo usas en:** <!--usos:prometheus-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M05](../M05-ia-generativa/README.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M07](../M07-mlops-observabilidad/README.md) · [M07-02](../M07-mlops-observabilidad/M07-02-monitorizacion.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md)<!--/usos-->

<a id="serie-temporal"></a>
### Serie temporal

**Qué es:** una secuencia de valores de una misma cosa, cada uno con su hora: la temperatura del husillo cada 5 s, por ejemplo.

**Lo usas en:** <!--usos:serie-temporal-->[M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md)<!--/usos-->

<a id="promql"></a>
### PromQL: rate, increase y predict_linear

**Qué es:** el lenguaje de consultas de Prometheus. Trabaja sobre **ventanas de tiempo**, entre corchetes (`[1m]` = el último minuto).

| Función | Qué devuelve | Ejemplo en la línea |
|---------|--------------|---------------------|
| `increase(x[1m])` | Cuánto ha subido un contador en la ventana | Piezas fabricadas en el último minuto |
| `rate(x[1m])` | Lo mismo, por segundo | Piezas por segundo |
| `count_over_time(x[5m])` | Cuántas muestras hay en la ventana | Si faltan, el scrape falló |
| `predict_linear(x[2m], 300)` | Dónde estará el valor dentro de 300 s si sigue la tendencia | ¿Pasará la temperatura de 70 °C en 5 min? |

**Dónde se rompe:** `predict_linear` traza una recta: si la subida se acelera, llega tarde; si es ruido, da falsas alarmas.

**Lo usas en:** <!--usos:promql-->[M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md)<!--/usos-->

<a id="alerta"></a>
### Alerta y tiempo `for`

**Qué es:** una regla que Prometheus evalúa sin parar. Si la condición se cumple, la alerta pasa a **pendiente**; si se sigue cumpliendo durante el tiempo `for`, pasa a **disparada**.

**En la línea:** `infra/prometheus/alertas.yml`. Por ejemplo, `HistoricoSinDatos` se dispara si el último registro tiene más de 15 s durante 5 s seguidos.

**Dónde se rompe:** sin `for`, un pico aislado dispara la alerta (ruido); con un `for` demasiado largo, el aviso llega tarde.

| | Alerta de estado | Alerta de trabajo | Alerta predictiva |
|--|------------------|-------------------|-------------------|
| Pregunta | ¿Está vivo? | ¿Hace lo que debe? | ¿Va a pasar algo? |
| En la línea | `EstacionCaida` | `HistoricoSinDatos`, `RegistrosPerdidos` | `predict_linear` (M06-03) |

**Lo usas en:** <!--usos:alerta-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M07](../M07-mlops-observabilidad/README.md) · [M07-02](../M07-mlops-observabilidad/M07-02-monitorizacion.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md)<!--/usos-->

<a id="kpi"></a>
### Indicador de proceso, KPI y OEE

**Qué es:** un **indicador de proceso** dice cómo está la máquina ahora (temperatura, vibración). Un **KPI** (*Key Performance Indicator*) dice cómo rinde la producción. El más usado en planta es el **OEE**: disponibilidad × rendimiento × calidad.

**En la línea:** el panel enseña indicadores de proceso; el tiempo de ciclo y las microparadas son la base del rendimiento.

**Lo usas en:** <!--usos:kpi-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md)<!--/usos-->

<a id="frescura"></a>
### Frescura del dato

**Qué es:** cuánto tiempo ha pasado desde el **último dato** recibido. Una pantalla que enseña valores sin su hora puede estar mostrando datos de hace una hora como si fueran de ahora.

**En la línea:** la mejora del M01-02 añade al panel la hora del último dato y un aviso si es antigua.

**Lo usas en:** <!--usos:frescura-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md)<!--/usos-->
