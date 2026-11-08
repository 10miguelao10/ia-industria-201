# Glosario 6 — Modelos abiertos en planta

[← Hoja anterior](05-operacion-gobierno.md) · [Índice del glosario](README.md)

Qué modelos de IA se pueden instalar en los equipos de la propia planta, sin enviar datos fuera: un **catálogo por tarea** (texto, búsqueda, documentos, voz, visión, series temporales y filtros de seguridad) con para qué sirve cada modelo, cuándo usarlo y cuándo no, qué licencia tiene y qué equipo necesita. No hace falta probarlos todos; hace falta **saber situarlos** para elegir bien y para entender lo que pide un integrador. Lo practicas en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md).

> Los modelos y las licencias cambian cada pocos meses. Esta hoja recoge la situación de **noviembre de 2026**; antes de elegir un modelo, se comprueba su ficha oficial (en Hugging Face, la «model card» y el fichero `LICENSE`).

---

<a id="mapa"></a>
## 1. El mapa: ¿qué tiene que hacer el modelo?

✔ = lo usas en el curso · ○ = existe y se usa en la industria; aquí solo se sitúa.

```text
¿Qué tiene que hacer el modelo?
│
├── Redactar, resumir, extraer datos de un texto, conversar ── modelo de lenguaje (LLM)
│   ├── Pequeño (0,5–4 B parámetros): CPU, equipo edge ......... ✔ Qwen2.5 0.5B (M05)   ✔ Qwen2.5 1.5B (M05-05)
│   │                                                            ○ Phi-4-mini · ○ Gemma pequeños
│   ├── Mediano denso (unos 7–32 B): GPU de servidor ........... ○ Qwen3.8 27B · ○ Mistral Small · ○ Gemma
│   └── Mezcla de expertos, MoE (muchos parámetros, pocos activos) ○ Qwen3.6 35B-A3B · ○ gpt-oss
│
├── Buscar en documentos
│   ├── Encontrar por significado (embeddings) ................. ✔ Qwen3-Embedding 0.6B (M05-05) · ○ BGE-M3 · ○ multilingual-e5
│   └── Reordenar lo encontrado (reranker) ..................... ○ Qwen3-Reranker · ○ bge-reranker
│
├── Leer documentos: OCR de etiquetas, albaranes, planos, PDF .. ○ PaddleOCR · ○ Docling · ○ modelos multimodales
│
├── Voz
│   ├── Pasar voz a texto (ASR) ................................ ○ Whisper · ○ Qwen3-ASR · ○ Voxtral · ○ Parakeet
│   └── Pasar texto a voz (TTS) ................................ ○ Kokoro
│
├── Ver ── visión
│   ├── ¿Esta foto es buena o mala? (clasificar) ............... ✔ regresión logística y red (M04)
│   ├── ¿Es distinta de las buenas? (anomalía visual) .......... ○ PatchCore y otros, con Anomalib
│   ├── ¿Qué hay y dónde? (detectar objetos) ................... ○ YOLO · ○ RT-DETR · ○ D-FINE · ○ YOLOX
│   ├── ¿Qué puntos exactos son la pieza o el defecto? (segmentar) ○ SAM 2
│   └── Entender una imagen y hablar de ella (multimodal) ...... ○ Qwen3.8 27B · ○ Gemma · ○ Florence-2
│
├── Prever una serie temporal (temperatura, consumo, demanda) .. ✔ recta de tendencia (M06-03) · ○ Chronos-Bolt · ○ TimesFM
│
├── Vigilar lo que entra y sale de un LLM (filtro de seguridad) ○ Llama Guard · ○ Granite Guardian · ○ Qwen3Guard
│
└── Predecir un defecto o una avería con datos de proceso ...... ✔ árbol, regresión logística (M03)
                                                                   NO es trabajo de un LLM
```

