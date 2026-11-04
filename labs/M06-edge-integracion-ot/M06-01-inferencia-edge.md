# M06-01 — Inferencia en entornos edge

[← Página anterior](README.md) · [Siguiente página →](M06-02-integracion-ot.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Das un dictamen con el modelo cargado desde el disco del puesto y mides el tiempo por pieza.

### Prerrequisitos

- `data/modelo_defecto.joblib` de M03-03.
- Unos 0,4 GB. Este paso no usa el modelo generativo.

### Qué está pasando

El modelo de defecto del M03-03 tiene que dar su dictamen de cada carcasa **antes de que salga la siguiente**, y en EST-01 sale una por segundo. Además, la línea no puede depender de que funcione la red de la oficina o internet.

Por eso el modelo se ejecuta en el **equipo edge**, el ordenador que está junto a la máquina. En este laboratorio ese equipo es tu puesto: el modelo se carga desde un fichero del disco, sin ninguna dirección de red.

Se dictaminan 20 piezas seguidas y se mide la media. La primera no cuenta, porque incluye el tiempo de cargar el modelo y no se repite en cada pieza.

### 1 — Liberar memoria

Vas a parar el modelo generativo, que en este módulo no hace falta y es el que más memoria ocupa.

```bash
docker compose stop llm
```

### 2 — Medir en caliente

Vas a cargar el modelo de defecto desde el disco y medir cuántos milisegundos tarda en dictaminar una pieza. La latencia que importa es la de la pieza siguiente, no la del arranque.

```bash
docker compose --profile lab run --rm --no-deps lab m06-01
```

📋 Ficha del comando [`m06-01`](../comandos-lab.md#m06-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado** (el tiempo depende del puesto; tiene que quedar por debajo de 200 ms):

```text
ms_por_pieza=0.39 fichero=modelo_defecto.joblib
OK m06-01: 0.39 ms por pieza, modelo en disco
```

Menos de medio milisegundo frente a un ciclo de estación de 1 segundo: cabe de sobra.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
modelo = joblib.load(DATA / "modelo_defecto.joblib")    # del disco, sin red
fila = pd.read_csv(DATA / "limpio.csv").head(1)[FEATURES]
modelo.predict_proba(fila)                              # calentamiento: la primera no cuenta

t0 = time.perf_counter()
for _ in range(20):
    modelo.predict_proba(fila)
ms = (time.perf_counter() - t0) * 1000 / 20             # media por pieza
```

</details>

## Comprueba tu entendimiento

**Sin nube**

¿A qué dirección se conecta este paso para predecir?

→ A ninguna. Lee `modelo_defecto.joblib` del disco.

## Reto

### 1 — Pieza lenta

Si un dictamen tardara más que el ciclo de la estación, ¿se acepta la pieza sola?

<details>
<summary>Ver solución</summary>

No. Llegar tarde es no llegar: la pieza iría a revisión.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: falta el modelo; pasa antes por M03-03` | no terminó M03-03 | lanza `m03-03` |
| `FALLO: la inferencia local va demasiado lenta` | el puesto está saturado | `docker compose stop llm` y repite |
