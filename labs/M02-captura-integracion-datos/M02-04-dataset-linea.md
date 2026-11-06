# M02-04 — Construir un dataset con datos de la línea

[← Página anterior](M02-03-preparacion-datos.md) · [Siguiente página →](../M03-ml-prediccion-anomalias/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender cómo se **construye un [dataset](../glosario/01-datos-arquitectura.md#dataset) para entrenar a partir de la producción real**: de dónde salen las señales y de dónde las [etiquetas](../glosario/03-aprendizaje-automatico.md#etiqueta), cómo deben unirse dos sistemas distintos, qué errores aparecen al unirlos y cómo se evitan.

### Prerrequisitos

- M01-01 hecho: mosquitto, sensor y archivador en marcha.
- En este lab se añade el contenedor `calidad`. Hay que dejar la línea fabricando **al menos 5 minutos** (mejor 10) con `calidad` en marcha.

### Qué está pasando

En el M02-03 trabajaste con un [histórico](../glosario/01-datos-arquitectura.md#historico) generado de golpe, con su columna `defecto` ya puesta. En una planta nadie te da eso: **hay que construirlo**. Las piezas de información vienen de dos sistemas distintos:

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

**La situación:** en «Investiga» descubriste el criterio de calidad: una carcasa sale mala cuando la vibración es de 0,265 mm/s o más **y** la corriente pasa de 4,08 A. Pero calidad no aplica una regla: inspecciona, y a veces se equivoca.

**Qué haces:** en tu script de «Constrúyelo tú», añades al final un bloque que aplica ese criterio a cada carcasa de tu dataset y cuenta en cuántas no coincide con lo que dijo calidad. Hazlo después del paso 5.

**Pistas:** `(dataset["vibracion_mm_s"] >= 0.265) & (dataset["corriente_a"] > 4.08)` da `True` o `False` por carcasa; `.astype(int)` lo convierte en 1 o 0, como la columna `defecto`; `(a != b).sum()` cuenta las diferencias.

**Lo que buscas:** el porcentaje de carcasas en las que calidad y el criterio no coinciden. ¿Podría un modelo acertar más que eso contra estas etiquetas?

<details>
<summary>Ver solución</summary>

```python
# Reto 2: el criterio descubierto en «Investiga», aplicado a cada carcasa
regla = ((dataset["vibracion_mm_s"] >= 0.265) & (dataset["corriente_a"] > 4.08)).astype(int)
desacuerdos = int((regla != dataset["defecto"]).sum())
print(f"la regla y calidad no coinciden en {desacuerdos} de {len(dataset)} carcasas ({desacuerdos / len(dataset):.1%})")
```

```text
la regla y calidad no coinciden en 66 de 2294 carcasas (2.9%)
```

**Un 2,9 %**: es el error de la inspección, que en esta línea es del 3 %. Ni siquiera el criterio exacto acierta el 100 % contra estas etiquetas, así que **ningún modelo podrá medir un acierto mayor del 97 %**, por bueno que sea. Si un modelo midiera un 100 %, estaría aprendiendo los errores de la inspección. Para subir ese techo hay que mejorar la inspección o revisar las etiquetas dudosas, que es lo que haces en «Mejora».

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

## Constrúyelo tú: tu propio dataset

**Qué está pasando:** `lab m02-04` une el histórico con la base de calidad y deja `dataset_linea.csv`. Ahora haces tú esa unión con pandas: lees las dos bases, las unes primero mal (solo por identificador) para ver el error con tus propios ojos, después bien (identificador y hora), y cuentas lo que no se ha podido unir. Al final tienes tu dataset y sabes de dónde sale cada una de sus filas.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que tu código lee las dos bases que vas a unir.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m02_04_mi_dataset.py`](../../infra/construye/m02_04_mi_dataset.py). El paso 1 ya está escrito: lee la tabla `lecturas` del histórico (las señales de cada carcasa) y la tabla `inspecciones` de calidad (el resultado de cada carcasa), las dos en solo lectura. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_04_mi_dataset.py
```

**Resultado esperado** (cambian los números):

```text
histórico: 2327 registros   calidad: 2418 inspecciones
```

**Cómo se lee:** dos sistemas distintos, cada uno con su base y sus números. El histórico tiene más registros porque empezó antes: calidad solo inspecciona desde que la arrancaste en el paso 1 del lab. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Unir solo por identificador

**Para qué:** ver qué pasa con la unión que parece obvia.

**Qué ocurre:** unes las dos tablas por `pieza_id`, como haría cualquiera la primera vez, y cuentas cuántas filas salen y cuántos identificadores tienen más de una inspección.

Pega debajo de `# --- PASO 2`:

```python
por_id = lecturas.merge(inspecciones, on="pieza_id")
inspecciones_por_id = inspecciones.groupby("pieza_id").size()
print(f"unión por pieza_id: {len(por_id)} filas")
print(f"identificadores con más de una inspección: {int((inspecciones_por_id > 1).sum())}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas; cambian los números):

```text
unión por pieza_id: 5508 filas
identificadores con más de una inspección: 986
```

**Cómo se lee:** salen **más filas que registros** tiene el histórico. Cada vez que la estación se ha reiniciado, ha vuelto a numerar desde `P0001`: un mismo identificador corresponde a varias carcasas, y la unión cruza cada una con todas las inspecciones de ese nombre.

### 3 — Ver una carcasa mal unida

**Para qué:** comprobar con un caso concreto que la unión por identificador mezcla carcasas distintas.

**Qué ocurre:** eliges un identificador que calidad ha marcado unas veces como buena y otras como defectuosa (fueron carcasas distintas con el mismo nombre) y enseñas las primeras filas de la unión.

Pega debajo de `# --- PASO 3`:

```python
# Un identificador que calidad ha marcado unas veces como buena y otras como defectuosa
resultados = inspecciones.groupby("pieza_id")["defecto"].nunique()
ejemplo = resultados[resultados > 1].index[0]
filas = por_id[por_id["pieza_id"] == ejemplo][["pieza_id", "ts", "ts_pieza", "defecto"]]
print(f"{ejemplo}: {len(filas)} filas en la unión; las primeras:")
print(filas.head(6).to_string(index=False))
```

**Resultado esperado** (líneas nuevas; cambian las horas):

```text
P0005: 15 filas en la unión; las primeras:
pieza_id                        ts                  ts_pieza  defecto
   P0005 2026-11-06T03:10:01+00:00 2026-11-06T03:28:07+00:00        1
   P0005 2026-11-06T03:10:01+00:00 2026-11-06T14:20:09+00:00        0
   P0005 2026-11-06T03:10:01+00:00 2026-11-06T14:22:47+00:00        1
   P0005 2026-11-06T03:11:16+00:00 2026-11-06T03:28:07+00:00        1
   P0005 2026-11-06T03:11:16+00:00 2026-11-06T14:20:09+00:00        0
   P0005 2026-11-06T03:11:16+00:00 2026-11-06T14:22:47+00:00        1
```

**Cómo se lee:** en cada fila, `ts` es la hora del registro y `ts_pieza` la de la carcasa que inspeccionó calidad. El registro de las 03:10:01 aparece **tres veces, con tres resultados: defectuosa, buena y defectuosa**, y ninguno es el suyo: las tres inspecciones son de otras carcasas que se llamaron P0005 después de un reinicio. Solo las filas en las que `ts` y `ts_pieza` coinciden son la misma carcasa. Un modelo que aprendiera de esta unión vería unas mismas señales dar a la vez buena y defectuosa.

### 4 — Unir por identificador y hora

**Para qué:** unir cada registro con su propia inspección y contar lo que no casa.

**Qué ocurre:** unes por `pieza_id` **y** por la hora (la `ts` del histórico con la `ts_pieza` de calidad). Después cuentas los registros sin inspección y las inspecciones sin registro, desde que calidad empezó.

Pega debajo de `# --- PASO 4`:

```python
bien = lecturas.merge(inspecciones, left_on=["pieza_id", "ts"], right_on=["pieza_id", "ts_pieza"])
desde = inspecciones["ts_pieza"].min()                    # calidad empezó a inspeccionar aquí
registros_desde = int((lecturas["ts"] >= desde).sum())
print(f"unión por pieza_id + hora: {len(bien)} filas")
print(f"registros sin inspección: {registros_desde - len(bien)}   inspecciones sin registro: {len(inspecciones) - len(bien)}")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
unión por pieza_id + hora: 2270 filas
registros sin inspección: 0   inspecciones sin registro: 148
```

**Cómo se lee:** ahora cada fila es una carcasa con sus señales y su resultado. Los dos recuentos de lo que no casa son la **huella de los fallos de la arquitectura**: los registros sin inspección son carcasas que calidad no vio; las inspecciones sin registro, carcasas cuyas señales no se guardaron. Aquí son 148 porque en este histórico se paró el archivador varias veces mientras calidad seguía inspeccionando, como en el reto 1.

### 5 — Guardar el dataset

**Para qué:** dejar una tabla lista para entrenar y comprobar que coincide con la del comando.

**Qué ocurre:** te quedas con las señales y la etiqueta, ordenas por hora, guardas `mi_dataset.csv` y lo comparas con el `dataset_linea.csv` que dejó `lab m02-04`.

Pega debajo de `# --- PASO 5`:

```python
dataset = bien[["pieza_id", "ts", "temperatura_c", "vibracion_mm_s", "corriente_a", "defecto"]].sort_values("ts")
dataset.to_csv("/data/mi_dataset.csv", index=False)
print(f"mi_dataset.csv: {len(dataset)} piezas, defectuosas={int(dataset['defecto'].sum())} ({dataset['defecto'].mean():.0%})")
del_comando = pd.read_csv("/data/dataset_linea.csv")
print(f"dataset_linea.csv del comando: {len(del_comando)} piezas (el tuyo tiene las carcasas fabricadas desde entonces)")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
mi_dataset.csv: 2270 piezas, defectuosas=281 (12%)
dataset_linea.csv del comando: 2269 piezas (el tuyo tiene las carcasas fabricadas desde entonces)
```

**Cómo se lee:** tu dataset es el del comando más las carcasas fabricadas desde que lo lanzaste: la línea no ha dejado de producir. Si lanzas `lab m02-04` y tu script uno detrás de otro, las cifras casi coinciden. La proporción de defectuosas es la que tendrá que aprender el modelo del M03-04.
## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no hay inspecciones` | El contenedor `calidad` no está en marcha | `docker compose up -d calidad` |
| `FALLO: solo … piezas con señales y resultado` | Ha fabricado poco tiempo con calidad en marcha | Espera unos minutos más y repite |
| `no such table: calidad.inspecciones` en `lab sql` | Calidad todavía no ha creado su base | Arranca `calidad` y espera unos segundos |
| La unión por `pieza_id` da lo mismo que por pieza + hora | No hay identificadores repetidos desde que calidad arrancó | Reinicia la estación (`docker compose restart sensor`) y espera un minuto |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `no such table: inspecciones` | calidad no ha arrancado todavía | `docker compose up -d calidad` y deja fabricar unos minutos |
| `FileNotFoundError: /data/dataset_linea.csv` en el paso 5 | no has lanzado `lab m02-04` | lanza el paso 4 del lab y vuelve a ejecutar |

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