**Lo primero que aclara el mapa:** «modelo de IA» no es una sola cosa. Un modelo de lenguaje redacta; un modelo de embeddings no redacta nada, convierte textos en números para comparar su significado; un modelo de voz solo transcribe; y para predecir defectos con señales de máquina, lo adecuado sigue siendo el aprendizaje automático clásico del M03. Elegir empieza por la **tarea**, no por el nombre del modelo.

Los modelos con nombre de cada rama son **ejemplos conocidos a noviembre de 2026**, no una lista cerrada: en cada tarea salen modelos nuevos cada pocos meses. Lo que dura es la rama: saber qué tipo de modelo pide cada tarea.

<a id="comparacion-tipos"></a>
### Comparación por tipo de modelo

| Tipo | Para qué sirve | Cuándo usarlo | Cuándo **no** | Equipo típico |
|------|----------------|---------------|---------------|---------------|
| **LLM pequeño** (0,5–4 B) | Redactar frases cortas, resumir, extraer campos de un texto | En el edge, sin GPU, con el dato delante (RAG, herramientas) | Si tiene que saber cosas por sí mismo o razonar varios pasos | CPU normal, 1–4 GB de memoria |
| **LLM mediano** (7–32 B) | Informes, código, respuestas largas, razonar | Asistentes de mantenimiento, análisis de incidencias, documentación | En un puesto sin GPU; para cifras exactas sin dárselas | GPU de servidor, 16–40 GB |
| **LLM MoE** (p. ej. 35B-A3B) | Lo mismo que un mediano, más rápido | Muchos usuarios a la vez, chat, resúmenes en volumen | Si la memoria es justa: ocupa como un modelo grande | GPU con memoria para todos los parámetros |
| **Embeddings** | Convertir textos en números para buscar por significado | El «recuperar» de un RAG; buscar incidencias parecidas | Para contestar: no redacta | CPU, menos de 1 GB |
| **ASR** (voz a texto) | Transcribir partes de turno, llamadas, notas de voz | Cuando el dato nace hablado | Si hay ruido de planta y nadie revisa la transcripción | CPU o GPU pequeña |
| **Detección de objetos** (YOLO) | Decir qué hay en una foto **y dónde**, con un recuadro | Localizar piezas, defectos o personas en la imagen | Si basta con «buena o mala» (M04); si la licencia no encaja | GPU o equipo edge con acelerador |
| **Multimodal** (imagen + texto) | Describir una foto, leer una placa o un plano | Asistencia al técnico con una foto | Para inspeccionar en línea a 1 pieza por segundo | GPU de servidor |
| **Aprendizaje clásico** (M03) | Predecir con datos de proceso | Defectos, anomalías, mantenimiento | Para texto, voz o imágenes complejas | CPU, kilobytes |

<a id="catalogo"></a>
## 2. El catálogo por tarea

Para cada tarea, varios modelos abiertos conocidos, para qué sirve cada uno y cuándo **no** conviene. No hace falta probarlos: sirve para reconocerlos cuando aparezcan en un pedido, una oferta o una demo, y para hacer las preguntas correctas. La licencia es la de su ficha a noviembre de 2026; antes de usar uno, se comprueba de nuevo (sección 5).

<a id="cat-texto"></a>
### Redactar, resumir, extraer y conversar (modelos de lenguaje)

