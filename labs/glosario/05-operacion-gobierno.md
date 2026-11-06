# Glosario 5 — Operación, MLOps y gobierno

[← Hoja anterior](04-ia-generativa.md) · [Índice del glosario](README.md)

Qué pasa cuando el modelo sale del laboratorio y entra en la línea: cómo se sirve, cómo actúa, cómo se vigila, cómo se protege y cómo se rinden cuentas. Lo usas del M06 al M08.

---

<a id="mapa"></a>
## 1. El mapa: cuánto decide el modelo

De menos a más autonomía. Cada escalón exige más garantías que el anterior.

| Modo | Qué hace el modelo | Quién decide | En el curso |
|------|--------------------|--------------|-------------|
| **Informar** | Enseña un dato o un resumen | La persona, sin propuesta | M01-02 (resumen del turno) |
| **Recomendar** | Da un dictamen: seguir o revisar | La persona | M06-02, M04-03 (zona de duda) |
| **Asistido** | Propone una acción concreta | La persona la aprueba y la ejecuta | M06-03 modo asistido, M07-03 |
| **Automático con límites** | Ejecuta la acción | El modelo, dentro de los límites que pone la máquina | M06-03 modo automático (refrigeración solo de 1 a 3) |
| ○ **Autónomo** | Decide y actúa sin límites externos | El modelo | No se hace en planta: nadie responde del resultado |

**Cómo se lee:** los límites **no los pone el modelo, los pone la máquina**. En el M06-03 la estación solo acepta niveles de refrigeración de 1 a 3, venga la orden de quien venga.

---

## 2. Los conceptos

<a id="inferencia"></a>
### Inferencia

**Qué es:** **usar** un modelo ya entrenado para dar una respuesta con datos nuevos. Entrenar se hace una vez y cuesta; inferir se hace con cada pieza y tiene que ser rápido.

**En la línea:** en el M06-01, la regresión logística tarda 0,35 ms por pieza en el edge; un ciclo dura 1 s.

