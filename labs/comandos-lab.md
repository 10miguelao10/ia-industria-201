# Fichas de los comandos `lab`

[← Volver al índice del curso](../README.md)

En los laboratorios, muchas comprobaciones se lanzan así:

```bash
docker compose --profile lab run --rm --no-deps lab m01-01
```

| Parte | Qué significa |
|-------|---------------|
| `docker compose run` | Arranca un contenedor para hacer **una tarea** y terminar |
| `--profile lab` | El servicio `lab` está oculto tras un perfil; esto lo activa |
| `--rm` | Borra el contenedor al terminar |
| `--no-deps` | No arranca otros servicios: usa los que ya estén en marcha |
| `lab` | El contenedor con Python, las librerías y el código del curso |
| `m01-01` | **Qué comprobación ejecuta**: una de las fichas de esta página |

Por dentro, `lab m01-01` ejecuta `python -m linea.cli m01-01`, es decir, la función `cmd_m01_01` de [`infra/linea/cli.py`](../infra/linea/cli.py). Todo lo que lee o escribe en `/data` aparece en `infra/data/` de tu equipo.

Cada ficha dice qué hace el comando en palabras, qué necesita en marcha, qué lee, qué deja escrito y cuándo da `OK` o `FALLO`.

---

## M01 — Arquitectura y supervisión

### m01-01

**Qué hace:** comprueba que el registro de una pieza recorre los tres tramos (origen, transporte y almacén) y que no se pierde.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `archivador` |
| Lee | `historial.sqlite` (cuenta los registros guardados) · el tema MQTT `linea/est01/ciclo` (espera un registro hasta 15 s) · `estado.json` (lo último que la estación dice haber fabricado) |
| Escribe | Nada |
| `OK` si | Hay registros en el histórico, llega uno por MQTT y es de la misma estación y de una pieza cercana a la del estado |
| `FALLO` si | El histórico está vacío tras 25 s · no llega ningún registro por MQTT · el registro y el estado no cuadran |

Se usa en [M01-01](M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md).

### m01-02

**Qué hace:** comprueba que el panel del turno responde y cuenta, directamente en el histórico, cuántas lecturas pasan de 70 °C.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `archivador`, `panel` |
| Lee | La página del panel (`http://panel:8501`) · las temperaturas de `historial.sqlite` |
| Escribe | Nada |
| `OK` si | El panel contesta sin error y hay al menos 2 registros en el histórico |
| `FALLO` si | El panel no responde o el histórico tiene menos de 2 registros |

Se usa en [M01-02](M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md).

---

## M02 — Captura, integración y preparación de datos

### m02-01

