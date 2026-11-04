# M08-02 — Gobierno y trazabilidad

[← Página anterior](M08-01-evaluacion-riesgos.md) · [Siguiente página →](../../README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Reconstruyes la entrada, el dictamen y la versión de una pieza, y compruebas que cambiar el fichero `VERSION` no reescribe el pasado.

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
{"pieza_id": "AUD0007", "version": "defecto-0.1", "entrada": {"pieza_id": "AUD0007", "temperatura_c": 63.19, "vibracion_mm_s": 0.246, "corriente_a": 3.88, "presion_bar": 6.1}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}
{"pieza_id": "AUD0008", "version": "defecto-0.1", "entrada": {"pieza_id": "AUD0008", "temperatura_c": 63.19, "vibracion_mm_s": 0.246, "corriente_a": 3.88, "presion_bar": 6.1}, "dictamen": "seguir", "probabilidad": 0.0798, "ts": "…"}
defecto-0.1
```

De cada pieza sabes qué entró, qué se decidió, con qué versión y cuándo.

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

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no hay rastro de las dos piezas` | `api` no está guardando | `docker compose logs api` y repite M07-01 |
| `FALLO: el rastro cambió de versión` | `api` se reinició entre las dos llamadas | deja `api` en marcha y repite |
