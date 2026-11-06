# M08-02 — Gobierno y trazabilidad

[← Página anterior](M08-01-evaluacion-riesgos.md) · [Siguiente página →](../../README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es el **[gobierno](../glosario/05-operacion-gobierno.md#gobierno) y la [trazabilidad](../glosario/05-operacion-gobierno.md#trazabilidad)** de un modelo: qué hay que poder reconstruir de cada decisión, cómo debe ser un registro fiable, cómo se comprueba que no se puede alterar y cómo se clasifica el uso del sistema.

### Prerrequisitos

- `api` en marcha (M07-01), arrancada después de existir `VERSION`.
- No reinicies `api` durante el paso.

### Qué está pasando

Llega una **reclamación del cliente** por una carcasa. La pregunta es: ¿por qué se aceptó esa pieza? Para contestar hay que poder reconstruir **qué entró** al modelo, **qué dictaminó**, **con qué versión** y **cuándo**.

Además, el registro tiene que ser fiable aunque alguien toque los ficheros. En este lab se dictaminan dos piezas, AUD0007 y AUD0008, y entre medias se cambia el fichero de versión en disco a `defecto-0.2` sin reiniciar el servicio. El rastro de las dos piezas tiene que seguir diciendo la versión que de verdad contestó.

Por último, el uso queda clasificado: el sistema **asiste**, recomendando seguir o revisar; no decide por sí solo ni toca el paro. Es lo que se documenta al evaluar el uso frente al Reglamento europeo de IA.

### 1 — Reconstruir y no reescribir la historia

Vas a dictaminar dos piezas, cambiar el fichero de versión entre medias y leer el rastro. Una auditoría que cambia cuando alguien sustituye un fichero no sirve.

```bash
docker compose --profile lab run --rm --no-deps lab m08-02
```

📋 Ficha del comando [`m08-02`](../comandos-lab.md#m08-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
[{"pieza_id": "AUD0007", "version": "defecto-0.1", "entrada": {…}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}, {"pieza_id": "AUD0008", "version": "defecto-0.1", …}]
asistencia: el dictamen recomienda seguir o revisar; no escribe el paro
OK m08-02: rastro de AUD0007 con version=defecto-0.1 aunque el fichero cambió
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
primera = httpx.post(f"{API_URL}/predecir", json=cuerpo_AUD0007).json()
(DATA / "VERSION").write_text("defecto-0.2\n")          # alguien cambia el fichero
segunda = httpx.post(f"{API_URL}/predecir", json=cuerpo_AUD0008).json()

# Las dos líneas del registro siguen con la versión con la que arrancó el servicio
suyas = [l for l in predicciones if l["pieza_id"] in {"AUD0007", "AUD0008"}]
assert all(l["version"] == "defecto-0.1" for l in suyas)

(DATA / "VERSION").write_text("defecto-0.1\n")          # se deja como estaba
```

</details>

### 2 — Leer el rastro tú

Vas a buscar las dos piezas en el registro de predicciones, como lo haría un auditor.

```bash
grep AUD000 data/predicciones.jsonl
cat data/VERSION
```

**Resultado esperado:**

```text
{"pieza_id": "AUD0007", "version": "defecto-0.1", "huella_modelo": "69a897cdf955", "entrada": {"pieza_id": "AUD0007", "temperatura_c": 63.19, "vibracion_mm_s": 0.246, "corriente_a": 3.88, "presion_bar": 6.1}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "2026-11-06T03:06:36+00:00"}
{"pieza_id": "AUD0008", "version": "defecto-0.1", "huella_modelo": "69a897cdf955", "entrada": {"pieza_id": "AUD0008", "temperatura_c": 63.19, "vibracion_mm_s": 0.246, "corriente_a": 3.88, "presion_bar": 6.1}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "2026-11-06T03:06:36+00:00"}
defecto-0.1
```

De cada pieza sabes qué entró, qué se decidió, con qué versión, con qué modelo exacto (la [huella](../glosario/05-operacion-gobierno.md#version-huella)) y cuándo. Si has repetido el comando, verás también las líneas de ejecuciones anteriores: el registro no se borra.

## Comprueba tu entendimiento

**Otra versión**

¿Alguna línea de AUD0007 o AUD0008 dice `defecto-0.2`?

→ No. El fichero cambió, pero el servicio que respondió seguía siendo el `defecto-0.1`.

## Mejora: verificar el modelo del rastro

**Qué ocurre:** un auditor no se fía de la etiqueta de versión (M07-01). Comprueba que la huella que aparece en el rastro es la del modelo que hay en disco.

```bash
# La huella del rastro de AUD0007 (la última vez que se dictaminó)
grep AUD0007 data/predicciones.jsonl | tail -1 | grep -o '"huella_modelo": "[^"]*"'

# La huella del fichero del modelo en disco
sha256sum data/modelo_defecto.joblib | cut -c1-12
```

**Resultado esperado:**

```text
"huella_modelo": "69a897cdf955"
69a897cdf955
```

**Cómo se lee:** coinciden: la pieza la dictaminó el modelo que está hoy en disco. Si mañana se entrena y se despliega otro, las piezas nuevas tendrán otra huella y las antiguas conservarán la suya. Así, ante una reclamación de una pieza de hace tres meses, se sabe qué modelo exacto la dictaminó, aunque ese fichero ya no esté en producción. En una plataforma real se guardan **todos** los modelos desplegados con su huella, para poder reproducir cualquier decisión.

## Constrúyelo tú: tu propia auditoría del rastro

**Qué está pasando:** el servicio de [inferencia](../glosario/05-operacion-gobierno.md#inferencia) deja una línea en `predicciones.jsonl` por cada [dictamen](../glosario/05-operacion-gobierno.md#dictamen). En este lab has visto que el rastro no se reescribe al cambiar la versión. Ahora haces tú la auditoría que haría calidad o un auditor externo: resumes el rastro por modelo, compruebas que cada dictamen se hizo con el modelo instalado, buscas líneas incompletas y, al final, **sellas** el rastro para que cualquier cambio posterior se note.

**Cómo se trabaja en cada paso:**

1. Lees para qué es el paso y qué hace el bloque.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Para qué:** tener delante todo lo que el servicio ha dictaminado, con fecha.

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m08_02_mi_auditoria.py`](../../infra/construye/m08_02_mi_auditoria.py). El paso 1 ya está escrito: lee `predicciones.jsonl` línea a línea. Ábrelo también tal cual en VS Code (`infra/data/predicciones.jsonl`) para ver qué trae cada línea. Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m08_02_mi_auditoria.py
```

**Resultado esperado** (cambian los números: depende de cuántas veces hayas llamado a la [API](../glosario/05-operacion-gobierno.md#api)):

```text
dictámenes en el rastro: 3  primero: 2026-11-06T03:26:13+00:00  último: 2026-11-06T03:27:26+00:00
```

**Cómo se lee:** cada línea es un dictamen: qué pieza, qué entrada, qué decisión, cuándo, con qué versión y con qué huella. Todas las llamadas a la API que has hecho en el curso están aquí. `--entrypoint python` hace que el contenedor `lab` ejecute **tu fichero**.

### 2 — Resumir por modelo

**Para qué:** saber con qué modelos se han tomado las decisiones.

**Qué ocurre:** cuentas cuántos dictámenes hay de cada combinación de versión y huella, y cuántos «revisar» hay en cada una.

Pega debajo de `# --- PASO 2`:

```python
por_modelo = Counter((d.get("version"), d.get("huella_modelo")) for d in rastro)
print("versión        huella        dictámenes  revisar")
for (version, huella), n in por_modelo.items():
    revisar = sum(1 for d in rastro if d.get("version") == version and d.get("huella_modelo") == huella and d["dictamen"] == "revisar")
    print(f"{str(version):14s} {str(huella):12s}  {n:10d}  {revisar:7d}")
```

Ejecuta de nuevo (el mismo comando del paso 1).

**Resultado esperado** (líneas nuevas; cambian los números):

```text
versión        huella        dictámenes  revisar
defecto-0.1    69a897cdf955           3        0
```

**Cómo se lee:** lo normal es una sola fila: todos los dictámenes con el mismo modelo. Fíjate en que el paso 1 del lab cambió el fichero `VERSION` a `defecto-0.2` y, aun así, el rastro dice `defecto-0.1`: el servicio registra la versión que cargó al arrancar, no la que diga el fichero después. Si reentrenaras el modelo y recrearas la API, aparecería una segunda fila con otra huella.

### 3 — Comprobar contra el modelo instalado

**Para qué:** saber si los dictámenes se tomaron con el modelo que está instalado ahora.

**Qué ocurre:** calculas la huella del fichero `modelo_defecto.joblib` y cuentas los dictámenes cuya huella no coincide.

Pega debajo de `# --- PASO 3`:

```python
huella_instalada = hashlib.sha256(open("/data/modelo_defecto.joblib", "rb").read()).hexdigest()[:12]
otros = [d for d in rastro if d.get("huella_modelo") != huella_instalada]
print(f"huella del modelo instalado: {huella_instalada}")
print(f"dictámenes tomados con otro modelo (o sin huella): {len(otros)} de {len(rastro)}")
```

**Resultado esperado** (líneas nuevas; cambian los números):

```text
huella del modelo instalado: 69a897cdf955
dictámenes tomados con otro modelo (o sin huella): 0 de 3
```

**Cómo se lee:** si salen 0, todo el rastro corresponde al modelo instalado. Si salen más, hubo otro modelo antes (por ejemplo, si reentrenaste en el M03-03 después de usar la API) o hay líneas sin huella. Eso no es un fallo en sí, pero un auditor querrá saber **qué modelo era** y si se conserva: sin el fichero de ese modelo, esos dictámenes no se pueden reproducir.

### 4 — Buscar líneas incompletas

**Para qué:** comprobar que cada dictamen tiene todo lo necesario para reconstruirlo.

**Qué ocurre:** compruebas que cada línea trae los campos sin los que no se puede reconstruir una decisión: pieza, hora, versión, huella, entrada y dictamen.

Pega debajo de `# --- PASO 4`:

```python
OBLIGATORIOS = ["pieza_id", "ts", "version", "huella_modelo", "entrada", "dictamen"]
incompletas = [(i, [c for c in OBLIGATORIOS if c not in d]) for i, d in enumerate(rastro) if any(c not in d for c in OBLIGATORIOS)]
print(f"líneas incompletas: {len(incompletas)}", incompletas[:3])
```

**Resultado esperado** (líneas nuevas):

```text
líneas incompletas: 0 []
```

**Cómo se lee:** ninguna, si el rastro solo lo ha escrito el servicio de la API, que siempre pone todos los campos. Es la diferencia con un dictamen publicado a mano en el [broker](../glosario/01-datos-arquitectura.md#broker) (M06-02): ese no deja ninguna línea aquí. La auditoría solo cubre lo que pasó por el servicio.

### 5 — Sellar el rastro

**Para qué:** que cualquier cambio posterior en el rastro, aunque sea de una letra, se pueda detectar.

**Qué ocurre:** calculas un **sello encadenado**: la huella de la primera línea, después la huella de ese resultado junto con la segunda, y así hasta el final. El último valor depende de todas las líneas y de su orden. Lo guardas en `sello_rastro.txt`.

Pega debajo de `# --- PASO 5`:

```python
def sellar(lineas):
    sello = ""
    for linea in lineas:
        sello = hashlib.sha256((sello + linea).encode()).hexdigest()   # cada sello depende del anterior
    return sello[:16]

sello = sellar(lineas)
open("/data/sello_rastro.txt", "w").write(f"{len(lineas)} {sello}\n")
print(f"sello de las {len(lineas)} líneas: {sello} (guardado en sello_rastro.txt)")
```

**Resultado esperado** (línea nueva; el sello cambia con tu rastro):

```text
sello de las 3 líneas: 474a377fc23bdbb8 (guardado en sello_rastro.txt)
```

**Cómo se lee:** un código de 16 caracteres que resume todo el rastro. Si mañana alguien cambia un «revisar» por un «seguir», borra una línea o las reordena, el sello que salga ya no será este. Guardado fuera del alcance de quien escribe el rastro (otro equipo, una copia firmada), permite demostrar que el rastro no se ha tocado.

### 6 — Decide tú: alguien cambia un dictamen

**Para qué:** comprobar que el sello detecta una manipulación que a simple vista no se nota.

**Qué ocurre:** añades al final este bloque, que hace una **copia** del rastro en memoria, cambia el dictamen de una línea y vuelve a sellar. El fichero de verdad no se toca.

```python
# Una copia manipulada: un «revisar» pasa a «seguir» (o al revés) en la línea del medio
copia = list(lineas)
i = len(copia) // 2
d = json.loads(copia[i])
d["dictamen"] = "seguir" if d["dictamen"] == "revisar" else "revisar"
copia[i] = json.dumps(d, ensure_ascii=False)
print(f"línea {i} cambiada a «{d['dictamen']}»: sello original={sello}  sello de la copia={sellar(copia)}")
```

**Resultado esperado** (la línea nueva):

```text
línea 1 cambiada a «revisar»: sello original=474a377fc23bdbb8  sello de la copia=1da1643e653e962d
```

**Cómo se lee:** **los dos sellos no se parecen en nada**, aunque solo ha cambiado una palabra de una línea entre muchas. Comparar el sello guardado con uno recalculado dice si el rastro se ha tocado; para saber **qué** línea, se guarda también el sello de cada línea. Es la base de un registro de auditoría fiable: no impide cambiarlo, pero hace imposible cambiarlo sin que se note. Quita el bloque cuando acabes.
## Reto

### 1 — Qué tipo de sistema es

**La situación:** para evaluar el uso frente al Reglamento europeo de IA hay que documentar qué hace el sistema con sus decisiones: ¿**decide** y actúa, o **asiste** a una persona? La frase del paso 1 del lab lo afirma; un auditor querrá verlo en los datos.

**Qué haces:** en tu auditoría de «Constrúyelo tú», añades al final un bloque que cuenta qué valores toma el campo `dictamen` en todo el rastro y qué campos tiene cada línea. Buscas alguno que indique una acción sobre la máquina (un paro, una [consigna](../glosario/05-operacion-gobierno.md#consigna), un rechazo de pieza).

**Pistas:** `Counter(d["dictamen"] for d in rastro)` cuenta los valores; `set().union(*(d.keys() for d in rastro))` junta todos los campos que aparecen.

**Lo que buscas:** pruebas, en el propio rastro, de si el sistema decide o asiste.

<details>
<summary>Ver solución</summary>

```python
# Reto 1: ¿qué hace el sistema con sus dictámenes?
print("valores de dictamen en el rastro:", dict(Counter(d["dictamen"] for d in rastro)))
campos = set().union(*(d.keys() for d in rastro))
print("campos del rastro:", sorted(campos))
```

```text
valores de dictamen en el rastro: {'seguir': 3}
campos del rastro: ['dictamen', 'entrada', 'huella_modelo', 'pieza_id', 'probabilidad', 'ts', 'version']
```

El dictamen solo puede ser **«seguir» o «revisar»** (en este rastro, todos «seguir»), y ningún campo registra una acción sobre la máquina: ni paro, ni consigna, ni rechazo. El sistema **recomienda** qué hacer con la carcasa; quien la desvía es el automatismo, con sus propias protecciones, y quien decide sobre ella es una persona. Es un sistema de **asistencia**, y ahora lo puedes demostrar con su propio rastro. **La regla:** la clasificación de un sistema de IA no se declara: se comprueba en lo que hace y en lo que deja escrito, y se vuelve a comprobar cada vez que cambia.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no hay rastro de las dos piezas` | `api` no está guardando | `docker compose logs api` y repite M07-01 |
| `FALLO: el rastro cambió de versión` | `api` se reinició entre las dos llamadas | deja `api` en marcha y repite |
| `NameError: name '…' is not defined` | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro de `for`, `if`, `while` y `def` |
| `ModuleNotFoundError` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| `FileNotFoundError: /data/predicciones.jsonl` | la API no ha dado ningún dictamen todavía | haz el M07-01, o lanza el paso 1 de este lab con la API en marcha |

## Conclusiones

### Qué es gobernar un modelo

Es poder responder, para cualquier pieza, a **por qué se tomó esa decisión**. Para eso, cada dictamen tiene que dejar rastro de cuatro cosas:

| Qué | Dónde está |
|-----|------------|
| Qué entró | `entrada`: las señales de la pieza |
| Qué se decidió | `dictamen` y `probabilidad` |
| Con qué modelo | `version` |
| Cuándo | `ts` |

### Cómo debe ser un registro fiable

| Requisito | En el lab |
|-----------|-----------|
| Lo escribe el servicio, no la aplicación | `predicciones.jsonl` lo llena `api` |
| La versión es la que de verdad contestó | La que se cargó al arrancar el servicio |
| No cambia si alguien toca un fichero | Con `VERSION` cambiado a `defecto-0.2`, AUD0007 y AUD0008 siguieron en `defecto-0.1` |

### Cómo se comprueba

Provocando el cambio y mirando el rastro: es lo que hace `m08-02`. Un auditor busca la pieza (`grep AUD0007 data/predicciones.jsonl`) y debe poder reconstruir la decisión sin preguntar a nadie.

### Cómo se clasifica el uso

El sistema del curso **asiste**: recomienda seguir o revisar, no rechaza piezas por sí solo y no toca el paro. Esa clasificación (quién decide, sobre qué, con qué supervisión) es la que se documenta al evaluar el uso frente al Reglamento europeo de IA.

### Todo empieza en el M01

Sin un identificador de pieza único y una hora desde el origen, aquí no habría nada que reconstruir. La trazabilidad no se añade al final: se diseña desde la primera pieza de la arquitectura.

### En una frase

> 🔑 Ante una reclamación, la pregunta es «¿por qué se aceptó esta pieza?». Si el registro no la responde, el modelo no está gobernado, por mucho que acierte.
