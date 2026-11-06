# M04-02 — Detección automática de defectos

[← Página anterior](M04-01-clasificacion-componentes.md) · [Siguiente página →](M04-03-inspeccion-camara.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **detección y localización de defectos**: en qué se diferencia de clasificar, cómo debe comprobarse un detector, cuáles son los límites de una regla sencilla y cuándo hace falta algo más.

### Prerrequisitos

- Las imágenes de M04-01.
- CPU. No hay red neuronal de detección.

### Qué está pasando

Saber que una carcasa está mala no basta. El operario de **retrabajo** necesita saber **dónde** está el rayón para repararlo o para decidir si la pieza se puede salvar.

En estas fotos el rayón es una línea horizontal más clara que el resto. Para encontrarlo, se calcula el brillo medio de cada fila de la foto y se elige la más clara. El laboratorio sabe en qué fila está de verdad cada rayón, así que puede medir si acertó.

También hay que comprobar lo contrario: en una carcasa buena no debe aparecer ninguna fila tan brillante. No hay red neuronal: es una regla sencilla, y por eso tiene límites que verás en el reto.

### 1 — Medir la zona

Vas a buscar en 5 piezas defectuosas la fila donde está el rayón y comprobar en 3 buenas que no se marca nada. Calidad necesita saber dónde mirar; una clase sola no lo dice.

```bash
# Localiza el rayón en 5 malas y revisa 3 buenas
docker compose --profile lab run --rm --no-deps lab m04-02
```

📋 Ficha del comando [`m04-02`](../comandos-lab.md#m04-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
brillo=230.0 errores_zona=0 falsos_en_buenas=0 de 3
OK m04-02: zona correcta en 5 defectos; buenas sin marca=0
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
def _fila_brillante(ruta):
    img = np.asarray(Image.open(ruta).convert("L"), dtype=np.float32)
    return int(img.mean(axis=1).argmax())     # brillo medio de cada fila → la más clara

# Acierta si cae a 2 filas o menos de la fila real del manifiesto
if abs(_fila_brillante(ruta) - fila_real) > 2:
    errores += 1

# En una buena, ninguna fila llega a un brillo medio de 230 (de 255)
if img.mean(axis=1).max() > 230:
    falsos += 1
```

</details>

## Comprueba tu entendimiento

**Dónde está el rayón**

Abre `infra/data/imagenes/defectuosas/ko_00.png` y busca la línea clara.

→ Es la fila más brillante de toda la imagen. El borde de la pieza es un contorno, no una fila clara entera.

## Experimenta: bajar el umbral de brillo

**Qué ocurre:** para decir que una pieza buena «no tiene rayón», la regla comprueba que ninguna fila llegue a un brillo medio de 230 (de 255). Vas a bajar ese [umbral](../glosario/03-aprendizaje-automatico.md#umbral) a 180, como si quisieras «pillar más» defectos.

```bash
docker compose --profile lab run --rm --no-deps lab m04-02 brillo=180
```

**Resultado esperado:**

```text
brillo=180.0 errores_zona=0 falsos_en_buenas=1 de 3
OK m04-02: zona correcta en 5 defectos; buenas sin marca=1
```

**Cómo se lee:** con 180, **una de las tres piezas buenas** ya tiene una fila «sospechosa»: una fila que es todo fondo, y en esa foto el fondo es algo más claro (entre 170 y 185). La regla empieza a inventarse defectos. Bajar un umbral para no perder nada se paga en [falsas alarmas](../glosario/03-aprendizaje-automatico.md#matriz-confusion), igual que en el M03-01.

## Constrúyelo tú: tu propio localizador de rayones

**Qué está pasando:** `lab m04-02` localiza el rayón con una regla sencilla: la fila más clara de la foto. Ahora escribes tú esa regla, punto a punto: calculas el brillo de cada fila, buscas la más clara, compruebas contra las fotos en las que se sabe dónde está el rayón y decides cuándo una fila es «demasiado clara». Al final la pones a prueba con una pieza buena fotografiada con más luz, que es donde una regla fija suele fallar.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** asegurarte de que tu código tiene las fotos y sabe dónde está cada rayón.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m04_02_mi_detector_rayones.py`](../../infra/construye/m04_02_mi_detector_rayones.py). El paso 1 ya está escrito: lee el manifiesto, separa buenas y malas, y abre la primera foto defectuosa a tamaño completo, 64 × 64, con brillos de 0 a 255. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m04_02_mi_detector_rayones.py
```

**Resultado esperado:**

```text
foto defectuosa: 64 filas × 64 columnas; el rayón está en la fila 18
```

**Cómo se lee:** el manifiesto dice en qué fila está de verdad cada rayón (`y`): es lo que permite comprobar si tu regla acierta. Aquí no se reduce la foto como en el M04-01: para localizar hay que ver cada fila. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — El brillo de cada fila

**Para qué:** convertir la foto en una sola lista de números que diga dónde hay algo claro.

**Qué ocurre:** calculas el brillo medio de cada una de las 64 filas y enseñas las tres más claras.

Pega debajo de `# --- PASO 2`:

```python
brillo_filas = foto.mean(axis=1)                    # una media por fila: 64 números
mas_claras = np.argsort(brillo_filas)[::-1][:3]      # las tres filas con más brillo
for fila in mas_claras:
    print(f"fila {fila:2d}: brillo medio {brillo_filas[fila]:.0f}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas):

```text
fila 18: brillo medio 232
fila 19: brillo medio 232
fila 63: brillo medio 174
```

**Cómo se lee:** las filas 18 y 19 destacan muy por encima del resto (232 frente a 174 de la siguiente): el rayón tiene 2 puntos de grosor y está justo donde dice el manifiesto. Para la regla, la foto se ha reducido a esto: un perfil de brillo de arriba abajo.

### 3 — Localizar el rayón y comprobarlo

**Para qué:** saber si la fila más clara cae de verdad sobre el rayón, en todas las fotos defectuosas.

**Qué ocurre:** para cada foto defectuosa, buscas la fila más clara y la comparas con la fila real del manifiesto. Cuentas como acierto si está a 2 filas o menos.

Pega debajo de `# --- PASO 3`:

```python
def fila_mas_clara(numeros):
    return int(numeros.mean(axis=1).argmax())

aciertos = sum(abs(fila_mas_clara(a_numeros(r)) - int(y)) <= 2 for r, y in zip(malas["ruta"], malas["y"]))
print(f"rayón localizado en {aciertos} de {len(malas)} fotos defectuosas")
```

**Resultado esperado** (líneas nuevas):

```text
rayón localizado en 40 de 40 fotos defectuosas
```

**Cómo se lee:** las 40: la regla encuentra el rayón en todas. Funciona porque en estas fotos el rayón siempre es una línea **horizontal y más clara** que el resto. Es la información que necesita el operario de retrabajo: dónde está, no solo que existe.

### 4 — Decidir si hay rayón

**Para qué:** que la regla también diga «no hay rayón» en una pieza buena.

**Qué ocurre:** en una pieza buena, la fila más clara existe igual, pero no es un rayón. Decides que hay rayón solo si esa fila pasa de `BRILLO_RAYON`, y lo compruebas con todas las fotos, buenas y malas.

Pega debajo de `# --- PASO 4`:

```python
def hay_rayon(numeros):
    return numeros.mean(axis=1).max() > BRILLO_RAYON

marca_malas = sum(hay_rayon(a_numeros(r)) for r in malas["ruta"])
marca_buenas = sum(hay_rayon(a_numeros(r)) for r in buenas["ruta"])
print(f"con brillo > {BRILLO_RAYON}: malas marcadas={marca_malas} de {len(malas)}  buenas marcadas={marca_buenas} de {len(buenas)}")
```

**Resultado esperado** (líneas nuevas):

```text
con brillo > 230: malas marcadas=40 de 40  buenas marcadas=0 de 40
```

**Cómo se lee:** todas las malas marcadas y ninguna buena: con estas fotos, 230 separa bien las filas de rayón de las filas normales. La regla tiene ahora dos partes: **dónde** (la fila más clara) y **si hay** (si esa fila pasa del umbral).

### 5 — Decide tú: una pieza buena con más luz

**Para qué:** poner la regla a prueba en la situación más habitual en planta: la iluminación cambia.

**Qué ocurre:** añades al final este bloque, que aclara una foto buena en `MAS_LUZ` puntos, y pruebas `MAS_LUZ = 40` y después `MAS_LUZ = 90`.

```python
# Una pieza buena, fotografiada con más luz
clara = np.clip(a_numeros(buenas["ruta"].iloc[0]) + MAS_LUZ, 0, 255)
print(f"pieza buena con +{MAS_LUZ} de luz: fila más clara con brillo {clara.mean(axis=1).max():.0f} -> rayón={hay_rayon(clara)}")
```

**Resultado esperado** (con 40 y con 90):

```text
pieza buena con +40 de luz: fila más clara con brillo 224 -> rayón=False
pieza buena con +90 de luz: fila más clara con brillo 255 -> rayón=True
```

**Cómo se lee:** con 40 puntos más de luz, la pieza buena sigue pasando (224, por debajo de 230). Con 90, **la regla marca un rayón que no existe**: el fondo, la parte más clara de una foto buena, sube por encima del umbral fijo. Basta con 60 para que pase. Una regla de brillo absoluto depende de que la luz no cambie, y en una línea cambia (lámparas que envejecen, luz del día). La alternativa es comparar cada fila con **las demás de la misma foto**, no con un número fijo. Vuelve a dejar `MAS_LUZ = 0` y quita el bloque.
## Reto

### 1 — Un rayón que la regla no ve

**La situación:** el proveedor cambia la orientación de la carcasa en la bandeja y los rayones, que siguen siendo líneas claras, ahora salen **verticales** en la foto.

**Qué haces:** en tu script de «Constrúyelo tú», añades al final un bloque que gira 90° las fotos defectuosas (así los rayones quedan verticales) y les aplica `hay_rayon`. Después escribes una versión de la regla que mire filas **y** columnas, y la compruebas con las verticales, las horizontales y las buenas.

**Pistas:** `np.rot90(numeros)` gira la foto; `numeros.mean(axis=0)` da el brillo medio de cada **columna**, igual que `axis=1` lo da de cada fila.

**Lo que buscas:** cuántos rayones verticales ve la regla original, y una regla que vea los dos tipos sin marcar ninguna buena.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: los mismos rayones, pero verticales (la foto girada 90°)
verticales = [np.rot90(a_numeros(r)) for r in malas["ruta"]]
print(f"rayones verticales marcados por la regla de filas: {sum(hay_rayon(v) for v in verticales)} de {len(verticales)}")

def hay_rayon_2(numeros):
    return max(numeros.mean(axis=1).max(), numeros.mean(axis=0).max()) > BRILLO_RAYON   # filas o columnas

print(f"con filas y columnas: verticales={sum(hay_rayon_2(v) for v in verticales)} de {len(verticales)}  "
      f"horizontales={sum(hay_rayon_2(a_numeros(r)) for r in malas['ruta'])} de {len(malas)}  "
      f"buenas={sum(hay_rayon_2(a_numeros(r)) for r in buenas['ruta'])} de {len(buenas)}")
```

```text
rayones verticales marcados por la regla de filas: 0 de 40
con filas y columnas: verticales=40 de 40  horizontales=40 de 40  buenas=0 de 40
```

**La regla original no ve ninguno**: busca filas claras y un rayón vertical reparte su brillo entre todas las filas. Mirando también las columnas, los ve todos. Pero sigue sin ver un rayón diagonal, uno oscuro o una abolladura. **La regla:** una regla sencilla solo ve el defecto para el que se escribió; cada nuevo tipo de defecto pide otra regla. Cuando los defectos varían mucho, compensa un modelo que aprenda de ejemplos, como el del M04-01 o la red del M04-04.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la zona no cae sobre el rayón` | el manifiesto no es el de estas imágenes | borra `data/imagenes` y repite `m04-01` |
| falsos en buenas | se bajó el umbral de brillo | el comando usa 230; no lo bajes para «pillar más» |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/imagenes/manifiesto.csv` | no has generado las fotos | lanza `lab m04-01` |

## Conclusiones

### Qué es detectar un defecto

Clasificar responde «¿está mala?». Detectar responde «**¿dónde?**». Es lo que necesita retrabajo para reparar la pieza o decidir si se puede salvar.

### Cómo debe comprobarse un detector

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Encuentra el defecto donde está | En las 5 defectuosas, la fila encontrada cae a 2 filas o menos de la real |
| No inventa defectos | En las 3 buenas, ninguna fila llega al brillo del rayón |
| Se mide contra la verdad | El manifiesto guarda la fila real de cada rayón |

### Los límites de una regla sencilla

La regla del lab busca la fila más brillante. Funciona porque aquí el defecto es siempre una línea clara y horizontal. No vería:

- un defecto **oscuro** (una mancha, una falta de material);
- un rayón **vertical** o en diagonal;
- un defecto que **no cambia el brillo** de una fila entera.

### Cuándo hace falta algo más

- Cuando hay **varios tipos de defecto** o cambian de forma y posición: modelos de detección que aprenden de ejemplos marcados con su recuadro.
- Siempre conviene empezar por la regla más simple que resuelva el caso, y **escribir sus límites**, para saber cuándo deja de servir.

### En una frase

> 🔑 Antes de usar una red neuronal, comprueba si una regla simple resuelve el caso, y deja escrito qué defectos no vería.
