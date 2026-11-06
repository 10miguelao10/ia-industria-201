# Glosario 1 — Datos y arquitectura

[← Índice del glosario](README.md) · [Siguiente hoja →](02-observabilidad.md)

Cómo sale el dato de la máquina, por dónde viaja y dónde se guarda. Lo usas sobre todo en el M01 y el M02.

Cada ficha dice **qué es**, **cómo es en la línea del curso**, **dónde se rompe** y **en qué páginas lo usas**.

---

<a id="pieza"></a>
### Pieza (carcasa)

**Qué es:** cada carcasa que pasa por la estación EST-01 y sale hacia la fase siguiente. En el curso, una pieza es a la vez un objeto físico y el **registro** que la representa en los datos.

**En la línea:** cada pieza tiene un identificador que crece (`P0906`, `H0562`…) y un tiempo de ciclo de en torno a 1 s.

**Dónde se rompe:** si el identificador se reinicia al reiniciar la estación, aparecen piezas «repetidas» en el histórico que no lo son.

**Lo usas en:** <!--usos:pieza-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md)<!--/usos-->

<a id="evento"></a>
### Evento y muestra

**Qué es:** dos formas de producir datos.

| | Evento | Muestra |
|--|--------|---------|
| Cuándo se produce | Cuando **pasa algo** (sale una pieza, empieza una parada) | **Cada cierto tiempo**, pase o no algo |
| Ejemplo en la línea | Un mensaje MQTT por cada carcasa | Prometheus lee la temperatura cada 5 s |
| Si se pierde uno | Falta esa pieza para siempre | El siguiente valor llega en 5 s |

**Dónde se rompe:** perder eventos significa perder producción en los datos; perder muestras solo reduce el detalle.

**Lo usas en:** <!--usos:evento-->[M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md)<!--/usos-->

