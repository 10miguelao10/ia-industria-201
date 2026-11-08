# Glosario 6 — Modelos abiertos en planta

[← Hoja anterior](05-operacion-gobierno.md) · [Índice del glosario](README.md)

Qué modelos de IA se pueden instalar en los equipos de la propia planta, sin enviar datos fuera: para qué sirve cada tipo, cuándo usarlo y cuándo no, qué licencia tiene y qué equipo necesita. No hace falta probarlos todos; hace falta **saber situarlos** para elegir bien y para entender lo que pide un integrador. Lo practicas en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md).

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
├── Buscar por significado en documentos ── modelo de embeddings ✔ Qwen3-Embedding 0.6B (M05-05)
│
├── Pasar voz a texto ── reconocimiento de voz (ASR) ........... ○ Qwen3-ASR 1.7B · ○ Voxtral Mini 3B · ○ Whisper
│
├── Ver ── visión
│   ├── ¿Esta foto es buena o mala? (clasificar) ............... ✔ regresión logística y red (M04)
│   ├── ¿Qué hay y dónde? (detectar objetos) ................... ○ YOLO
│   └── Entender una imagen y hablar de ella (multimodal) ...... ○ Qwen3.8 27B · ○ Gemma
│
└── Predecir un defecto o una avería con datos de proceso ...... ✔ árbol, regresión logística (M03)
                                                                   NO es trabajo de un LLM
