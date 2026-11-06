# M02-03 — Preparación de información para analítica

[← Página anterior](M02-02-protocolos.md) · [Siguiente página →](M02-04-dataset-linea.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **preparación del dato para analítica**: qué problemas trae un histórico real, cómo debe quedar un dataset para entrenar, cómo se detectan los datos malos y cómo se tratan sin esconderlos.

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

Antes de entrenar hay que limpiar y, sobre todo, **contar lo que se descarta**. Un modelo entrenado con temperaturas de 9999 o de 614 °C aprende cosas que no existen en la máquina.

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

32 piezas sin temperatura y 6 con 9999 no pasan al limpio.

### 2 — Mirar los tres ficheros

Vas a comparar el crudo, el limpio y los imposibles. El crudo conserva el desastre, el limpio es lo que se entrena y los 9999 no se convierten en una temperatura.

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

**Una pieza, una fila**

Cuenta filas y valores distintos de `pieza_id` en el limpio.

```bash
docker compose --profile lab run --rm --no-deps --entrypoint python lab -c \
  "import pandas as pd; d = pd.read_csv('/data/limpio.csv'); print(len(d), d.pieza_id.nunique())"
```

→ Los dos números son iguales (768 768).

## Reto

### 1 — No rellenes el hueco

Busca en el crudo una pieza con la temperatura vacía y comprueba que no está en el limpio.

```bash
# Piezas con la temperatura vacía (dos comas seguidas)
grep ',,' data/crudo.csv | head -3

# ¿Está H0017 en el limpio? Cuenta sus líneas
grep -c '^H0017,' data/limpio.csv
```

<details>
<summary>Ver solución</summary>

```text
H0017,,0.28,4.34,6.07,0
H0065,,0.225,4.23,6.01,0
H0080,,0.196,4.07,6.03,0
0
```

La pieza no aparece en `limpio.csv`: se excluye, no se sustituye por la media. Rellenarla escondería un sensor mudo.

</details>

## IA para datos no estructurados: las notas de turno

**Qué ocurre:** no todo el dato de planta está en tablas. Mucha información útil está en **notas escritas a mano** por el turno: «10:15 cambio de herramienta, la P0412 salió con rebaba». Para usarla hay que convertir cada nota en datos: qué pieza, a qué hora y qué causa.

Vas a pedírselo al **modelo de lenguaje local**, comprobar cuánto acierta y mejorarlo en dos pasos. Las notas, con la respuesta correcta de cada una para poder medir, están en `infra/linea/docs/notas-turno.csv`.

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

**Qué ocurre:** usas un prompt que le **enseña con ejemplos** cómo es una nota y cómo es su JSON (`infra/linea/docs/prompt-notas-ejemplos.txt`).

```bash
cat linea/docs/prompt-notas-ejemplos.txt
docker compose --profile lab run --rm --no-deps lab notas ejemplos
```

**Resultado esperado:** entre **3 y 4 de 8** notas bien. Mira los errores que quedan:

- Pieza y hora salen casi siempre bien.
- La **causa** falla: llama «refrigeración» a una rebaba de herramienta.
- A veces **se inventa una pieza** en una nota que no tiene ninguna, copiada de los ejemplos del prompt.

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
| Lo descartado, contado | 800 → 768: 32 huecos y 6 imposibles |

### Cómo se detectan los datos malos

| Problema | Qué pasó en la máquina | Cómo se detecta |
|----------|------------------------|-----------------|
| Hueco | Sensor desconectado | Campo vacío |
| Unidad distinta | Un equipo reporta en décimas | Valores fuera de rango físico, del orden de 10 veces lo normal |
| Sensor clavado | Valor de error del sensor | Un valor fijo imposible (9999) |
| Pieza repetida | Identificador que se reinicia (M01-01) | Contar filas frente a identificadores distintos |

### Cómo se tratan sin esconderlos

- **No rellenar huecos con la media**: escondería un sensor mudo y metería en el entrenamiento un dato que nadie midió.
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