| Modelo (ejemplos) | Tamaño | Para qué es bueno | Cuándo **no** | Licencia |
|-------------------|--------|-------------------|---------------|----------|
| **Qwen2.5 0.5B / 1.5B** | Pequeño | Frases cortas con el dato delante, en un equipo sin GPU | Si tiene que saber o razonar por sí mismo | Apache 2.0 |
| **Phi-4-mini** | Pequeño | Razonar bien para su tamaño, en CPU | Textos largos en español muy técnicos | MIT |
| **Gemma** (pequeños y medianos) | Pequeño a mediano | Buen equilibrio calidad/tamaño; algunos ven imágenes | Versiones antiguas: licencia propia | Apache 2.0 desde Gemma 4 |
| **Mistral Small** | Mediano | Asistentes en español y francés, empresa europea | Puestos sin GPU | Apache 2.0 |
| **Qwen3.8 27B** | Mediano denso | Informes, código, documentación, ve imágenes | Equipos sin GPU de servidor | Apache 2.0 |
| **Qwen3.6 35B-A3B**, **gpt-oss** | MoE | Mucho volumen: resumir, extraer, chat con muchos usuarios | Si la memoria es justa (ocupa como uno grande) | Apache 2.0 |
| **DeepSeek** | MoE muy grande | Razonamiento complejo | Casi siempre en planta: pide varios GPU | MIT |
| **Llama** | De pequeño a muy grande | Mucho ecosistema y ejemplos | Si la licencia comunitaria no encaja (multimodales y UE) | Comunitaria propia |

<a id="cat-buscar"></a>
### Buscar en documentos: embeddings y rerankers

Un **modelo de embeddings** convierte cada texto en una lista de números para encontrar los que significan algo parecido (M05-05). Un **reranker** recibe la pregunta y los diez párrafos que ha encontrado el de embeddings, y los **reordena** leyéndolos de verdad: es más lento, pero afina mucho. Un buscador serio usa los dos.

| Modelo (ejemplos) | Tipo | Para qué es bueno | Cuándo **no** | Licencia |
|-------------------|------|-------------------|---------------|----------|
| **Qwen3-Embedding** (0.6B, 4B, 8B) | Embeddings | Multilingüe, buen español; el pequeño va en CPU | — | Apache 2.0 |
| **BGE-M3** | Embeddings | Multilingüe, textos largos, muy usado | — | MIT |
| **multilingual-e5** | Embeddings | Ligero y multilingüe | Documentos muy largos | MIT |
| **jina-embeddings-v3** | Embeddings | Buena calidad | **Uso comercial sin contrato: su licencia es no comercial** | CC BY-NC 4.0 |
| **Qwen3-Reranker**, **bge-reranker** | Reranker | Afinar los primeros resultados de la búsqueda | Como buscador único: es lento para miles de textos | Apache 2.0 (comprobar en cada ficha) |

<a id="cat-documentos"></a>
### Leer documentos: OCR y estructura

| Herramienta o modelo | Para qué es buena | Cuándo **no** | Licencia |
|----------------------|-------------------|---------------|----------|
| **PaddleOCR** | Leer texto de fotos: etiquetas, placas, albaranes; muchos idiomas | Entender lo que dice: solo lo lee | Apache 2.0 |
| **Docling** (IBM) | Convertir PDF y documentos con tablas en texto ordenado, para un RAG | Fotos de etiquetas en la línea | MIT |
| **Modelos multimodales** (Qwen3.8, Gemma, Florence-2) | Leer y además interpretar: «¿qué referencia pone en la placa?» | A una pieza por segundo: son lentos | Apache 2.0 / MIT |

<a id="cat-voz"></a>
### Voz: pasar a texto y generar

| Modelo (ejemplos) | Para qué es bueno | Cuándo **no** | Licencia |
|-------------------|-------------------|---------------|----------|
| **Whisper** (large-v3, turbo) | Transcribir en muchos idiomas; el más extendido | Con mucho ruido de planta sin micrófono adecuado | MIT |
| **Qwen3-ASR** | Transcripción multilingüe, ligero | — | Apache 2.0 |
| **Voxtral Mini** | Transcribir y entender audio; europeo (Mistral) | — | Apache 2.0 (comprobar en su ficha) |
| **Parakeet** (NVIDIA) | Muy rápido, sobre todo en GPU NVIDIA | Si el idioma no está entre los suyos | CC BY 4.0 (comprobar la versión) |
| **Kokoro** | Texto a voz ligero: avisos hablados en un puesto | Voces personalizadas | Apache 2.0 |