```

**Lo primero que aclara el mapa:** «modelo de IA» no es una sola cosa. Un modelo de lenguaje redacta; un modelo de embeddings no redacta nada, convierte textos en números para comparar su significado; un modelo de voz solo transcribe; y para predecir defectos con señales de máquina, lo adecuado sigue siendo el aprendizaje automático clásico del M03. Elegir empieza por la **tarea**, no por el nombre del modelo.

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

---

<a id="caso-real"></a>
## 2. Un caso real: lo que pide un integrador

Un equipo de integración pidió hace poco preparar estos modelos en un servidor propio. Todos tienen licencia Apache 2.0. Así se lee cada línea del pedido con esta hoja:

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
- **Todo Apache 2.0.** No es casualidad: es la licencia más sencilla para uso comercial (sección 4).

---

<a id="familias"></a>
## 3. Las familias más conocidas

| Familia | De quién | Fuerte en | Licencia habitual (comprobar en cada modelo) |
|---------|----------|-----------|----------------------------------------------|
| **Qwen** | Alibaba | De todo: texto, código, embeddings, voz, multimodal; buen español | Apache 2.0 en la mayoría; algún modelo con licencia propia |
| **Mistral / Voxtral** | Mistral AI (Francia) | Texto y voz; empresa europea | Apache 2.0 en muchos; los más grandes, licencia propia |
| **Gemma** | Google | Modelos pequeños y medianos, multimodal | Apache 2.0 desde Gemma 4; las versiones anteriores, licencia propia |
| **Phi** | Microsoft | Modelos pequeños que razonan bien para su tamaño | MIT |
| **gpt-oss** | OpenAI | Modelos MoE para servidor | Apache 2.0 |
| **DeepSeek** | DeepSeek | Modelos MoE muy grandes, razonamiento | MIT |
| **Llama** | Meta | Muy extendido, mucho ecosistema | Licencia comunitaria propia, con condiciones (sección 4) |
| **Whisper** | OpenAI | Voz a texto, muchos idiomas | MIT |
| **YOLO** | Ultralytics | Detección de objetos en imágenes | **AGPL-3.0** o licencia de empresa (sección 4) |

<a id="licencias"></a>
## 4. Licencias: lo que hay que mirar antes de instalar

**Pesos abiertos no es lo mismo que código abierto.** Casi todos estos modelos publican los **pesos** (el fichero que se descarga), pero no los datos con los que se entrenaron. Se pueden usar y adaptar; no se puede reproducir cómo se hicieron. Lo que manda es la licencia de cada modelo.

| Licencia | Uso comercial en planta | Qué obliga | Ejemplos |
|----------|-------------------------|------------|----------|
| **Apache 2.0** | Sí | Mantener el aviso de licencia; protege frente a patentes | La mayoría de Qwen, muchos Mistral, gpt-oss, Gemma 4 |
| **MIT** | Sí | Mantener el aviso de licencia | Phi, DeepSeek, Whisper |
| **Comunitaria propia** (Llama y otras) | Con condiciones | Política de usos aceptables, límites por tamaño de empresa; según varias fuentes, Llama no concede sus modelos multimodales a empresas de la UE | Llama, versiones antiguas de Gemma, los Mistral más grandes |
| **AGPL-3.0** | Solo publicando tu código, o con licencia comercial | Si el software se usa o se ofrece, hay que publicar su código fuente con la misma licencia. Ultralytics indica que se aplica también al uso interno y a los modelos que entrenes tú | YOLO de Ultralytics |

**La trampa más habitual en industria es YOLO.** Es el detector de objetos más conocido y se instala en minutos, pero el de Ultralytics es AGPL-3.0: para un sistema de inspección de una planta, en la práctica, hace falta su licencia de empresa o elegir otro detector con licencia permisiva. Es una decisión de compras y legal, no del técnico que lo prueba.

**La regla:** la licencia se comprueba **en la ficha oficial de cada modelo concreto**, no por la familia: dentro de una misma familia hay modelos con licencias distintas, y cambian de una versión a otra.

<a id="memoria"></a>
## 5. Formatos y memoria: cuánto ocupa un modelo

La memoria que necesita un modelo es, sobre todo, **parámetros × bytes por parámetro**, más un margen para la conversación (el contexto).

| Formato | Bytes por parámetro | Un modelo de 27 B ocupa | Dónde se usa |
|---------|---------------------|--------------------------|--------------|
| BF16 (el original) | 2 | ~54 GB | Entrenar, ajustar, servidores grandes |
| FP8 | 1 | ~27 GB | GPU de servidor recientes (el pedido de la sección 2) |
| GGUF Q4 (4 bits) | ~0,6 | ~16–17 GB | CPU, portátiles, equipos edge (el curso: llama.cpp) |

Con el modelo del curso: 0,5 B en Q4 son **470 MB**, y por eso cabe en el contenedor de 2 GB. En el reto del M05-01 estimaste que uno de 7 B no cabría; en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md) lo mides con uno de 1,5 B.

Un **MoE** engaña: el 35B-A3B **ocupa** como uno de 35 B (hay que cargar todos los expertos), pero **calcula** como uno de 3 B. Es rápido, no pequeño.

<a id="servir"></a>
## 6. Cómo se sirven

| Servidor | Para qué | Cuándo elegirlo | En el curso |
|----------|----------|-----------------|-------------|
| **llama.cpp** | Ejecutar modelos GGUF en CPU (o GPU), con poco | Equipos edge, un puesto, sin GPU | ✔ el contenedor `llm` |
| **Ollama** | Lo mismo, con una instalación muy sencilla | Probar modelos en un portátil, un usuario | ○ |
| **vLLM** | Servir modelos en GPU a muchos usuarios a la vez | Un servidor de planta para todos los asistentes | ○ es lo que usaría el pedido de la sección 2 |

Los tres hablan el mismo «idioma» por HTTP (`/v1/chat/completions`), así que una aplicación como la del M05-02 funciona con cualquiera: cambia la dirección del servicio, no el código.

<a id="cuando-no"></a>
## 7. Cuándo no hace falta un modelo generativo

| Si lo que necesitas es… | Lo adecuado | En el curso |
|-------------------------|-------------|-------------|
| Predecir un defecto o una avería con señales de máquina | Aprendizaje automático clásico | M03, M06-03 |
| Avisar cuando algo pasa de un límite | Una regla o una alerta | M01-03 |
| Una cifra exacta (temperatura, par de apriete) | Leer el dato o el documento, no preguntarlo | M05-03, M05-04 |
| Actuar sobre la máquina | Una persona o el automatismo, con límites | M06-03, M07-03 |

Un modelo generativo redacta muy bien y se equivoca con seguridad. En planta se usa para **redactar, resumir y buscar** con los datos delante, y se comprueba lo que dice.

<a id="elegir"></a>
## 8. Cómo elegir, en cinco preguntas

1. **¿Qué tarea es?** Redactar, buscar, transcribir, ver o predecir (sección 1). Si es predecir con datos de proceso, no es un LLM.
2. **¿Qué licencia tiene ese modelo concreto?** Apache 2.0 o MIT simplifican; cualquier otra, a legal (sección 4).
3. **¿En qué equipo va a correr?** Memoria disponible y si hay GPU (sección 5): eso fija el tamaño y el formato.
4. **¿Funciona en español y con el vocabulario de la planta?** Se prueba con preguntas reales de la planta, no con las del fabricante.
5. **¿Cuánto tarda y cuántos lo usarán a la vez?** Un usuario en un puesto, llama.cpp u Ollama; muchos usuarios, vLLM en un servidor (sección 6).

Las preguntas 3 a 5 las contestas midiendo en el [M05-05](../M05-ia-generativa/M05-05-modelos-abiertos.md).

---

**Fuentes** (consultadas en noviembre de 2026): fichas de [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B), [Qwen3.6-35B-A3B-FP8](https://modal.com/library/qwen/qwen3-6-35b-a3b-fp8), [colección Qwen3-Embedding](https://huggingface.co/collections/Qwen/qwen3-embedding), [Qwen3-ASR](https://qwen.ai/blog?id=qwen3asr), [artículo de Voxtral](https://arxiv.org/pdf/2507.13264), [licencia de Ultralytics](https://ultralytics.com/license) y [documentación de YOLO](https://docs.ultralytics.com/); comparativas de licencias ([1](https://codersera.com/blog/open-source-llms-landscape-2026/), [2](https://sysart.consulting/knowledge-hub/open-weight-model-licenses/)) y de servidores ([1](https://insiderllm.com/guides/llamacpp-vs-ollama-vs-vllm/), [2](https://www.morphllm.com/comparisons/vllm-vs-ollama)). Las comparativas de terceros no siempre coinciden entre sí: lo que vale es la ficha oficial de cada modelo.
