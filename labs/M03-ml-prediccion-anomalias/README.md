# M03 — Machine learning para predicción y detección de incidencias

[← Página anterior](../M02-captura-integracion-datos/M02-04-dataset-linea.md) · [Siguiente página →](M03-01-prediccion-defectos.md)

> [!NOTE]
> **Cómo funciona este módulo.** Tiene cuatro bloques, uno por laboratorio. En cada bloque: primero la **teoría** y una **demostración** que se proyecta en clase, paso a paso; después **practicas tú** con el laboratorio, a tu ritmo.

## Qué aprenderás

- Qué es un **[modelo](../glosario/03-aprendizaje-automatico.md#modelo) de aprendizaje automático** y cómo aprende de piezas pasadas.
- Cómo se **evalúa** un modelo para que el resultado sea creíble, y qué números mirar.
- Cómo se detectan **[anomalías](../glosario/03-aprendizaje-automatico.md#anomalia)** sin tener ejemplos de defecto.
- Cómo se **elige** el modelo que va a la línea con una regla escrita de antemano.
- Qué pasa al entrenar con **datos de tu propia línea**.

| Bloque | Concepto | Laboratorio |
|--------|----------|-------------|
| 1 | Predicción de defectos | [M03-01](M03-01-prediccion-defectos.md) |
| 2 | Detección de anomalías | [M03-02](M03-02-anomalias.md) |
| 3 | Comparación y elección de modelos | [M03-03](M03-03-comparacion-modelos.md) |
| 4 | Entrenar con datos de la propia línea | [M03-04](M03-04-entrenar-datos-linea.md) |

## Antes de empezar

Los bloques 1 a 3 usan el [histórico](../glosario/01-datos-arquitectura.md#historico) preparado en el M02-03 (`infra/data/limpio.csv`). Si no lo tienes, genéralo:

```bash
cd infra
docker compose --profile lab run --rm --no-deps lab m02-03
```

El bloque 4 usa el [dataset](../glosario/01-datos-arquitectura.md#dataset) propio del M02-04 (`infra/data/dataset_linea.csv`).

## Introducción: de la regla escrita al modelo aprendido

Hasta ahora, las decisiones las tomaban **reglas escritas por personas**: «si la temperatura pasa de 70 °C, avisa». Una regla así es clara, pero solo mira una señal y solo sabe lo que su autor supo escribir.

Un **modelo** aprende la regla **a partir de ejemplos**: se le enseñan muchas piezas pasadas con sus [señales](../glosario/03-aprendizaje-automatico.md#senal) y su resultado, y busca qué combinaciones de señales acaban en defecto.

| | Regla escrita | Modelo aprendido |
|--|---------------|------------------|
| Quién la decide | Una persona | Los datos |
| Cuántas señales mira | Normalmente una | Todas a la vez |
| Cómo se explica | Se lee | Depende del modelo |
| Cómo se equivoca | Siempre igual | Según lo que haya visto |

Un modelo **se equivoca**: la pregunta no es si acierta, sino **cuánto y en qué**.

---

## Bloque 1 — Predicción de defectos

### Teoría

Un **clasificador** recibe las señales de una pieza (temperatura, vibración, corriente, presión) y devuelve una **probabilidad de defecto**. Si pasa de un **[umbral](../glosario/03-aprendizaje-automatico.md#umbral)** (normalmente 0,5), dice «defecto».

Para saber si sirve, se le examina con piezas que **[no ha visto](../glosario/03-aprendizaje-automatico.md#particion)**, y se cuentan cuatro casos:

| | El modelo dijo «defecto» | El modelo dijo «buena» |
|--|--------------------------|------------------------|
| **Era defectuosa** | Defecto encontrado | **Defecto que se escapa** |
| **Era buena** | **[Falsa alarma](../glosario/03-aprendizaje-automatico.md#matriz-confusion)** | Bien |

En planta importan dos números: **cuántos defectos encuentra** (recall) y **cuántas piezas buenas para sin motivo** (falsas alarmas). El porcentaje de acierto global engaña cuando el defecto es raro.

### Demostración

**Qué se demuestra:** por qué el porcentaje de acierto engaña, con una regla escrita a mano sobre el histórico. En el laboratorio entrenarás un modelo de verdad y lo medirás igual.

#### Paso 1 — ¿Cuántas piezas defectuosas hay?

**Qué vamos a ver:** el balance del histórico. Es lo primero que se mira antes de entrenar nada.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS piezas, SUM(defecto) AS defectuosas,
          ROUND(100.0 * SUM(defecto) / COUNT(*), 1) AS porcentaje
   FROM limpio"
```

**Resultado esperado:**

```text
 piezas  defectuosas  porcentaje
    768           68         8.9
```

**Cómo se lee:** solo un 8,9 % de las piezas son defectuosas. Un «modelo» que dijera siempre «buena» acertaría el **91 %** de las veces y no encontraría **ni un defecto**.

> **Qué señalar en pantalla:** «Por eso nunca preguntamos cuánto acierta, sino cuántos defectos encuentra».

#### Paso 2 — Una regla a mano

**Qué vamos a ver:** una regla escrita por una persona, «defecto si la temperatura pasa de 65 °C», medida con los cuatro casos.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT SUM(temperatura_c > 65 AND defecto = 1) AS defectos_encontrados,
          SUM(temperatura_c <= 65 AND defecto = 1) AS defectos_escapados,
          SUM(temperatura_c > 65 AND defecto = 0) AS falsas_alarmas,
          SUM(temperatura_c <= 65 AND defecto = 0) AS buenas_bien
   FROM limpio"
```

**Resultado esperado:**

```text
 defectos_encontrados  defectos_escapados  falsas_alarmas  buenas_bien
                   50                  18              28          672
```

**Cómo se lee:**

| Caso | Piezas | Qué significa en planta |
|------|--------|-------------------------|
| Defectos encontrados | 50 de 68 | Se paran a tiempo |
| Defectos escapados | 18 | **Llegan al cliente** |
| Falsas alarmas | 28 | Piezas buenas que alguien revisa para nada |
| Buenas bien | 672 | — |

El acierto global sería (50 + 672) / 768 = 94 %. Parece muy bueno, y se escapan 18 defectos.

> **Qué señalar en pantalla:** la regla mira solo la temperatura. ¿Y si los defectos dependieran también de la vibración o la presión?

#### Paso 3 — La pregunta que abre el laboratorio

> **¿Puede una máquina encontrar, mirando todas las señales a la vez, una regla que deje escapar menos defectos sin disparar las falsas alarmas?**

### Ahora tú: M03-01

→ **[M03-01 — Predicción de defectos de fabricación](M03-01-prediccion-defectos.md)**

Entrenarás un modelo con el pasado y lo examinarás con el futuro, leerás su matriz de confusión, moverás el umbral de decisión para ver el equilibrio entre defectos encontrados y falsas alarmas, y comprobarás qué pasa si no se le avisa de que el defecto es raro.

---

## Bloque 2 — Detección de anomalías

### Teoría

A veces **no hay [etiqueta](../glosario/03-aprendizaje-automatico.md#etiqueta)**: la máquina hace algo que no se había visto nunca (un rodamiento que empieza a fallar) y nadie ha marcado aún esas piezas. Un **detector de anomalías** no aprende qué es un defecto: aprende **cómo es lo normal** y avisa de lo que se aleja.

La clave es mirar **todas las señales a la vez**. Un ciclo puede tener cada señal dentro de su rango y ser raro en conjunto (por ejemplo, mucha vibración con muy poca corriente).

### Demostración

**Qué se demuestra:** qué es «lo normal» de la estación, señal a señal, y por qué no basta con mirar cada una por separado. En el laboratorio ajustarás un detector que mira las señales juntas.

#### Paso 1 — El rango normal de cada señal

**Qué vamos a ver:** el mínimo y el máximo de cada señal en las piezas buenas del histórico.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT ROUND(MIN(temperatura_c), 2) AS temp_min, ROUND(MAX(temperatura_c), 2) AS temp_max,
          ROUND(MIN(vibracion_mm_s), 3) AS vib_min, ROUND(MAX(vibracion_mm_s), 3) AS vib_max,
          ROUND(MIN(corriente_a), 2) AS corr_min, ROUND(MAX(corriente_a), 2) AS corr_max
   FROM limpio WHERE defecto = 0"
```

**Resultado esperado:**

```text
 temp_min  temp_max  vib_min  vib_max  corr_min  corr_max
    54.83     65.62    0.058      0.4       3.6      4.61
```

**Cómo se lee:** una regla por señal diría «es normal si la temperatura está entre 54,8 y 65,6, la vibración entre 0,06 y 0,40 y la corriente entre 3,6 y 4,6».

> **Qué señalar en pantalla:** imaginad una pieza a 55 °C, con vibración de 0,40 y corriente de 3,6. Cada señal está dentro de su rango. ¿Es normal esa combinación? Probablemente no: cada valor está en un extremo distinto. Ninguna regla por señal lo vería.

#### Paso 2 — La pregunta que abre el laboratorio

> **¿Cómo se mide «cuánto se aleja un ciclo de lo normal» con todas las señales a la vez, y dónde se pone el límite?**

### Ahora tú: M03-02

→ **[M03-02 — Detección temprana de anomalías](M03-02-anomalias.md)**

Ajustarás un detector con ciclos normales, comprobarás si avisa los 20 ciclos con un rodamiento fallando, investigarás con tus consultas cuánto se alejan, y moverás el umbral para ver el equilibrio entre avisar a tiempo y llenar el turno de falsas alarmas.

---

## Bloque 3 — Comparación y elección de modelos

### Teoría

Cuando hay varios modelos candidatos, la elección es una **decisión de proceso**, no técnica. Para que sea justa:

1. Todos se entrenan y se examinan con **las mismas piezas**.
2. La **regla de elección se escribe antes** de ver los resultados.
3. El elegido queda con **nombre y versión**, porque es lo que se despliega y se audita.

Y una cuarta, que en planta pesa mucho: **que se pueda explicar**. Un [árbol de decisión](../glosario/03-aprendizaje-automatico.md#arbol) se lee como reglas; una red neuronal, no.

### Demostración

**Qué se demuestra:** cómo es «la misma vara»: el corte en el tiempo que usarán todos los candidatos. En el laboratorio compararás dos modelos (y una red neuronal) y leerás las reglas del ganador.

#### Paso 1 — Dónde se corta

**Qué vamos a ver:** las piezas van ordenadas por identificador, que aquí hace de tiempo. El 70 % primero entrena; el 30 % último examina. Se busca la primera pieza de examen.

```bash
# 768 piezas × 0,7 = 537: la pieza en la posición 538 es la primera de examen
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id AS primera_de_examen FROM limpio ORDER BY pieza_id LIMIT 1 OFFSET 537"
```

**Resultado esperado:**

```text
primera_de_examen
            H0558
```

#### Paso 2 — Qué hay en cada tramo

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT CASE WHEN pieza_id < 'H0558' THEN 'entrenamiento' ELSE 'examen' END AS tramo,
          COUNT(*) AS piezas, SUM(defecto) AS defectuosas
   FROM limpio GROUP BY 1"
```

**Resultado esperado:**

```text
        tramo  piezas  defectuosas
entrenamiento     537           47
       examen     231           21
```

**Cómo se lee:** cada candidato aprenderá de las mismas 537 piezas (47 defectuosas) y se le examinará con las mismas 231 (21 defectuosas). Si uno se examinara con otras piezas, podría parecer mejor solo porque le tocaron más fáciles.

> **Qué señalar en pantalla:** se corta en el tiempo, no al azar, porque así se usará el modelo: aprendiendo del pasado para decidir sobre lo que viene.

#### Paso 3 — La pregunta que abre el laboratorio

> **Si un modelo encuentra un defecto más y otro da treinta falsas alarmas menos, ¿con cuál os quedáis? ¿Y quién decide esa regla?**

### Ahora tú: M03-03

→ **[M03-03 — Comparación de modelos predictivos](M03-03-comparacion-modelos.md)**

Compararás una [regresión logística](../glosario/03-aprendizaje-automatico.md#regresion-logistica) y un árbol con la misma vara, leerás las reglas que ha aprendido el árbol y añadirás una red neuronal como tercer candidato, con y sin [escalar](../glosario/03-aprendizaje-automatico.md#escalado) las señales.

---

## Bloque 4 — Entrenar con datos de la propia línea

### Teoría

Los bloques anteriores usan un histórico generado por el laboratorio. En el M02-04 construiste **tu propio dataset**: las carcasas que fabricó tu estación, con su resultado de calidad. Entrenar con él es lo más parecido al trabajo real: pocos cientos de piezas, pocos defectos y etiquetas con error.

### Demostración

**Qué se demuestra:** cómo es el dataset propio antes de entrenar. En el laboratorio entrenarás con él y comprobarás si el modelo descubre el criterio de calidad.

#### Paso 1 — El dataset de tu línea

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS piezas, SUM(defecto) AS defectuosas, MIN(ts) AS desde, MAX(ts) AS hasta
   FROM dataset_linea"
```

**Resultado esperado** (cambian los números: es tu producción):

```text
 piezas  defectuosas                     desde                     hasta
    426           48 2026-11-06T02:04:11+00:00 2026-11-06T02:11:48+00:00
```

**Cómo se lee:** unos siete minutos de producción, con 48 defectuosas. Con un corte 70/30, el examen tendrá unos 14 defectos: muy pocos para medir con precisión.

#### Paso 2 — La pregunta que abre el laboratorio

> **Con tan pocos datos, ¿descubrirá un modelo el criterio de calidad que encontrasteis a mano en el M02-04?**

### Ahora tú: M03-04

→ **[M03-04 — Entrenar con los datos de tu línea](M03-04-entrenar-datos-linea.md)**

Entrenarás un árbol y una red con tu dataset, leerás qué señales ha usado el árbol y sus reglas, y comprobarás cuánto cambia el resultado al recoger más producción.

---

## Conclusiones del módulo

### Qué es un modelo de aprendizaje automático en planta

Una regla que se aprende de ejemplos en lugar de escribirse. Mira todas las señales a la vez, se equivoca, y su valor depende de con qué datos aprendió y de cómo se mide.

### Cómo debe tratarse

| Requisito | Dónde lo has trabajado |
|-----------|------------------------|
| Examinar con piezas que no ha visto, en orden de tiempo | M03-01, M03-03 |
| Medir defectos encontrados y falsas alarmas, no el acierto global | M03-01 |
| Elegir el umbral según qué error cuesta más | M03-01, M03-02 |
| Elegir el modelo con una regla escrita, y que se pueda explicar | M03-03 |
| Desconfiar de los porcentajes con pocos datos | M03-04 |

### Lo que has visto romperse

| Fallo | Dónde | Qué enseña |
|-------|-------|------------|
| Acierto del 94 % con 18 defectos escapados | Demo del bloque 1 | El acierto global engaña |
| Modelo sin [equilibrar](../glosario/03-aprendizaje-automatico.md#desequilibrio) que deja escapar defectos | M03-01 | Hay que decirle que el defecto es raro |
| Red sin escalar que no encuentra ningún defecto | M03-03 | Un error silencioso: el comando no falla |
| Árbol que aprende un corte espurio | M03-04 | Con pocos datos, el modelo aprende parte del ruido |

### En una frase

> 🔑 Un modelo se juzga por los defectos que deja escapar y las piezas buenas que para, examinado con piezas que no ha visto, y elegido con una regla que alguien pueda defender.
