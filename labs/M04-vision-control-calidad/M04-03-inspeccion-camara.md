# M04-03 — Sistema de inspección basado en cámara

[← Página anterior](M04-02-deteccion-defectos.md) · [Siguiente página →](../M05-ia-generativa/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Cierras el flujo de inspección: entra una carpeta de imágenes y sale un registro con una decisión por pieza.

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

## Reto

### 1 — El umbral

¿Qué pasaría con `ko_00.png` si el umbral de `revisar` bajara de 0,5 a 0,4? ¿Y con las buenas?

<details>
<summary>Ver solución</summary>

`ko_00.png` (0,493) pasaría a `revisar`. Las buenas siguen en `aceptar` porque la más alta está en 0,345. Bajar el umbral recupera defectos a cambio de mandar más piezas a revisión: la misma balanza que el recall y las falsas alarmas de M03.

</details>

### 2 — Sin foto

Si falta la imagen de una pieza, ¿se acepta?

<details>
<summary>Ver solución</summary>

No. Sin imagen no hay fila de aceptación. En planta, una pieza sin dictamen iría a revisión por ausencia.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el registro no tiene una fila por imagen` | el lote no se copió | repite `m04-03` |
| `FALLO: ninguna pieza fue a revisión` | el modelo no se cargó bien | lanza antes `m04-01` |

## Conclusiones

- **Un puesto de inspección es un flujo:** entran fotos y sale un registro con una decisión por pieza.
- **Inspeccionar no es entrenar.** Se usa el modelo que ya existe.
- **La decisión depende del umbral.** `ko_00.png` era defectuosa y se aceptó con 0,493, justo por debajo de 0,5.
- **Mover el umbral es cambiar el equilibrio:** más defectos detectados a cambio de más piezas buenas a revisión.

> 🔑 Ningún modelo es perfecto: hay que decidir, con calidad, qué error es más caro, si dejar pasar un defecto o parar una pieza buena.