**Qué hace:** se suscribe al tema de la estación, como haría cualquier sistema que quiere enterarse de cada pieza, y comprueba que el registro trae los campos necesarios.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor` |
| Lee | El tema MQTT `linea/est01/ciclo` (espera un registro hasta 15 s) |
| Escribe | Nada |
| `OK` si | Llega un registro con `pieza_id`, `temperatura_c`, `vibracion_mm_s` y `ts` |
| `FALLO` si | No llega nada o falta algún campo |

Se usa en [M02-01](M02-captura-integracion-datos/M02-01-telemetria.md).

### m02-01-pausa

**Qué hace:** escucha el tema durante 3 segundos con la estación parada. Comprueba que el silencio es silencio y que nada inventa lecturas.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, con `sensor` **parado** |
| Lee | El tema MQTT `linea/est01/ciclo` durante 3 s |
| Escribe | Nada |
| `OK` si | **No** llega ningún registro |
| `FALLO` si | Llega algún registro (la estación no estaba parada o hay otra publicando) |

Se usa en [M02-01](M02-captura-integracion-datos/M02-01-telemetria.md).

### m02-02

**Qué hace:** lee la temperatura del husillo por los tres caminos (el estado que publica MQTT, el nodo OPC-UA y el registro Modbus) y comprueba que dicen lo mismo.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `opcua`, `modbus` |
| Lee | `estado.json` · nodo OPC-UA `Estacion` → `Temperatura` · registro Modbus 0, dividido entre 10 |
| Escribe | Nada |
| `OK` si | OPC-UA y Modbus quedan a menos de 1,5 °C del estado |
| `FALLO` si | OPC-UA o Modbus no responden, o el valor no cuadra (por ejemplo, si no se divide entre 10) |

Se usa en [M02-02](M02-captura-integracion-datos/M02-02-protocolos.md).

### m02-03

**Qué hace:** genera un histórico de 800 piezas con los problemas típicos de planta (huecos, valores en décimas y sensores clavados en 9999), lo limpia y cuenta lo que se descarta.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Nada: el histórico lo genera el propio comando |
| Escribe | `crudo.csv` (tal cual) · `limpio.csv` (una fila por pieza, en grados) · `imposibles.csv` (los 9999). Los sobrescribe si ya existían |
| `OK` si | En el limpio hay una fila por pieza, todas las temperaturas están entre 40 y 120 °C y se apartaron los 9999 |
| `FALLO` si | Quedan piezas repetidas, temperaturas sin escalar o no se apartó ningún 9999 |

Se usa en [M02-03](M02-captura-integracion-datos/M02-03-preparacion-datos.md).

---

## M03 — Predicción y anomalías

### m03-01

**Qué hace:** entrena un modelo de regresión logística que relaciona las señales de cada pieza con el defecto que marcó calidad. Entrena con el 70 % más antiguo y lo examina con el 30 % más reciente.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `limpio.csv` (si falta, lo genera como `m02-03`) |
| Escribe | `modelo_logreg.joblib` |
| `OK` si | Encuentra al menos el 45 % de los defectos del tramo de examen |
| `FALLO` si | Encuentra menos del 45 % |

Se usa en [M03-01](M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md).

### m03-02

**Qué hace:** aprende cómo es un ciclo normal con piezas sin defecto. Después revisa 200 ciclos nuevos, 20 de ellos con la vibración subida a propósito, y cuenta cuántos de esos 20 avisa.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Nada: genera sus propios ciclos normales (400) y los 200 de vigilancia |
| Escribe | `detector_anomalia.joblib` |
| `OK` si | Avisa al menos el 70 % de los ciclos alterados |
| `FALLO` si | Avisa menos del 70 % |

Se usa en [M03-02](M03-ml-prediccion-anomalias/M03-02-anomalias.md).

### m03-03

**Qué hace:** entrena dos modelos candidatos (regresión logística y árbol de decisión) con las mismas piezas, elige uno con la regla acordada (más defectos encontrados y, si empatan, menos falsas alarmas) y lo deja listo para la línea.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `limpio.csv` |
| Escribe | `modelo_defecto.joblib` (el ganador) · `VERSION` (`defecto-0.1`) · `modelo_elegido.txt` (`arbol` o `logreg`) |
| `OK` si | Siempre que termine: no tiene umbral mínimo |
| `FALLO` si | Falta `limpio.csv` (sale un error de Python, no un `FALLO`) |

Se usa en [M03-03](M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md). Los comandos de M06, M07 y M08 usan el modelo que deja.

---

## M04 — Visión

### m04-01

**Qué hace:** genera 80 fotos de carcasas (40 buenas y 40 con un rayón), entrena un modelo que las distingue y lo examina con fotos que no ha visto.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `imagenes/manifiesto.csv` (si falta, genera las fotos) |
| Escribe | `imagenes/buenas/*.png` · `imagenes/defectuosas/*.png` · `imagenes/manifiesto.csv` · `modelo_vision.joblib` |
| `OK` si | Acierta al menos el 85 % de las fotos de examen |
| `FALLO` si | Acierta menos del 85 % |

Se usa en [M04-01](M04-vision-control-calidad/M04-01-clasificacion-componentes.md).

### m04-02

**Qué hace:** busca en 5 fotos defectuosas la fila donde está el rayón (la más brillante) y la compara con la fila real. Después mira 3 fotos buenas para ver si alguna tendría una fila igual de brillante.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | Las fotos y `imagenes/manifiesto.csv` (si faltan, las genera) |
| Escribe | Nada |
| `OK` si | En las 5 defectuosas acierta la fila con un margen de 2 filas |
| `FALLO` si | Falla la fila en alguna defectuosa. Las buenas con marca se cuentan, pero no hacen fallar |

Se usa en [M04-02](M04-vision-control-calidad/M04-02-deteccion-defectos.md).

### m04-03

**Qué hace:** simula el puesto de inspección. Copia 6 fotos (3 buenas y 3 malas) a una carpeta de entrada, da a cada una su probabilidad de defecto y deja un registro con `aceptar` o `revisar`.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_vision.joblib` (si falta, lo entrena como `m04-01`) · las fotos |
| Escribe | `lote_entrada/*.png` · `lote_resultado.csv` |
| `OK` si | Hay una fila por foto (6) y al menos una va a `revisar` |
| `FALLO` si | Faltan filas o ninguna pieza va a revisión |

Se usa en [M04-03](M04-vision-control-calidad/M04-03-inspeccion-camara.md).

---

## M05 — IA generativa

### m05-01

**Qué hace:** comprueba que el modelo de lenguaje del puesto está listo, le pide que diga «hola» y mide cuánto tarda.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | `http://llm:8088/salud` · la respuesta del modelo |
| Escribe | Nada |
| `OK` si | El servicio local responde y devuelve un texto no vacío |
| `FALLO` si | El servicio no responde o la respuesta llega vacía |

Se usa en [M05-01](M05-ia-generativa/M05-01-modelo-local.md).

### m05-02

**Qué hace:** hace de aplicación. Pide un texto al modelo por HTTP y luego llama a un servicio que no existe, para comprobar que el fallo se ve como un error de red.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | La respuesta de `http://llm:8088/v1/chat/completions` |
| Escribe | Nada |
| `OK` si | Hay respuesta del modelo y la llamada al servicio inexistente da error de red |
| `FALLO` si | La respuesta llega vacía o el servicio inexistente contesta |

Se usa en [M05-02](M05-ia-generativa/M05-02-integracion-aplicacion.md).

### m05-03

**Qué hace:** pregunta el par de apriete del tornillo de la brida. Primero busca el párrafo del procedimiento que más palabras comparte con la pregunta, y después pide al modelo que conteste usando solo ese párrafo.

| | |
|--|--|
| Necesita en marcha | `llm` |
| Lee | `linea/docs/procedimiento-est01.md` · la respuesta del modelo |
| Escribe | Nada |
| `OK` si | El párrafo encontrado contiene 12 y la respuesta del modelo también (lo intenta hasta 3 veces) |
| `FALLO` si | No encuentra el párrafo del par o el modelo no da el 12 en 3 intentos |

Se usa en [M05-03](M05-ia-generativa/M05-03-asistente-documentacion.md).

### m05-03-ausente

**Qué hace:** busca en el procedimiento un párrafo sobre el color del tornillo de recambio, un tema que el documento no trata.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`). **No llama al modelo** |
| Lee | `linea/docs/procedimiento-est01.md` |
| Escribe | Nada |
| `OK` si | El párrafo más parecido no habla de color ni de recambio, así que no hay nada que pasar al modelo |
| `FALLO` si | Aparece un párrafo sobre ese tema |

Se usa en [M05-03](M05-ia-generativa/M05-03-asistente-documentacion.md). Comprueba la recuperación del documento, no lo que diría el modelo.

### m05-04

**Qué hace:** simula un agente con una única herramienta, `leer_estacion`. El código lee la temperatura actual, la apunta en una traza y pide al modelo una frase con ese número. Después rechaza una petición de escritura en el automatismo.

| | |
|--|--|
| Necesita en marcha | `llm`, `sensor` |
| Lee | `estado.json` · la respuesta del modelo |
| Escribe | `traza_agente.jsonl` (herramienta usada y valor leído) |
| `OK` si | La frase del modelo contiene el número leído (lo intenta hasta 3 veces) y queda la traza |
| `FALLO` si | El modelo cambia el número en los 3 intentos o no queda traza |

Se usa en [M05-04](M05-ia-generativa/M05-04-agentes.md). El rechazo de escritura es un texto fijo del código: el agente no puede escribir porque no existe esa herramienta, no porque el modelo decida negarse.

---

## M06 — Edge e integración OT

### m06-01

**Qué hace:** carga el modelo de defecto desde el disco del puesto, dictamina la misma pieza 20 veces seguidas y calcula el tiempo medio por pieza. La primera predicción, que incluye la carga, no cuenta.

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_defecto.joblib` · la primera pieza de `limpio.csv` |
| Escribe | Nada |
| `OK` si | Tarda menos de 200 ms por pieza |
| `FALLO` si | Falta el modelo o tarda 200 ms o más |

Se usa en [M06-01](M06-edge-integracion-ot/M06-01-inferencia-edge.md).

### m06-02

**Qué hace:** dictamina la pieza que acaba de salir de la estación, publica el dictamen como evento para el automatismo y comprueba que el paro de seguridad no se ha tocado.

| | |
|--|--|
| Necesita en marcha | `mosquitto`, `sensor`, `modbus` |
| Lee | `modelo_defecto.joblib` · `estado.json` (la presión se fija en 6 bar) · el tema `linea/est01/dictamen` · registro Modbus 10 |
| Escribe | Publica un evento en `linea/est01/dictamen` |
| `OK` si | El evento llega, es de la misma pieza y el registro 10 sigue en 0 |
| `FALLO` si | El evento no llega, es de otra pieza o el paro cambió |

Se usa en [M06-02](M06-edge-integracion-ot/M06-02-integracion-ot.md).

---

## M07 — Operación y observabilidad

### m07-01

**Qué hace:** llama al servicio de inferencia como lo haría una aplicación de planta. Primero manda una pieza completa, `SRV0001`, y después una sin señales.

| | |
|--|--|
| Necesita en marcha | `api` |
| Lee | `http://api:8000/salud` · la respuesta de `POST /predecir` · la primera pieza de `limpio.csv` |
| Escribe | Lo escribe el servicio, no el comando: una línea en `predicciones.jsonl` |
| `OK` si | La respuesta trae la misma versión que `/salud` y la pieza sin señales se rechaza con un error |
| `FALLO` si | El servicio no está, la versión no coincide o acepta la pieza incompleta |

Se usa en [M07-01](M07-mlops-observabilidad/M07-01-servicio-inferencia.md).

### m07-02

**Qué hace:** calcula qué parte de las piezas de examen mandaría el modelo a revisión con los datos tal cual (la base) y con esas mismas piezas 8 °C más calientes (la deriva).

| | |
|--|--|
| Necesita en marcha | Nada (solo `lab`) |
| Lee | `modelo_defecto.joblib` · `limpio.csv` |
| Escribe | `seguimiento.json` (tasa base y tasa desplazada) |
| `OK` si | La tasa desplazada supera a la base en al menos 0,10 |
| `FALLO` si | No se aprecia la deriva |

Se usa en [M07-02](M07-mlops-observabilidad/M07-02-monitorizacion.md).

---

## M08 — Seguridad y gobierno

### m08-01

**Qué hace:** imprime el inventario de servicios de la arquitectura con su puerto y su función, y las tres medidas de seguridad declaradas. Después lee el registro del paro de seguridad.

| | |
|--|--|
| Necesita en marcha | `modbus` |
| Lee | Registro Modbus 10 |
| Escribe | Nada |
| `OK` si | El paro de seguridad está en 0 |
| `FALLO` si | `modbus` no responde o el paro no está en 0 |

Se usa en [M08-01](M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md). El inventario y las medidas son textos fijos del código: **no comprueba** que se cumplan. Comprobarlo es el ejercicio del lab.

### m08-02

**Qué hace:** simula una auditoría. Dictamina `AUD0007`, cambia el fichero `VERSION` a `defecto-0.2` sin reiniciar el servicio, dictamina `AUD0008` y comprueba en el registro que las dos piezas conservan la versión que de verdad contestó.

| | |
|--|--|
| Necesita en marcha | `api` |
| Lee | Las respuestas de `POST /predecir` · `predicciones.jsonl` |
| Escribe | Cambia `VERSION` a `defecto-0.2` y, al terminar bien, la devuelve a su valor. El servicio añade dos líneas a `predicciones.jsonl` |
| `OK` si | Las dos piezas aparecen en el registro con la versión original |
| `FALLO` si | Falta alguna pieza o cambió la versión. Si falla, `VERSION` puede quedarse en `defecto-0.2` |

Se usa en [M08-02](M08-ciberseguridad-gobierno/M08-02-gobierno-trazabilidad.md).