Usar **dos transcriptores distintos** y comparar es una forma barata de saber cuándo una transcripción no es fiable (sección 3).

<a id="cat-vision"></a>
### Visión: clasificar, detectar, segmentar y buscar anomalías

| Modelo o herramienta | Pregunta que responde | Para qué en planta | Cuándo **no** | Licencia |
|----------------------|-----------------------|--------------------|---------------|----------|
| **Clasificador** (M04) | ¿Buena o mala? | Una foto por pieza, un defecto conocido | Si hay que decir dónde | La del código que uses |
| **PatchCore** y otros, con **Anomalib** | ¿Se parece a las buenas? | Inspección cuando **casi no hay fotos de defectos**: aprende solo de piezas buenas | Si los defectos son sutiles y cambian de forma constantemente | Apache 2.0 el código; **los modelos ya entrenados con MVTec AD heredan su licencia no comercial** |
| **YOLO** (Ultralytics) | ¿Qué hay y dónde? | Localizar piezas, defectos o personas, en tiempo real | **Sin licencia de empresa**: es AGPL-3.0 | AGPL-3.0 o comercial |
| **RT-DETR**, **D-FINE**, **YOLOX** | ¿Qué hay y dónde? | Lo mismo que YOLO, con licencia permisiva | Si no hay quien los entrene: piden más trabajo que YOLO | Apache 2.0 (en su repositorio original) |
| **SAM 2** | ¿Qué puntos exactos son esto? | Medir el área de un defecto, recortar la pieza, preparar fotos para entrenar | Para decidir solo: no sabe qué es un defecto | Apache 2.0 |

En inspección industrial, **la anomalía visual suele ser el primer modelo útil**: en una línea hay miles de fotos de piezas buenas y muy pocas de defectuosas. Es la misma idea del M03-02 (aprender lo normal), aplicada a imágenes.

<a id="cat-series"></a>
### Series temporales: prever

| Modelo | Para qué es bueno | Cuándo **no** | Licencia |
|--------|-------------------|---------------|----------|
| **Recta de tendencia** (M06-03, `predict_linear`) | Una señal que sube de forma sostenida | Señales con ciclos (turnos, días) | — |
| **Chronos-Bolt** (Amazon) | Prever una serie sin entrenar nada («cero ejemplos»), en CPU; de 9 M a 205 M parámetros | Si la avería no se ve en la propia serie | Apache 2.0 |
| **TimesFM 2.5** (Google) | Lo mismo, con contextos largos | Versiones posteriores: comprueba si siguen siendo de uso comercial | Apache 2.0 (la 2.5) |

Estos modelos **prevén** cómo seguirá una curva; no dicen si eso es una avería. Combinados con la banda normal del M06-03 (¿se va a salir de lo normal?), mejoran la previsión cuando la señal tiene ritmos de turno o de día.

<a id="cat-seguridad"></a>
### Filtros de seguridad para modelos de lenguaje

| Modelo | Para qué es bueno | Cuándo **no** | Licencia |
|--------|-------------------|---------------|----------|
| **Llama Guard** | Revisar lo que entra y sale de un asistente: peticiones peligrosas, respuestas que no debe dar | Si la licencia comunitaria no encaja | Comunitaria (Llama) |
| **Granite Guardian** (IBM) | Lo mismo, y detectar respuestas no apoyadas en el documento | — | Apache 2.0 |
| **Qwen3Guard** | Lo mismo, multilingüe | — | Apache 2.0 (comprobar en su ficha) |

Un filtro **no sustituye** a no dar herramientas de escritura (M05-04): es una capa más.

---

<a id="caso-real"></a>
## 3. Un ejemplo: leer un pedido real

Un ejemplo de cómo se usa el catálogo. Un equipo de integración pidió hace poco preparar estos modelos en un servidor propio, todos con licencia Apache 2.0. Así se lee cada línea del pedido:

