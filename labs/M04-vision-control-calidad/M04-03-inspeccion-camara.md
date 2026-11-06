# M04-03 — Sistema de inspección basado en cámara

[← Página anterior](M04-02-deteccion-defectos.md) · [Siguiente página →](M04-04-red-neuronal.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo funciona un **puesto de inspección**: cómo pasa una pieza de foto a decisión, cómo debe ser el registro que deja, qué papel tiene el umbral y cómo se decide dónde ponerlo.

### Prerrequisitos

- `modelo_vision.joblib` de M04-01.
- Escribe `data/lote_entrada/` y `data/lote_resultado.csv`.

### Qué está pasando

Así trabaja un puesto de inspección en la línea: las fotos de las carcasas llegan a una **carpeta de entrada** y el sistema deja un **registro** con una decisión por cada una, `aceptar` o `revisar`.

Llega un lote de 6 carcasas: 3 buenas y 3 con rayón. El modelo del M04-01 da a cada una una probabilidad de defecto. Con 0,5 o más va a revisión; por debajo se acepta. No se vuelve a entrenar nada: inspeccionar es usar el modelo que ya hay.

### 1 — Pasar el lote

Vas a inspeccionar un lote con el modelo ya entrenado. Inspeccionar es dar un dictamen por imagen, no volver a entrenar.

```bash
# Copia 6 imágenes a lote_entrada, las puntúa y escribe lote_resultado.csv
docker compose --profile lab run --rm --no-deps lab m04-03
```

📋 Ficha del comando [`m04-03`](../comandos-lab.md#m04-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493  aceptar
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=2
```

Fíjate en `ko_00.png`: es defectuosa, pero con 0,493 queda justo por debajo del umbral y se acepta. Es un defecto que se escapa.

### 2 — Leer el registro

Vas a abrir el registro que quedaría en el puesto de inspección.

```bash
cat data/lote_resultado.csv
ls data/lote_entrada
```

**Resultado esperado:**

```text
imagen,probabilidad_defecto,decision
ok_00.png,0.345,aceptar
ok_01.png,0.269,aceptar
ok_02.png,0.314,aceptar
ko_00.png,0.493,aceptar
ko_01.png,0.657,revisar
ko_02.png,0.714,revisar
```

```text
ko_00.png  ko_01.png  ko_02.png  ok_00.png  ok_01.png  ok_02.png
```

## Comprueba tu entendimiento

**El registro cuadra**

Cuenta filas del CSV (sin la cabecera) y ficheros en `lote_entrada`.

→ Seis y seis: cada imagen tiene su dictamen.

## Experimenta: mover el umbral

**Qué ocurre:** `ko_00.png` se escapa por 0,007. Vas a bajar el umbral de revisión de 0,5 a 0,4.

```bash
docker compose --profile lab run --rm --no-deps lab m04-03 umbral=0.4
```

**Resultado esperado:**

```text
umbral=0.4 duda=±0.0
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493  revisar
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=3
```

**Cómo se lee:** las tres defectuosas van a revisión y las tres buenas siguen aceptándose. Con este lote, 0,4 es mejor. Pero la buena con más probabilidad está en 0,345: con un umbral de 0,3 empezarías a parar piezas buenas. El margen entre «la mala más baja» (0,493) y «la buena más alta» (0,345) es estrecho, y con miles de piezas habrá solapes.

## Reto

### 1 — Quién decide el umbral

El modelo lo has entrenado tú. ¿Debes decidir tú también el umbral y el tamaño de la zona de duda?

<details>
<summary>Ver solución</summary>

No solo. El umbral decide cuántos defectos se escapan y cuántas piezas buenas se paran, y eso cuesta dinero y carga de trabajo. Lo decide **calidad**, con los números que tú le das (como el coste del M03-01) y con la capacidad del turno para revisar piezas dudosas.

</details>

### 2 — Sin foto

Si falta la imagen de una pieza, ¿se acepta?

<details>
<summary>Ver solución</summary>

No. Sin imagen no hay fila de aceptación. En planta, una pieza sin dictamen iría a revisión por ausencia.

</details>

## Mejora: una zona de duda

**Qué ocurre:** en lugar de obligar al umbral a decidir siempre, defines una **zona de duda**: las piezas cuya probabilidad esté a menos de 0,1 del umbral no se aceptan ni se rechazan: van a una persona. El parámetro `duda` lo activa.

```bash
docker compose --profile lab run --rm --no-deps lab m04-03 duda=0.1
```

**Resultado esperado:**

```text
umbral=0.5 duda=±0.1
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493   dudosa
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=2
```

**Cómo se lee:** `ko_00.png` ya no se acepta: queda como **dudosa**, para que la mire un operario. Las claras siguen decidiéndose solas. Es el diseño habitual de los puestos de inspección con IA: el modelo resuelve lo evidente y la persona, lo dudoso. El tamaño de la zona de duda se ajusta según cuántas piezas puede revisar el turno.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el registro no tiene una fila por imagen` | el lote no se copió | repite `m04-03` |
| `FALLO: ninguna pieza fue a revisión` | el modelo no se cargó bien | lanza antes `m04-01` |

## Conclusiones

### Qué es un puesto de inspección

Es el flujo completo: **entra la foto de cada pieza y sale una decisión con su registro**. No se entrena nada: se usa el modelo que ya existe.

```
 cámara ──▶ lote_entrada/ ──▶ modelo ──▶ probabilidad ──▶ umbral ──▶ aceptar / revisar ──▶ lote_resultado.csv
```

### Cómo debe ser el registro

| Requisito | En `lote_resultado.csv` |
|-----------|-------------------------|
| Una fila por pieza | 6 fotos, 6 filas |
| La decisión y su motivo | Decisión y probabilidad de defecto |
| Sin pieza sin dictamen | Si falta la foto, la pieza no se acepta |

### El papel del umbral

| Imagen | Probabilidad | Decisión | ¿Correcta? |
|--------|--------------|----------|------------|
| `ok_00.png` – `ok_02.png` | 0,27 – 0,35 | aceptar | Sí |
| `ko_00.png` | **0,493** | aceptar | **No: defecto que se escapa** |
| `ko_01.png`, `ko_02.png` | 0,66 – 0,71 | revisar | Sí |

Con el umbral en 0,5, una pieza defectuosa pasa. Con 0,4, se habría parado, y las buenas seguirían pasando.

### Cómo se decide el umbral

- No lo decide el modelo: lo decide **calidad**, según qué error cuesta más, si dejar pasar un defecto o revisar una pieza buena.
- Se revisa con **datos reales** del puesto, contando cuántos defectos se escapan y cuántas piezas buenas se paran con cada umbral.
- Las piezas **dudosas** (cerca del umbral) pueden ir a una revisión manual en lugar de decidirse solas.

### En una frase

> 🔑 Ningún modelo es perfecto: el umbral es una decisión de calidad sobre qué error se acepta, y tiene que estar escrita.