Relacionado: [métrica](02-observabilidad.md#metrica) · [histórico](#historico)

<a id="mqtt"></a>
### MQTT

**Qué es:** *Message Queuing Telemetry Transport*, un protocolo ligero de mensajería de **publicación y suscripción**. Quien produce un dato lo **publica** en un **tema**; quien lo necesita se **suscribe** a ese tema. No se conocen entre sí: los une el [broker](#broker).

**En la línea:** la estación publica cada pieza en `linea/est01/ciclo`; el archivador y el panel se suscriben. Va sobre TCP: la conexión se abre una vez y se mantiene, así que el coste de establecerla no se paga en cada mensaje.

**Dónde se rompe:** por defecto, un mensaje que se publica mientras nadie escucha **se pierde**. MQTT no es una cola como RabbitMQ ni un registro como Kafka: el dato pasa y no se queda.

**Lo usas en:** <!--usos:mqtt-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md)<!--/usos-->

Relacionado: [tema](#tema) · [QoS](#qos) · [mensaje retenido](#retenido)

<a id="broker"></a>
### Broker

**Qué es:** el servidor que recibe los mensajes MQTT y se los reparte a los suscriptores de cada tema.

**En la línea:** Mosquitto, en el puerto 1883, **sin usuario ni contraseña** y **sin guardar mensajes** en disco.

**Dónde se rompe:** si se reinicia, los clientes que no se vuelvan a suscribir se quedan sordos sin avisar (es el fallo del archivador del M01-03). Sin autenticación, cualquiera de la red puede publicar (M08-01).

**Lo usas en:** <!--usos:broker-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="tema"></a>
### Tema (topic)

**Qué es:** la «dirección» de un mensaje MQTT, con niveles separados por `/`. El comodín `#` recoge todos los niveles por debajo.

**En la línea:** `linea/est01/ciclo` (piezas), `linea/est01/dictamen` (decisión del modelo), `linea/est01/evento` (provocar un fallo simulado), `linea/est01/consigna` (pedir nivel de refrigeración). `linea/est01/#` los recoge todos.

**Lo usas en:** <!--usos:tema-->[M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md)<!--/usos-->

<a id="qos"></a>
### QoS (calidad de servicio)

**Qué es:** el nivel de garantía de entrega de MQTT. **0**: se envía una vez, sin confirmación. **1**: se repite hasta que llega, al menos una vez. **2**: exactamente una vez.

**En la línea:** se usa QoS 0, sin sesión persistente: lo que se publica durante un corte del archivador se pierde.

**Cómo se mejora:** QoS 1 con sesión persistente, o *store-and-forward* en el [edge](#edge): guardar en local y reenviar cuando vuelve la conexión.

**Lo usas en:** <!--usos:qos-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md)<!--/usos-->

<a id="retenido"></a>
### Mensaje retenido y Last Will

**Qué es:** dos ayudas de MQTT para conocer el **estado** de una máquina.

- **Retenido:** el broker guarda el último mensaje de un tema y se lo da al momento a quien se suscribe tarde.
- **Last Will** (último deseo): un mensaje que el cliente deja dicho al conectarse y que el broker publica por él si se desconecta sin despedirse.

**En la línea:** la mejora del M02-01 publica `{"estado": …}` retenido en `linea/est01/estado`.

**Dónde se rompe:** el retenido es para el estado, no para el histórico: solo guarda **uno**.

**Lo usas en:** <!--usos:retenido-->[M02](../M02-captura-integracion-datos/README.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md)<!--/usos-->

<a id="edge"></a>
### Edge (equipo de borde)

**Qué es:** un ordenador industrial **junto a la máquina**, dentro de la red de planta, que recoge, filtra y procesa datos sin depender de la nube.

**En la línea:** los contenedores del curso hacen el papel del edge: broker, archivador, pasarela, modelo y API corren en el mismo equipo.

**Por qué importa:** la latencia es baja, sigue funcionando sin Internet y el dato no sale de la planta.

**Lo usas en:** <!--usos:edge-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M04-04](../M04-vision-control-calidad/M04-04-red-neuronal.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-01](../M06-edge-integracion-ot/M06-01-inferencia-edge.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md)<!--/usos-->

<a id="ot"></a>
### OT e IT

**Qué es:** **OT** (*Operational Technology*) son los sistemas que controlan el proceso físico: autómatas, sensores, SCADA. **IT** son los sistemas de información: servidores, bases de datos, correo.

**Por qué importa:** en OT manda la **disponibilidad y la seguridad física**; un modelo de IA que escribe en OT puede parar o dañar una máquina. Por eso, en el curso, el modelo propone y la máquina pone los límites.

**Lo usas en:** <!--usos:ot-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="scada"></a>
### SCADA

**Qué es:** *Supervisory Control And Data Acquisition*. El sistema de planta que **recoge datos** de los autómatas, los **muestra** en pantallas de supervisión, **guarda histórico**, lanza **alarmas** y permite al operador **mandar órdenes**.

**En la línea:** no hay un SCADA comercial; sus funciones están repartidas: el panel (pantalla), el archivador (histórico), Prometheus (alarmas) y las consignas por MQTT (órdenes).

**Lo usas en:** <!--usos:scada-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="modbus"></a>
### Modbus

**Qué es:** un protocolo industrial de los años 70, muy extendido, en el que un cliente **pregunta** y el equipo **contesta**. Los datos están en **registros** numerados de 16 bits, sin nombre ni unidad: hay que saber qué hay en cada uno.

**En la línea:** puerto 1502. Registro 0 = temperatura × 10, 1 = vibración × 1000, 2 = corriente × 100, 3 = número de secuencia, 10 = paro de seguridad.

**Dónde se rompe:** si te equivocas de escala, lees 621 °C en vez de 62,1 °C. Sin autenticación, quien llega a la red puede **escribir** en un registro (M08-01).

**Lo usas en:** <!--usos:modbus-->[M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M06-02](../M06-edge-integracion-ot/M06-02-integracion-ot.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

Relacionado: [mapa de registros](#mapa-registros) · [pasarela](#pasarela)

<a id="mapa-registros"></a>
### Mapa de registros

**Qué es:** la tabla, normalmente del manual del fabricante, que dice qué variable hay en cada registro Modbus, con qué escala y si se puede escribir.

**Por qué importa:** sin el mapa, los números de un equipo Modbus no significan nada.

**Lo usas en:** <!--usos:mapa-registros-->[M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md)<!--/usos-->

<a id="opcua"></a>
### OPC UA

**Qué es:** el estándar moderno de comunicación industrial. A diferencia de Modbus, cada variable tiene **nombre, tipo y unidad**, y el protocolo admite cifrado y usuarios.

**En la línea:** puerto 4840. En el curso las variables se pueden escribir sin autenticarse, a propósito, para el M08-01.

**Lo usas en:** <!--usos:opcua-->[M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="pasarela"></a>
### Pasarela (gateway)

**Qué es:** un programa que **traduce** entre protocolos: lee de un equipo en su idioma (Modbus) y lo publica en otro (MQTT).

**En la línea:** el M02-02 monta una pasarela Modbus → MQTT que lee los registros, aplica la escala y publica en un tema.

**Lo usas en:** <!--usos:pasarela-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md)<!--/usos-->

<a id="historico"></a>
### Histórico (historian)

**Qué es:** la base de datos donde se guarda **cada dato con su hora**, para consultarlo después: qué pasó, cuándo y con qué valores.

**En la línea:** el archivador guarda cada pieza en `infra/data/historial.sqlite`, tabla `lecturas`. Calidad guarda sus inspecciones en `calidad.sqlite`.

**Dónde se rompe:** si el archivador deja de recibir, el histórico se queda con **huecos que no se ven** a simple vista: la consulta funciona, pero faltan piezas.

**Lo usas en:** <!--usos:historico-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M02-03](../M02-captura-integracion-datos/M02-03-preparacion-datos.md) · [M02-04](../M02-captura-integracion-datos/M02-04-dataset-linea.md) · [M03](../M03-ml-prediccion-anomalias/README.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md) · [M07-03](../M07-mlops-observabilidad/M07-03-incidencias-agente.md) · [M08](../M08-ciberseguridad-gobierno/README.md) · [M08-01](../M08-ciberseguridad-gobierno/M08-01-evaluacion-riesgos.md)<!--/usos-->

<a id="tiempo-ciclo"></a>
### Tiempo de ciclo y microparada

**Qué es:** el **tiempo de ciclo** es lo que tarda la estación en hacer una pieza. Una **microparada** es una parada corta (segundos) que nadie registra como avería, pero que resta producción.

**En la línea:** ciclo de 1 s ± 10 %; microparadas de 3 a 8 s cada 2,5 min de media.

**Por qué importa:** es la base del **rendimiento** del [OEE](02-observabilidad.md#kpi): cuánto se fabrica frente a lo que se podría.

**Lo usas en:** <!--usos:tiempo-ciclo-->[M01](../M01-ia-industrial-arquitectura/README.md) · [M01-01](../M01-ia-industrial-arquitectura/M01-01-arquitectura-datos.md) · [M01-02](../M01-ia-industrial-arquitectura/M01-02-visualizacion-supervision.md) · [M01-03](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [M02](../M02-captura-integracion-datos/README.md) · [M02-01](../M02-captura-integracion-datos/M02-01-telemetria.md) · [M06](../M06-edge-integracion-ot/README.md) · [M06-03](../M06-edge-integracion-ot/M06-03-prediccion-actuacion.md)<!--/usos-->

<a id="limpieza"></a>
### Limpieza de datos

**Qué es:** detectar y tratar los problemas que trae un histórico real antes de usarlo: **huecos** (falta el valor), **valores imposibles** (un sensor que da 9999), **duplicados**, **unidades mezcladas**.

**En la línea:** el `crudo.csv` del M02-03 trae 26 piezas sin temperatura y 6 con 9999; la limpieza las marca o las quita y deja `limpio.csv`.

**Dónde se rompe:** rellenar huecos con la media parece inocente, pero inventa piezas «normales» justo donde el sensor falló, y puede esconder defectos.

**Lo usas en:** <!--usos:limpieza-->[M02](../M02-captura-integracion-datos/README.md) · [M02-02](../M02-captura-integracion-datos/M02-02-protocolos.md) · [M02-03](../M02-captura-integracion-datos/M02-03-preparacion-datos.md)<!--/usos-->

Relacionado: [dataset](#dataset) · [fuga de información](03-aprendizaje-automatico.md#fuga)

<a id="dataset"></a>
### Dataset

**Qué es:** la tabla con la que aprende un modelo: **una fila por ejemplo** (pieza), **columnas de entrada** (señales) y, si se va a predecir algo, una **columna de etiqueta** (`defecto`).

**En la línea:** `limpio.csv` (M02-03, datos sintéticos) y `dataset_linea.csv` (M02-04, que une el histórico de la estación con las inspecciones de calidad).

**Dónde se rompe:** si unes mal las tablas (pieza equivocada, hora desfasada), el modelo aprende relaciones que no existen.

**Lo usas en:** <!--usos:dataset-->[M02](../M02-captura-integracion-datos/README.md) · [M02-03](../M02-captura-integracion-datos/M02-03-preparacion-datos.md) · [M02-04](../M02-captura-integracion-datos/M02-04-dataset-linea.md) · [M03](../M03-ml-prediccion-anomalias/README.md) · [M03-01](../M03-ml-prediccion-anomalias/M03-01-prediccion-defectos.md) · [M03-04](../M03-ml-prediccion-anomalias/M03-04-entrenar-datos-linea.md)<!--/usos-->

Relacionado: [etiqueta](03-aprendizaje-automatico.md#etiqueta) · [señal](03-aprendizaje-automatico.md#senal)
