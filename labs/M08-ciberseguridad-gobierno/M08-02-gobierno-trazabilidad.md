# M08-02 — Gobierno y trazabilidad

[← Página anterior](M08-01-evaluacion-riesgos.md) · [Siguiente página →](../../README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es el **gobierno y la trazabilidad** de un modelo: qué hay que poder reconstruir de cada decisión, cómo debe ser un registro fiable, cómo se comprueba que no se puede alterar y cómo se clasifica el uso del sistema.

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

De cada pieza sabes qué entró, qué se decidió, con qué versión, con qué modelo exacto (la huella) y cuándo. Si has repetido el comando, verás también las líneas de ejecuciones anteriores: el registro no se borra.

## Comprueba tu entendimiento

**Otra versión**

¿Alguna línea de AUD0007 o AUD0008 dice `defecto-0.2`?

→ No. El fichero cambió, pero el servicio que respondió seguía siendo el `defecto-0.1`.

## Reto

### 1 — Qué tipo de sistema es

Lee la frase que imprime el comando antes del `OK`. ¿Es un sistema que decide o que asiste?

<details>
<summary>Ver solución</summary>

Asiste: recomienda seguir o revisar y no escribe el paro. No rechaza piezas por sí solo. Esa clasificación es la que se documenta cuando se evalúa el uso frente al Reglamento de IA.

</details>

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

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no hay rastro de las dos piezas` | `api` no está guardando | `docker compose logs api` y repite M07-01 |
| `FALLO: el rastro cambió de versión` | `api` se reinició entre las dos llamadas | deja `api` en marcha y repite |

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
