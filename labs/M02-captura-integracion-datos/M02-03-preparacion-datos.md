# M02-03 — Preparación de información para analítica

[← Página anterior](M02-02-protocolos.md) · [Siguiente página →](../M03-ml-prediccion-anomalias/README.md)

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

### En una frase

> 🔑 Un modelo aprende lo que hay en el fichero. Preparar el dato es decidir, y dejar escrito, qué parte del histórico es la realidad.
