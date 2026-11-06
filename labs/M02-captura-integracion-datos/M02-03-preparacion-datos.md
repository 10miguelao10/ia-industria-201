# M02-03 — Preparación de información para analítica

[← Página anterior](M02-02-protocolos.md) · [Siguiente página →](M02-04-dataset-linea.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **preparación del dato para analítica**: qué problemas trae un [histórico](../glosario/01-datos-arquitectura.md#historico) real, cómo debe quedar un [dataset](../glosario/01-datos-arquitectura.md#dataset) para entrenar, cómo se detectan los datos malos y cómo se tratan sin esconderlos.

### Prerrequisitos

- Solo el contenedor `lab`. No hace falta la línea en vivo.
- Genera `infra/data/crudo.csv`, `limpio.csv` e `imposibles.csv` (pocos MB).

### Qué está pasando

Ingeniería de procesos quiere entrenar un modelo con **800 carcasas** del histórico de EST-01. Cada una tiene sus señales (temperatura, vibración, corriente y presión) y la columna `defecto`, que pone **calidad** después de inspeccionarla.

Pero el histórico real nunca viene limpio. En este hay tres problemas típicos:

| Problema | Qué pasó en la máquina | Cómo aparece en el fichero |
|----------|------------------------|----------------------------|
| Hueco | El sensor se desconectó en esa pieza | Temperatura vacía |
| Unidad distinta | Un equipo reporta en décimas de grado | 614 en lugar de 61,4 |
| Sensor clavado | El sensor falló y devuelve su valor de error | 9999 |

Antes de entrenar hay que [limpiar](../glosario/01-datos-arquitectura.md#limpieza) y, sobre todo, **contar lo que se descarta**. Un modelo entrenado con temperaturas de 9999 o de 614 °C aprende cosas que no existen en la máquina.

Este paso no necesita la estación en marcha: trabaja sobre un histórico ya guardado.

### 1 — Generar y limpiar

Vas a generar el histórico crudo y limpiarlo. Antes de fiarte de un modelo tienes que saber cuántas filas sobrevivieron y por qué se cayeron las demás.

```bash
# Escribe crudo.csv, lo limpia y deja limpio.csv e imposibles.csv
docker compose --profile lab run --rm --no-deps lab m02-03
```

📋 Ficha del comando [`m02-03`](../comandos-lab.md#m02-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
{"filas_crudo": 800, "filas_limpias": 768, "huecos": 32, "imposibles": 6, "piezas_unicas": 768}
OK m02-03: crudo=800 limpio=768 huecos=32
```

**Cómo se lee:** de 800 piezas quedan 768. Fíjate en que el resumen llama `huecos` a 32 piezas, pero son dos problemas distintos: **26 sin temperatura y 6 con el sensor clavado en 9999**, que el comando convierte en vacío antes de descartarlas. Leer bien qué cuenta cada número de un resumen también es preparar el dato. Lo comprobarás tú en «Investiga».

### 2 — Mirar los tres ficheros

**Qué ocurre:** abres primero los ficheros en VS Code (`infra/data/crudo.csv`, `limpio.csv` e `imposibles.csv`) y te desplazas por ellos: el crudo conserva el desastre, el limpio es lo que se entrena y los 9999 no se convierten en una temperatura. Después, para compararlos rápido, miras sus primeras líneas desde la terminal:

```bash
head -5 data/crudo.csv        # tal cual llegó
head -5 data/limpio.csv       # una fila por pieza, en grados, con la columna hueco
head -5 data/imposibles.csv   # los 9999 apartados
```

**Resultado esperado:**

```text
pieza_id,temperatura_c,vibracion_mm_s,corriente_a,presion_bar,defecto
H0001,61.39,0.286,4.07,5.96,0
H0002,61.45,0.268,4.06,6.0,0
H0003,62.95,0.263,3.85,6.1,0
H0004,62.56,0.347,4.29,5.95,0
```

```text
pieza_id,temperatura_c,vibracion_mm_s,corriente_a,presion_bar,defecto,hueco
H0001,61.39,0.286,4.07,5.96,0,0
H0002,61.45,0.268,4.06,6.0,0,0
H0003,62.95,0.263,3.85,6.1,0,0
H0004,62.56,0.347,4.29,5.95,0,0
```

```text
pieza_id,temperatura_c,vibracion_mm_s,corriente_a,presion_bar,defecto
H0059,9999.0,0.218,4.22,6.09,0
H0322,9999.0,0.244,4.15,5.95,1
H0510,9999.0,0.289,4.0,5.94,0
H0601,9999.0,0.286,4.12,6.06,0
```

También puedes abrirlos en VS Code: están en `infra/data/`.

## Comprueba tu entendimiento

**Qué no está en el limpio**

¿Hay alguna pieza con 9999 en `limpio.csv`?

→ No: están apartadas en `imposibles.csv`. Lo comprobarás con una consulta en «Investiga».

## Investiga: cuenta tú los problemas

**Qué ocurre:** `lab sql` (la herramienta del M01-01) también consulta los CSV de `infra/data/` como si fueran tablas: `crudo`, `limpio`, `imposibles`… Vas a contar cada problema en el crudo y a comprobar que el limpio está como debe.

📋 Ficha del comando [`sql`](../comandos-lab.md#sql).

### 1 — Los problemas del crudo, uno a uno

```bash
#   IS NULL: valor vacío   = 9999: sensor clavado   > 150 y < 9999: viene en décimas
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS piezas,
          SUM(temperatura_c IS NULL) AS huecos,
          SUM(temperatura_c = 9999) AS clavados,
          SUM(temperatura_c > 150 AND temperatura_c < 9999) AS en_decimas
   FROM crudo"
```

**Resultado esperado:**

```text
 piezas  huecos  clavados  en_decimas
    800      26         6          12
```

**Cómo se lee:** 26 + 6 = 32 piezas sin una temperatura real, que se descartan. Las 12 en décimas se **corrigen** dividiendo entre 10 y se quedan. 800 − 32 = 768, las filas del limpio.

### 2 — Ver las piezas en décimas

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, temperatura_c FROM crudo WHERE temperatura_c > 150 AND temperatura_c < 9999 LIMIT 3"
```

```text
pieza_id  temperatura_c
   H0025          601.1
   H0036          618.9
   H0100          594.5
```

Comprueba una en el limpio:

```bash
docker compose --profile lab run --rm --no-deps lab sql "SELECT pieza_id, temperatura_c FROM limpio WHERE pieza_id = 'H0025'"
```

**Resultado esperado:** `H0025` con `60.11`: se ha corregido, no descartado.

### 3 — Una pieza, una fila, y cómo son las defectuosas

```bash
# ¿Hay piezas repetidas en el limpio?
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS filas, COUNT(DISTINCT pieza_id) AS piezas FROM limpio"

# Medias de las señales en piezas buenas y defectuosas
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT defecto, COUNT(*) AS piezas, ROUND(AVG(temperatura_c), 2) AS temp,
          ROUND(AVG(vibracion_mm_s), 3) AS vib, ROUND(AVG(corriente_a), 2) AS corriente,
          ROUND(AVG(presion_bar), 2) AS presion
   FROM limpio GROUP BY defecto"
```

**Resultado esperado:**

```text
 filas  piezas
   768     768
```

```text
 defecto  piezas  temp   vib  corriente  presion
       0     700 61.72 0.248       4.11     6.00
       1      68 65.30 0.264       4.10     5.99
```

**Cómo se lee:** una fila por pieza, como debe ser. Y una pista para el M03: las piezas defectuosas tienen, de media, **3,6 °C más** y algo más de vibración; corriente y presión, casi iguales. Un modelo tendrá de dónde aprender.

## Experimenta: ¿y si rellenamos los huecos con la media?

**Qué ocurre:** es una tentación habitual: en lugar de quitar las piezas sin temperatura, ponerles la temperatura media. El comando lo hace en un fichero aparte (`limpio_relleno.csv`) y compara los dos resultados.

**Predice:** ¿qué le pasa a la distribución de temperaturas?

```bash
docker compose --profile lab run --rm --no-deps lab m02-03 rellenar
```

**Resultado esperado:**

```text
{"filas_crudo": 800, "filas_limpias": 768, "huecos": 32, "imposibles": 6, "piezas_unicas": 768}
relleno: 26 huecos rellenados con la media 62.04 °C -> limpio_relleno.csv
  piezas con temperatura exactamente 62.04: limpio=2 relleno=28
  desviación típica de la temperatura: limpio=2.354 relleno=2.315
OK m02-03: crudo=800 limpio=768 huecos=32
```

**Cómo se lee:** ahora hay **28 piezas con exactamente 62,04 °C**, cuando en la realidad había 2. Se ha creado un pico artificial en la media, y la dispersión de los datos ha bajado: el dataset parece **más tranquilo de lo que fue la línea**. Peor aún: si los huecos no fueran al azar (por ejemplo, si el sensor se desconecta cuando la máquina se calienta), las piezas rellenadas serían justo las más interesantes, y el modelo aprendería que eran normales.

## Reto

### 1 — No rellenes el hueco

Busca en el crudo una pieza con la temperatura vacía y comprueba que no está en el limpio.

```bash
# Piezas con la temperatura vacía
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, temperatura_c, vibracion_mm_s FROM crudo WHERE temperatura_c IS NULL LIMIT 3"

# ¿Está H0017 en el limpio?
docker compose --profile lab run --rm --no-deps lab sql "SELECT COUNT(*) AS veces FROM limpio WHERE pieza_id = 'H0017'"
```

<details>
<summary>Ver solución</summary>

```text
pieza_id temperatura_c  vibracion_mm_s
   H0017          None           0.280
   H0065          None           0.225
   H0080          None           0.196
```

```text
 veces
     0
```

La pieza no aparece en `limpio.csv`: se excluye, no se sustituye por la media. Rellenarla escondería un sensor mudo.

</details>

## IA para datos no estructurados: las notas de turno

**Qué ocurre:** no todo el dato de planta está en tablas. Mucha información útil está en **notas escritas a mano** por el turno: «10:15 cambio de herramienta, la P0412 salió con rebaba». Para usarla hay que convertir cada nota en datos: qué pieza, a qué hora y qué causa.

Vas a pedírselo al **[modelo de lenguaje](../glosario/04-ia-generativa.md#llm) local**, comprobar cuánto acierta y mejorarlo en dos pasos. Las notas, con la respuesta correcta de cada una para poder medir, están en `infra/linea/docs/notas-turno.csv`.

Necesita el modelo en marcha:

```bash
docker compose up -d llm
curl -s http://localhost:8088/salud
```

📋 Ficha del comando [`notas`](../comandos-lab.md#notas).

### 1 — Con un prompt sencillo

**Qué ocurre:** el modelo recibe cada nota con una instrucción directa (`infra/linea/docs/prompt-notas.txt`) y devuelve un JSON. El código valida el formato y lo compara con la respuesta correcta.

```bash
cat linea/docs/prompt-notas.txt
docker compose --profile lab run --rm --no-deps lab notas
```

**Resultado esperado** (la redacción cambia en cada ejecución):

```text
                                          nota pieza  hora                                       causa formato correcto
10:15 cambio de herramienta en EST-01, la P04… P0000 10:15                                 herramienta      ok       NO
A las 11h40 vibraba mucho el husillo. Paro de… P0587 11:40                   una de: vibracion, 5 min.     MAL       NO
...
OK notas: 0 de 8 notas extraídas sin error
```

**Cómo se lee:** **ninguna** nota sale bien. El modelo copia literalmente partes de la instrucción: pone `P0000` (el ejemplo de formato) o escribe «una de: vibracion…». Un modelo pequeño no distingue bien entre la plantilla y el contenido.

### 2 — Con ejemplos

**Qué ocurre:** usas un [prompt](../glosario/04-ia-generativa.md#prompt) que le **enseña [con ejemplos](../glosario/04-ia-generativa.md#few-shot)** cómo es una nota y cómo es su JSON (`infra/linea/docs/prompt-notas-ejemplos.txt`).

```bash
cat linea/docs/prompt-notas-ejemplos.txt
docker compose --profile lab run --rm --no-deps lab notas ejemplos
```

**Resultado esperado:** entre **3 y 4 de 8** notas bien. Mira los errores que quedan:

- Pieza y hora salen casi siempre bien.
- La **causa** falla: llama «refrigeración» a una rebaba de herramienta.
- A veces **[se inventa](../glosario/04-ia-generativa.md#alucinacion) una pieza** en una nota que no tiene ninguna, copiada de los ejemplos del prompt.

### 3 — Lo que tiene formato, con código

**Qué ocurre:** la pieza (`P` y cuatro cifras) y la hora (`10:15`, `11h40`) tienen un **formato fijo**: se pueden sacar con un patrón, sin modelo. En modo `hibrido`, el código extrae pieza y hora, y el modelo solo clasifica la causa.

```bash
docker compose --profile lab run --rm --no-deps lab notas ejemplos hibrido
```

**Resultado esperado:**

```text
prompt: linea/docs/prompt-notas-ejemplos.txt   modo híbrido: pieza y hora con código, causa con el modelo
                                       nota pieza  hora         causa formato correcto
10:15 cambio de herramienta en EST-01, la … P0412 10:15 refrigeracion      ok       NO
A las 11h40 vibraba mucho el husillo. Paro… P0587 11:40     vibracion      ok       sí
12:05 - P0633 rechazada en calidad, marca … P0633 12:05      sujecion      ok       sí
...
OK notas: 5 de 8 notas extraídas sin error
```

**Cómo se lee:** pieza y hora, **siempre bien**. Solo fallan algunas causas, y esas ya no son un problema de formato, sino de comprensión. En una planta, esas son las que revisaría una persona. La progresión 0 → 3–4 → 5 de 8 resume cómo se usa bien la IA para preparar datos: **código para lo que tiene reglas, modelo para lo que hay que interpretar, y siempre una validación**.

Puedes editar `infra/linea/docs/prompt-notas-ejemplos.txt` (por ejemplo, añadir un ejemplo de rebaba con causa `herramienta`) y repetir el paso 3 para ver si mejora.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la temperatura limpia no está en grados` | una décima no se escaló | vuelve a lanzar `m02-03`: el comando es quien limpia |
| `FALLO: no se apartaron los 9999` | el crudo no trae 9999 | borra `data/crudo.csv` y repite el comando |

## Conclusiones

### Qué es preparar el dato

Es convertir el histórico tal como llegó en un **dataset**: una tabla con una fila por pieza, señales en unidades correctas y solo con valores que la máquina pudo medir de verdad. Es el paso que más tiempo lleva en cualquier proyecto de IA industrial.

### Cómo debe quedar un dataset para entrenar

| Requisito | En `limpio.csv` |
|-----------|-----------------|
| Una fila por pieza | 768 filas y 768 identificadores distintos |
| Unidades homogéneas | Todas las temperaturas entre 40 y 120 °C |
| Sin valores imposibles | Los 9999 apartados en `imposibles.csv` |
| Lo descartado, contado | 800 → 768: 26 huecos y 6 imposibles (el resumen los cuenta juntos como 32) |

### Cómo se detectan los datos malos

| Problema | Qué pasó en la máquina | Cómo se detecta |
|----------|------------------------|-----------------|
| Hueco | Sensor desconectado | Campo vacío |
| Unidad distinta | Un equipo reporta en décimas | Valores fuera de rango físico, del orden de 10 veces lo normal |
| Sensor clavado | Valor de error del sensor | Un valor fijo imposible (9999) |
| Pieza repetida | Identificador que se reinicia (M01-01) | Contar filas frente a identificadores distintos |

### Cómo se tratan sin esconderlos

- **No rellenar huecos con la media**: escondería un sensor mudo y metería en el entrenamiento un dato que nadie midió. En el experimento, 28 piezas con exactamente 62,04 °C donde la realidad tenía 2.
- **Corregir solo lo que tiene una causa conocida**, como dividir entre 10 las décimas.
- **Apartar, no borrar**: los imposibles se guardan aparte para poder revisarlos y avisar a mantenimiento.
- **Dejar el recuento escrito** para que quien use el dataset sepa qué se quitó y por qué.

### Cuando el dato es texto

| Modo | Notas correctas | Qué enseña |
|------|-----------------|------------|
| Prompt sencillo | 0 de 8 | Un modelo pequeño copia la plantilla en lugar de rellenarla |
| Prompt con ejemplos | 3–4 de 8 | Los ejemplos ayudan, pero el modelo puede copiar datos de ellos |
| Código para pieza y hora, modelo para la causa | 5 de 8 | Lo que tiene formato fijo se saca con reglas; el modelo, solo para interpretar |

Convertir texto en datos con un modelo es útil, pero **siempre se valida** con código y se mide contra casos conocidos antes de fiarse.

### En una frase

> 🔑 Un modelo aprende lo que hay en el fichero. Preparar el dato es decidir, y dejar escrito, qué parte del histórico es la realidad.