**Lo usas en:** <!--usos:inferencia-->[M06](../M06-edge-integracion-ot/README.md) · [M06-01](../M06-edge-integracion-ot/M06-01-inferencia-edge.md) · [M07](../M07-mlops-observabilidad/README.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="latencia"></a>
### Latencia

**Qué es:** el tiempo desde que llega el dato hasta que sale la respuesta. Decide si una decisión llega **a tiempo**: un dictamen que llega después de que la pieza haya salido no sirve.

**Lo usas en:** <!--usos:latencia-->[M06](../M06-edge-integracion-ot/README.md) · [M06-01](../M06-edge-integracion-ot/M06-01-inferencia-edge.md)<!--/usos-->

<a id="api"></a>
### API de inferencia

**Qué es:** un servicio que recibe datos por HTTP y devuelve la respuesta del modelo. Cualquier aplicación de planta puede usarlo sin saber nada de Python ni del modelo.

**En la línea:** FastAPI en el puerto 8000. `/salud` dice si está vivo, la versión y la huella del modelo.

**Lo usas en:** <!--usos:api-->[M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="dictamen"></a>
### Dictamen

**Qué es:** la decisión del modelo sobre una pieza, publicada para que la usen otros sistemas: «seguir» o «revisar», con su probabilidad.

**En la línea:** se publica por MQTT en `linea/est01/dictamen`. La mejora del M06-02 le añade la hora y la versión del modelo, para poder rastrearlo.

**Lo usas en:** <!--usos:dictamen-->[M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M03-03](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [M04-03](../M04-vision-control-calidad/M04-03-inspeccion-camara.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-01](../M06-edge-integracion-ot/M06-01-inferencia-edge.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M07](../M07-mlops-observabilidad/README.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="consigna"></a>
### Consigna

**Qué es:** el valor que se le **pide** a un equipo (no el que mide): un nivel de refrigeración, una velocidad, una temperatura objetivo.

**En la línea:** `linea/est01/consigna`, nivel de refrigeración de 1 a 3. La estación rechaza lo que esté fuera.

**Lo usas en:** <!--usos:consigna-->[M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M05-04](../M05-ia-generativa/M05-04-agentes.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="mlops"></a>
### MLOps

**Qué es:** las prácticas para llevar modelos a producción y **mantenerlos**: versionar, desplegar, vigilar, detectar cuándo se degradan y reentrenar. Es lo mismo que se hace con el software, más lo propio de los modelos: sus datos cambian.

```text
datos → entrenar → evaluar → versionar → desplegar → vigilar ─┐
  ▲                                                          │
  └──────────────── reentrenar si hay deriva ◀───────────────┘
```

**Lo usas en:** <!--usos:mlops-->[M07](../M07-mlops-observabilidad/README.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M07-02](../M07-mlops-observabilidad/M07-02-monitorizacion.md)<!--/usos-->

<a id="version-huella"></a>
### Versión y huella del modelo

**Qué es:** la **versión** es una etiqueta que alguien escribe (`defecto-0.1`). La **huella** es un código calculado del propio fichero del modelo (los 12 primeros caracteres de su SHA-256): si cambia un solo byte, cambia la huella.

**Dónde se rompe:** en el M07-01 cambias la etiqueta a `defecto-0.2` sin tocar el modelo: la versión dice «modelo nuevo» y la huella sigue igual, `69a897cdf955`. Un auditor que solo mirara la versión se equivocaría. La etiqueta dice lo que alguien **cree** que hay; la huella, lo que **hay**.

**Lo usas en:** <!--usos:version-huella-->[M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M07](../M07-mlops-observabilidad/README.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="deriva"></a>
### Deriva

**Qué es:** cuando los datos de la línea **dejan de parecerse** a los del entrenamiento, y el modelo sigue contestando como si nada. No falla: se equivoca sin avisar.

| Tipo | Qué cambia | Ejemplo |
|------|------------|---------|
| **Deriva de datos** (el del curso) | Las señales de entrada | El husillo trabaja 8 °C más caliente tras cambiar el refrigerante |
| ○ **Deriva de concepto** | La relación entre señales y defecto | Un material nuevo falla a temperaturas que antes eran seguras |

**Cómo se detecta:** comparando con una **base**: en el M07-02, la tasa de piezas que manda a revisión con datos normales frente a la de los datos desplazados.

**Lo usas en:** <!--usos:deriva-->[M07](../M07-mlops-observabilidad/README.md) · [M07-02](../M07-mlops-observabilidad/M07-02-monitorizacion.md)<!--/usos-->

<a id="incidencia"></a>
### Incidencia

**Qué es:** el registro de un problema: qué alerta, cuándo, qué datos se reunieron, qué diagnóstico y qué acción se propuso. Sirve para actuar ahora y para aprender después.

**En la línea:** el agente del M07-03 escribe cada una en `infra/data/incidencias.jsonl`.

**Lo usas en:** <!--usos:incidencia-->[M07](../M07-mlops-observabilidad/README.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md)<!--/usos-->

<a id="superficie"></a>
### Superficie de ataque

**Qué es:** todo lo que alguien podría usar para entrar o hacer daño: puertos abiertos, servicios sin contraseña, registros escribibles.

**En la línea:** broker MQTT anónimo (1883), Modbus escribible (1502), OPC UA sin usuario (4840), todos abiertos a la red. En el M08-01, cualquiera puede publicar un dictamen falso o una consigna sin ser el modelo.

**Familia de medidas** (defensa en profundidad):

| Capa | Medida | En el curso |
|------|--------|-------------|
| Red | Que el servicio solo escuche en el propio equipo (127.0.0.1) o en una red de planta separada | M08-01, con `docker-compose.override.yml` |
| Identidad | Usuario y contraseña, o certificados | ○ (se señala) |
| Permisos | Mínimo privilegio: cada uno solo lo que necesita | El agente solo tiene herramientas de lectura |
| Máquina | Límites que no dependen de quién manda la orden | Refrigeración de 1 a 3 |
| Rastro | Registrar quién hizo qué | M08-02 |

**Lo usas en:** <!--usos:superficie-->[M08](../M08-ciberseguridad-gobierno/README.md)<!--/usos-->

<a id="autenticacion"></a>
### Autenticación

**Qué es:** comprobar **quién** es el que se conecta antes de dejarle leer o escribir. Sin autenticación, el sistema no distingue al modelo de cualquier otro.

**Lo usas en:** <!--usos:autenticacion-->[M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="trazabilidad"></a>
### Trazabilidad (el rastro)

**Qué es:** poder reconstruir, para cada decisión, **qué modelo la tomó, con qué datos, cuándo y quién la ejecutó**. En planta es lo que permite responder a una reclamación o a una auditoría.

**En la línea:** cada respuesta de la API lleva versión y huella, y queda en un fichero; en el M08-02 verificas que la huella del rastro coincide con el modelo desplegado.

**Lo usas en:** <!--usos:trazabilidad-->[M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M04-03](../M04-vision-control-calidad/M04-03-inspeccion-camara.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M07-01](../M07-mlops-observabilidad/M07-01-servicio-inferencia.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->

<a id="gobierno"></a>
### Gobierno de la IA y Reglamento europeo

**Qué es:** las reglas de la empresa para decidir **qué IA se usa, para qué, con qué supervisión y quién responde**. El **Reglamento europeo de IA** (*AI Act*) clasifica los sistemas por riesgo y exige más cuanto más pueden afectar a personas o seguridad.

**En la línea:** el sistema del curso **asiste**: recomienda seguir o revisar, no decide solo ni toca el paro. Esa clasificación (quién decide, sobre qué, con qué supervisión) es lo que se documenta.

**Lo usas en:** <!--usos:gobierno-->[M08](../M08-ciberseguridad-gobierno/README.md) · [M08-02](../M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md)<!--/usos-->
