# M07-02 — Monitorización y seguimiento operacional

[← Página anterior](M07-01-servicio-inferencia.md) · [Siguiente página →](../M08-ciberseguridad-gobierno/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comparas la tasa de avisos de un lote normal con la del mismo lote 8 °C más caliente.

### Prerrequisitos

- El mismo `data/modelo_defecto.joblib`.

### En qué consiste

Es la misma función que sirve `api`, aplicada a un lote para ver la deriva. Subir la temperatura imita un proceso que ya no es el del entrenamiento: cambio de utillaje, otra refrigeración, verano. Si la tasa de `revisar` no se mueve, no estás viendo la degradación.

### 1 — Medir la base y el desplazamiento

Vas a puntuar las piezas de evaluación tal cual (la base) y otra vez con 8 °C más. Sin una línea base, el número de después no dice nada.

```bash
docker compose --profile lab run --rm --no-deps lab m07-02
```

**Resultado esperado:**

```text
tasa_base=0.08 tasa_desplazada=0.96
OK m07-02: base=0.08 desplazada=0.96
```

Con el proceso normal, el 8 % de las piezas va a revisión. Con el proceso desplazado, el 96 %: el modelo sigue contestando, pero ya no describe esta línea.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
_, test = _partir(df)                                   # las piezas de evaluación de M03
base = _tasa_alerta(modelo, test)                       # % con probabilidad ≥ 0,5

movido = test.copy()
movido["temperatura_c"] = movido["temperatura_c"] + 8   # el proceso «se ha ido»
deriva = _tasa_alerta(modelo, movido)
```

</details>

### 2 — Guardar el seguimiento

Vas a leer el resumen que queda escrito para compararlo con la medida de mañana.

```bash
cat data/seguimiento.json
```

**Resultado esperado:**

```json
{"tasa_base": 0.08225108225108226, "tasa_desplazada": 0.9567099567099567}
```

## Comprueba tu entendimiento

**Dos fallos distintos**

Si `api` se cae a mitad de un lote, ¿hay que reentrenar?

→ No. Eso es una caída del servicio. La deriva es el servicio funcionando con datos que ya no se parecen a los del entrenamiento.

## Reto

### 1 — Volver a la base

Si la estación vuelve a su temperatura habitual, ¿qué tasa esperas?

<details>
<summary>Ver solución</summary>

La de la base, alrededor de 0,08. Si no vuelve, ya no estás puntuando el modelo que crees, o la línea cambió en algo más que la temperatura.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: no se ve la deriva al subir 8 °C` | el CSV no es el limpio de este curso | repite `m02-03` y `m03-03` |
| `No such file … modelo_defecto.joblib` | saltaste M03-03 | `m03-03` |