| Modelo pedido | Tipo | Para qué lo quieren | Qué dice su nombre |
|---------------|------|---------------------|--------------------|
| Qwen3.8 27B FP8 | LLM mediano, denso, multimodal | Informes y código | 27 000 millones de parámetros, guardados en 8 bits (FP8) |
| Qwen3.6 35B-A3B FP8 | LLM MoE | Resúmenes, extracción de datos y chat | 35 000 millones en total, de los que trabajan **3 000 millones** por token (A3B): calcula como uno pequeño, ocupa como uno grande |
| Qwen3-Embedding 0.6B | Embeddings | Búsqueda semántica | Pequeño: cabe en cualquier equipo |
| Qwen3-ASR 1.7B | Voz a texto | Transcripción | |
| Voxtral Mini 3B | Voz a texto | Una **segunda** transcripción, independiente | De otro fabricante (Mistral) |

**Cómo se lee:** cada tarea tiene su modelo, y ninguno hace todo. Lo más interesante es lo que **no** se ve a primera vista:

- **Dos modelos para lo mismo.** Para la voz piden dos transcriptores de fabricantes distintos: si los dos coinciden, la transcripción es fiable; si no, se revisa. Es la misma idea que la comprobación del diagnóstico del M07-03: no fiarse de una sola salida.
- **Un modelo grande para escribir y otro rápido para el volumen.** El denso de 27 B para lo que pide calidad (un informe); el MoE para lo que llega en cantidad (resumir y extraer de muchos textos), porque cada respuesta le cuesta como uno de 3 B.
- **FP8 dice qué GPU hace falta.** FP8 es un formato de 8 bits que aprovechan las GPU de servidor recientes. Sin una de esas GPU, estos mismos modelos se instalarían en otro formato (GGUF, como el del curso).
- **Todo Apache 2.0.** No es casualidad: es la licencia más sencilla para uso comercial (sección 5).

---

<a id="familias"></a>
## 4. Las familias más conocidas

| Familia | De quién | Fuerte en | Licencia habitual (comprobar en cada modelo) |
|---------|----------|-----------|----------------------------------------------|
| **Qwen** | Alibaba | De todo: texto, código, embeddings, voz, multimodal; buen español | Apache 2.0 en la mayoría; algún modelo con licencia propia |
| **Mistral / Voxtral** | Mistral AI (Francia) | Texto y voz; empresa europea | Apache 2.0 en muchos; los más grandes, licencia propia |
| **Gemma** | Google | Modelos pequeños y medianos, multimodal | Apache 2.0 desde Gemma 4; las versiones anteriores, licencia propia |
| **Phi** | Microsoft | Modelos pequeños que razonan bien para su tamaño | MIT |
| **gpt-oss** | OpenAI | Modelos MoE para servidor | Apache 2.0 |
| **DeepSeek** | DeepSeek | Modelos MoE muy grandes, razonamiento | MIT |
| **Llama** | Meta | Muy extendido, mucho ecosistema | Licencia comunitaria propia, con condiciones (sección 5) |
| **Whisper** | OpenAI | Voz a texto, muchos idiomas | MIT |
| **YOLO** | Ultralytics | Detección de objetos en imágenes | **AGPL-3.0** o licencia de empresa (sección 5) |

<a id="licencias"></a>
## 5. Licencias: lo que hay que mirar antes de instalar

**Pesos abiertos no es lo mismo que código abierto.** Casi todos estos modelos publican los **pesos** (el fichero que se descarga), pero no los datos con los que se entrenaron. Se pueden usar y adaptar; no se puede reproducir cómo se hicieron. Lo que manda es la licencia de cada modelo.

