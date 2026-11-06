# M02-04 — Construir un dataset con datos de la línea

[← Página anterior](M02-03-preparacion-datos.md) · [Siguiente página →](../M03-ml-prediccion-anomalias/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **construye un dataset para entrenar a partir de la producción real**: de dónde salen las señales y de dónde las etiquetas, cómo deben unirse dos sistemas distintos, qué errores aparecen al unirlos y cómo se evitan.

### Prerrequisitos

- M01-01 hecho: mosquitto, sensor y archivador en marcha.
- En este lab se añade el contenedor `calidad`. Hay que dejar la línea fabricando **al menos 5 minutos** (mejor 10) con `calidad` en marcha.

### Qué está pasando

En el M02-03 trabajaste con un histórico generado de golpe, con su columna `defecto` ya puesta. En una planta nadie te da eso: **hay que construirlo**. Las piezas de información vienen de dos sistemas distintos:

```
 estación ──▶ broker ──┬──▶ archivador ──▶ historial.sqlite       (señales: temperatura, vibración, corriente)
                       │
                       └──▶ calidad ────▶ calidad.sqlite          (resultado: buena o defectuosa)
```

- El **histórico** sabe cómo se fabricó cada carcasa, pero no si salió buena.
- **Calidad** inspecciona cada carcasa y apunta si es defectuosa, en su propia base de datos, como el sistema de calidad (QMS) de una planta.

Un **dataset** para entrenar es la unión de los dos: **para cada carcasa, sus señales y su resultado**. Unirlos bien es lo difícil, y es lo que trabajas en este lab.

Dos cosas que conviene saber de esta inspección simulada:
- **Tiene un criterio oculto**: nadie de la línea sabe por qué sale mala una carcasa. Lo descubrirás con los datos.
- **Se equivoca a veces**, como cualquier inspección real: alrededor de un 3 % de los dictámenes están mal.

| En la realidad | En este laboratorio |
|----------------|---------------------|
| Historian o base de datos del MES | `historial.sqlite`, que llena el archivador |
| Sistema de calidad (QMS), inspección manual o automática | Contenedor `calidad` y `calidad.sqlite` |
| Proceso ETL que junta los dos | El comando `m02-04` |

### 1 — Arrancar la inspección de calidad y dejar fabricar

**Qué ocurre:** arrancas el puesto de calidad. A partir de ahora inspecciona cada carcasa que publica la estación y apunta su resultado. Necesitas que acumule unos cientos de carcasas.

```bash
docker compose up -d calidad
docker compose logs --tail=1 calidad
```

**Resultado esperado:**

```text
calidad-1  | calidad: inspeccionando linea/est01/ciclo
```

Mientras esperas los 5–10 minutos, haz los pasos 2 y 3.

### 2 — Mirar la base de calidad

**Qué ocurre:** consultas la base de calidad. `lab sql` la tiene disponible como `calidad.inspecciones`, junto al histórico.

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT * FROM calidad.inspecciones ORDER BY id DESC LIMIT 3"
```

**Resultado esperado** (cambian las piezas y las horas):

```text
 id pieza_id                  ts_pieza  defecto             ts_inspeccion
475    P0123 2026-11-05T15:44:37+00:00        0 2026-11-05T15:44:37+00:00
474    P0122 2026-11-05T15:44:36+00:00        0 2026-11-05T15:44:36+00:00
473    P0121 2026-11-05T15:44:35+00:00        1 2026-11-05T15:44:35+00:00
```

**Cómo se lee:** cada inspección guarda la pieza (`pieza_id`), **la hora a la que se fabricó** (`ts_pieza`), el resultado (`defecto`: 1 = mala) y cuándo se inspeccionó. Calidad no guarda ninguna señal de la máquina: eso está en el histórico.

### 3 — Unir las dos fuentes: la trampa del identificador

**Qué ocurre:** antes de construir el dataset, compruebas cómo se unen las dos tablas. Lo natural sería unirlas por `pieza_id`. Pero en el M01-01 viste que la estación reinicia la numeración.

**Predice:** si la estación se ha reiniciado alguna vez desde que existe tu histórico, ¿qué pasará al unir solo por `pieza_id`?

Reinicia la estación para asegurarte de que hay identificadores repetidos, y espera un minuto:

```bash
docker compose restart sensor
```

Ahora cuenta cuántas filas salen uniendo de dos formas:

```bash
# Unir solo por identificador
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS filas FROM lecturas l JOIN calidad.inspecciones c ON l.pieza_id = c.pieza_id"

# Unir por identificador + hora de fabricación
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS filas FROM lecturas l
   JOIN calidad.inspecciones c ON l.pieza_id = c.pieza_id AND l.ts = c.ts_pieza"

# Cuántas inspecciones hay
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS inspecciones FROM calidad.inspecciones"
```

**Resultado esperado** (cambian los números; la primera unión sale **mayor** que el número de inspecciones):

```text
 filas
   633
```

```text
 filas
   454
```

```text
 inspecciones
          454
```

**Cómo se lee:** uniendo solo por `pieza_id`, cada inspección de una `P0003` se ha juntado con **todas** las `P0003` del histórico, de todas las tandas. Hay más filas que carcasas: el dataset tendría piezas con las señales de otra. Uniendo por **identificador + hora**, cada inspección se junta con su carcasa y sale una fila por pieza. Es la clave que encontraste en el M01-01.

### 4 — Construir el dataset

**Qué ocurre:** cuando hayan pasado al menos 5 minutos, construyes el dataset: une las dos fuentes por identificador + hora, cuenta lo que no se ha podido unir y guarda el resultado en `data/dataset_linea.csv`.

```bash
docker compose --profile lab run --rm --no-deps lab m02-04
```

📋 Ficha del comando [`m02-04`](../comandos-lab.md#m02-04): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (cambian los números):

```text
calidad inspecciona desde 2026-11-05T15:36:43+00:00
registros en el histórico desde entonces=454  inspecciones de calidad=454
unión por pieza_id=633 filas   unión por pieza_id + hora=454 filas
registros sin inspección=0  inspecciones sin registro=0
defectuosas=63 de 454 (14%)
OK m02-04: dataset_linea.csv con 454 piezas y 63 defectuosas
```

**Cómo se lee:**

| Línea | Qué dice |
|-------|----------|
| `calidad inspecciona desde` | Solo cuenta lo fabricado desde que calidad empezó; lo anterior no tiene resultado |
| `unión por pieza_id` frente a `pieza_id + hora` | La trampa del paso 3, comprobada |
| `registros sin inspección` | Carcasas con señales y sin resultado: no sirven para entrenar |
| `inspecciones sin registro` | Carcasas con resultado y sin señales: se perdieron en el histórico (el reto lo provoca) |
| `defectuosas=63 de 454` | El **balance de clases**: cuántos ejemplos de defecto tendrá el modelo para aprender |

Si sale `FALLO: solo … piezas`, deja la línea fabricando unos minutos más y repite.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>, función <code>cmd_m02_04</code>)</summary>

```python
con = sqlite3.connect("file:/data/historial.sqlite?mode=ro", uri=True)
con.execute("ATTACH DATABASE 'file:/data/calidad.sqlite?mode=ro' AS calidad")   # las dos bases juntas

df = pd.read_sql_query("""
    SELECT l.pieza_id, l.ts, l.temperatura_c, l.vibracion_mm_s, l.corriente_a, c.defecto
    FROM lecturas l
    JOIN calidad.inspecciones c ON l.pieza_id = c.pieza_id AND l.ts = c.ts_pieza   -- pieza + hora
    ORDER BY l.ts
""", con)
df.to_csv("/data/dataset_linea.csv", index=False)
```

</details>

## Comprueba tu entendimiento

**Qué no está en el dataset**

¿Por qué el dataset no tiene la columna `presion_bar`, que sí estaba en el M02-03?

→ Porque la estación no publica la presión en vivo. Un dataset solo puede tener lo que la línea mide y guarda de verdad.

## Investiga: descubre el criterio de calidad

**Qué ocurre:** calidad no dice por qué una carcasa sale mala. Vas a buscarlo tú con los datos, mirando cómo cambia la tasa de defectos con cada señal.

```bash
# Tasa de defectos según la vibración
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT l.vibracion_mm_s, COUNT(*) AS piezas, ROUND(AVG(c.defecto), 2) AS tasa_defecto
   FROM lecturas l JOIN calidad.inspecciones c ON l.pieza_id = c.pieza_id AND l.ts = c.ts_pieza
   GROUP BY l.vibracion_mm_s ORDER BY l.vibracion_mm_s"
```

**Resultado esperado:**

```text
 vibracion_mm_s  piezas  tasa_defecto
          0.220      93          0.04
          0.235      95          0.04
          0.250      95          0.03
          0.265      94          0.30
          0.280      94          0.28
```

Con vibración de 0,265 o más, la tasa de defecto sube del 3–4 % al 30 %. Pero no todas esas carcasas salen malas: algo más influye. Prueba a cruzar vibración y corriente:

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT l.corriente_a > 4.08 AS corriente_alta, l.vibracion_mm_s >= 0.265 AS vibracion_alta,
          COUNT(*) AS piezas, ROUND(AVG(c.defecto), 2) AS tasa_defecto
   FROM lecturas l JOIN calidad.inspecciones c ON l.pieza_id = c.pieza_id AND l.ts = c.ts_pieza
   GROUP BY 1, 2"
```

**Resultado esperado:**

```text
 corriente_alta  vibracion_alta  piezas  tasa_defecto
              0               0     212          0.05
              0               1     135          0.01
              1               0      73          0.03
              1               1      53          1.00
```

**Cómo se lee:** cuando la vibración **y** la corriente son altas a la vez, prácticamente todas las carcasas salen malas. En el resto, entre el 1 y el 5 %: ese es el error de la propia inspección. Acabas de descubrir el criterio oculto, y has visto por qué una regla sobre una sola señal (como el margen de temperatura del M01-02) no lo habría detectado.

## Reto

### 1 — Carcasas sin señales

Para el archivador un minuto, con calidad en marcha, vuelve a arrancarlo y repite `m02-04`. ¿Qué cambia?

```bash
docker compose stop archivador
sleep 60
docker compose start archivador
docker compose --profile lab run --rm --no-deps lab m02-04
```

<details>
<summary>Ver solución</summary>

Aparecen unas 60 **inspecciones sin registro**: calidad inspeccionó esas carcasas, pero el histórico no guardó sus señales. Tienen resultado y no tienen señales, así que no entran en el dataset. Es la pérdida del M01-01, vista ahora desde lo que le cuesta al modelo: menos ejemplos para aprender, y si los defectos se concentraran en ese tramo, un dataset sesgado.

</details>

### 2 — El error de la inspección

Si el 3 % de las inspecciones se equivocan, ¿podrá un modelo acertar el 100 %?

<details>
<summary>Ver solución</summary>

No contra estas etiquetas. Si la etiqueta está mal, un modelo que acierta de verdad «falla» según el dataset. Ese error de etiquetado pone un techo al acierto medible. En planta, mejorar la inspección (o revisar las etiquetas dudosas) suele aportar más que cambiar de modelo.

</details>

## Mejora: encontrar las inspecciones dudosas

**Qué ocurre:** ya conoces el criterio de calidad (vibración ≥ 0,265 **y** corriente > 4,08). Lo usas para revisar el propio dataset: las piezas en las que calidad dijo una cosa y el criterio otra son **etiquetas dudosas**, candidatas a que la inspección se equivocara. `lab sql` puede consultar también `dataset_linea.csv` como tabla.

```bash
# Cuántas piezas discrepan del criterio
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT COUNT(*) AS piezas,
          SUM((vibracion_mm_s >= 0.265 AND corriente_a > 4.08) <> defecto) AS discrepan
   FROM dataset_linea"

# Cuáles son
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT pieza_id, ts, vibracion_mm_s, corriente_a, defecto AS dijo_calidad,
          (vibracion_mm_s >= 0.265 AND corriente_a > 4.08) AS dice_el_criterio
   FROM dataset_linea WHERE (vibracion_mm_s >= 0.265 AND corriente_a > 4.08) <> defecto LIMIT 5"
```

**Resultado esperado** (cambian las piezas y los números):

```text
 piezas  discrepan
    426         21
```

```text
pieza_id                        ts  vibracion_mm_s  corriente_a  dijo_calidad  dice_el_criterio
   P0010 2026-11-06T02:04:21+00:00           0.220         4.11             1                 0
   P0016 2026-11-06T02:04:28+00:00           0.235         4.03             1                 0
   P0054 2026-11-06T02:05:05+00:00           0.280         4.10             0                 1
...
```

**Cómo se lee:** alrededor de un 5 % de las piezas discrepan. Son, casi seguro, el error de la inspección: carcasas con vibración normal marcadas como malas, o al revés. En planta, esta lista es oro: se mandan esas piezas a una **segunda revisión** y se corrigen sus etiquetas antes de entrenar. Un modelo entrenado con etiquetas revisadas aprende el proceso, no los errores de la inspección.

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no hay inspecciones` | El contenedor `calidad` no está en marcha | `docker compose up -d calidad` |
| `FALLO: solo … piezas con señales y resultado` | Ha fabricado poco tiempo con calidad en marcha | Espera unos minutos más y repite |
| `no such table: calidad.inspecciones` en `lab sql` | Calidad todavía no ha creado su base | Arranca `calidad` y espera unos segundos |
| La unión por `pieza_id` da lo mismo que por pieza + hora | No hay identificadores repetidos desde que calidad arrancó | Reinicia la estación (`docker compose restart sensor`) y espera un minuto |

## Conclusiones

### Qué es construir un dataset de producción

Es juntar, para cada pieza, **cómo se fabricó** (las señales del histórico) y **cómo salió** (el resultado de calidad). Vienen de sistemas distintos, con bases distintas, y nadie los ha unido antes por ti.

### Cómo debe ser

| Requisito | En el lab |
|-----------|-----------|
| Una fila por pieza | Unión por identificador + hora: 454 filas para 454 inspecciones |
| Solo lo que se mide de verdad | Sin presión, porque la línea no la publica |
| Lo que se queda fuera, contado | Registros sin inspección e inspecciones sin registro |
| Las clases, a la vista | 63 defectuosas de 454 |

### Dónde se rompe y cómo lo has detectado

| Problema | Cómo lo has visto | Qué provocaría en el modelo |
|----------|-------------------|-----------------------------|
| Identificador repetido | Unión por `pieza_id`: 633 filas para 454 piezas | Aprende con señales de una pieza y el resultado de otra |
| Pérdida en el histórico | Reto 1: inspecciones sin registro | Menos ejemplos, y un dataset sesgado si la pérdida no es al azar |
| Etiquetas con error | Tasa de 1–5 % en las carcasas que deberían ser buenas | Un techo al acierto y un modelo que aprende parte del error |
| Clase pequeña | Solo un 14 % de defectuosas | Pocos ejemplos de lo que más importa detectar |

### Cómo se perfecciona

- **Una clave de pieza común** a los dos sistemas desde el origen (MES, DataMatrix), para no depender de la hora.
- **Conciliar** el histórico y calidad antes de entrenar, como en el M01-01.
- **Revisar las etiquetas dudosas** (lo has hecho: un 5 % discrepa del criterio) y medir el error de la inspección.
- **Recoger más tiempo** para tener suficientes ejemplos de defecto, o recoger de forma dirigida cuando aparezcan.

### En una frase

> 🔑 Un dataset no se descarga: se construye uniendo cómo se fabricó cada pieza con cómo salió. Si la unión falla, el modelo aprende de piezas que no existen.