| Licencia | Uso comercial en planta | Qué obliga | Ejemplos |
|----------|-------------------------|------------|----------|
| **Apache 2.0** | Sí | Mantener el aviso de licencia; protege frente a patentes | La mayoría de Qwen, muchos Mistral, gpt-oss, Gemma 4 |
| **MIT** | Sí | Mantener el aviso de licencia | Phi, DeepSeek, Whisper |
| **Comunitaria propia** (Llama y otras) | Con condiciones | Política de usos aceptables, límites por tamaño de empresa; según varias fuentes, Llama no concede sus modelos multimodales a empresas de la UE | Llama, versiones antiguas de Gemma, los Mistral más grandes |
| **AGPL-3.0** | Solo publicando tu código, o con licencia comercial | Si el software se usa o se ofrece, hay que publicar su código fuente con la misma licencia. Ultralytics indica que se aplica también al uso interno y a los modelos que entrenes tú | YOLO de Ultralytics |

**La trampa más habitual en industria es YOLO.** Es el detector de objetos más conocido y se instala en minutos, pero el de Ultralytics es AGPL-3.0: para un sistema de inspección de una planta, en la práctica, hace falta su licencia de empresa o elegir otro detector con licencia permisiva. Es una decisión de compras y legal, no del técnico que lo prueba.

**Otras trampas que aparecen en el catálogo:**

| Dónde | La trampa |
|-------|-----------|
| **jina-embeddings-v3** | Su licencia es no comercial (CC BY-NC): para usarlo en la empresa hace falta un contrato con Jina |
| **Modelos de anomalía visual ya entrenados** | El código (Anomalib, PatchCore) es Apache 2.0, pero si los pesos se entrenaron con el conjunto de imágenes MVTec AD, heredan su licencia no comercial: hay que entrenarlos con fotos propias |
| **Series temporales** | TimesFM 2.5 es Apache 2.0; según algunas fuentes, versiones posteriores tienen pesos solo para uso no comercial |
| **Detectores dentro de Ultralytics** | RT-DETR es Apache 2.0 en su repositorio original, pero el que viene dentro del paquete de Ultralytics queda bajo su AGPL |
| **Pesos frente a datos** | Un modelo puede tener pesos Apache 2.0 y haberse entrenado con datos de otra licencia; la ficha lo suele decir |

**La regla:** la licencia se comprueba **en la ficha oficial de cada modelo concreto**, no por la familia: dentro de una misma familia hay modelos con licencias distintas, y cambian de una versión a otra.

<a id="memoria"></a>
## 6. Formatos y memoria: cuánto ocupa un modelo

La memoria que necesita un modelo es, sobre todo, **parámetros × bytes por parámetro**, más un margen para la conversación (el contexto).

| Formato | Bytes por parámetro | Un modelo de 27 B ocupa | Dónde se usa |
|---------|---------------------|--------------------------|--------------|
| BF16 (el original) | 2 | ~54 GB | Entrenar, ajustar, servidores grandes |
| FP8 | 1 | ~27 GB | GPU de servidor recientes (el pedido de la sección 3) |
| GGUF Q4 (4 bits) | ~0,6 | ~16–17 GB | CPU, portátiles, equipos edge (el curso: llama.cpp) |

Con el modelo del curso: 0,5 B en Q4 son **470 MB**, y por eso cabe en el contenedor de 2 GB. En el reto del M05-01 estimaste que uno de 7 B no cabría; en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md) lo mides con uno de 1,5 B.

Un **MoE** engaña: el 35B-A3B **ocupa** como uno de 35 B (hay que cargar todos los expertos), pero **calcula** como uno de 3 B. Es rápido, no pequeño.

<a id="servir"></a>
## 7. Cómo se sirven

| Servidor | Para qué | Cuándo elegirlo | En el curso |
|----------|----------|-----------------|-------------|
| **llama.cpp** | Ejecutar modelos GGUF en CPU (o GPU), con poco | Equipos edge, un puesto, sin GPU | ✔ el contenedor `llm` |
| **Ollama** | Lo mismo, con una instalación muy sencilla | Probar modelos en un portátil, un usuario | ○ |
| **vLLM** | Servir modelos en GPU a muchos usuarios a la vez | Un servidor de planta para todos los asistentes | ○ es lo que usaría el pedido de la sección 3 |

Los tres hablan el mismo «idioma» por HTTP (`/v1/chat/completions`), así que una aplicación como la del M05-02 funciona con cualquiera: cambia la dirección del servicio, no el código.

<a id="cuando-no"></a>
## 8. Cuándo no hace falta un modelo generativo

| Si lo que necesitas es… | Lo adecuado | En el curso |
|-------------------------|-------------|-------------|
| Predecir un defecto o una avería con señales de máquina | Aprendizaje automático clásico | M03, M06-03 |
| Avisar cuando algo pasa de un límite | Una regla o una alerta | M01-03 |
| Una cifra exacta (temperatura, par de apriete) | Leer el dato o el documento, no preguntarlo | M05-03, M05-04 |
| Actuar sobre la máquina | Una persona o el automatismo, con límites | M06-03, M07-03 |

Un modelo generativo redacta muy bien y se equivoca con seguridad. En planta se usa para **redactar, resumir y buscar** con los datos delante, y se comprueba lo que dice.

<a id="elegir"></a>
## 9. Cómo elegir, en cinco preguntas

1. **¿Qué tarea es?** Redactar, buscar, transcribir, ver o predecir (secciones 1 y 2). Si es predecir con datos de proceso, no es un LLM.
2. **¿Qué licencia tiene ese modelo concreto?** Apache 2.0 o MIT simplifican; cualquier otra, a legal (sección 5).
3. **¿En qué equipo va a correr?** Memoria disponible y si hay GPU (sección 6): eso fija el tamaño y el formato.
4. **¿Funciona en español y con el vocabulario de la planta?** Se prueba con preguntas reales de la planta, no con las del fabricante.
5. **¿Cuánto tarda y cuántos lo usarán a la vez?** Un usuario en un puesto, llama.cpp u Ollama; muchos usuarios, vLLM en un servidor (sección 7).

Las preguntas 3 a 5 las contestas midiendo en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md).

---

**Fuentes** (consultadas en noviembre de 2026): fichas de [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B), [Qwen3.6-35B-A3B-FP8](https://modal.com/library/qwen/qwen3-6-35b-a3b-fp8), [colección Qwen3-Embedding](https://huggingface.co/collections/Qwen/qwen3-embedding), [Qwen3-ASR](https://qwen.ai/blog?id=qwen3asr), [artículo de Voxtral](https://arxiv.org/pdf/2507.13264), [licencia de Ultralytics](https://ultralytics.com/license) y [documentación de YOLO](https://docs.ultralytics.com/); comparativas de licencias ([1](https://codersera.com/blog/open-source-llms-landscape-2026/), [2](https://sysart.consulting/knowledge-hub/open-weight-model-licenses/)) y de servidores ([1](https://insiderllm.com/guides/llamacpp-vs-ollama-vs-vllm/), [2](https://www.morphllm.com/comparisons/vllm-vs-ollama)); [Anomalib](https://pypi.org/project/anomalib/2.3.0/) y la [ficha de un modelo PatchCore entrenado con MVTec AD](https://huggingface.co/yusufdxb/inspectnet-cx); [Chronos-Bolt](https://huggingface.co/autogluon/chronos-bolt-base) y [TimesFM 2.5](https://huggingface.co/docs/transformers/model_doc/timesfm2_5); comparativas de embeddings ([1](https://wz-it.com/en/blog/best-embedding-models-german/), [2](https://learn.engineering.vips.edu/compare/bge-m3-vs-jina-embeddings-v3)); [PaddleOCR](https://pypi.org/project/vaaale-paddleocr) y [voz local](https://pasqualepillitteri.it/de/news/28187/lokale-sprach-ki-sprachausgabe-transkription). Las comparativas de terceros no siempre coinciden entre sí: lo que vale es la ficha oficial de cada modelo.
