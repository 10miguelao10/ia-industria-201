# M03-03 — Comparación de modelos predictivos

[← Página anterior](M03-02-anomalias.md) · [Siguiente página →](../M04-vision-control-calidad/README.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comparas una regresión logística y un árbol poco profundo sobre el mismo corte, y eliges uno con una regla escrita de antemano.

### Prerrequisitos

- El `limpio.csv` de M02-03.
- Deja `modelo_defecto.joblib` y `VERSION`. Es el modelo que usan M06, M07 y M08.

### Qué está pasando

Ingeniería tiene **dos modelos candidatos** para poner en la línea: la regresión logística del M03-01 y un árbol de decisión sencillo. Hay que elegir uno, y la regla se acuerda **antes** de ver los resultados para que nadie la ajuste a su favor:

1. Gana el que encuentre más defectos.
2. Si empatan, el que dé menos falsas alarmas.

Los dos se entrenan y se evalúan con exactamente las mismas piezas. El ganador se guarda como `modelo_defecto.joblib` con la versión `defecto-0.1`. Es el modelo que usará la línea en M06, M07 y M08.

### 1 — Comparar con la misma vara

Vas a entrenar los dos candidatos con las mismas piezas y medirlos con las mismas piezas nuevas. Sin el mismo corte, la comparación no vale.

```bash
# Entrena logreg y árbol, compara y guarda el ganador como modelo_defecto.joblib
docker compose --profile lab run --rm --no-deps lab m03-03
```

**Resultado esperado:**

```text
{"logreg": {"tp": 15, "fp": 38, "fn": 6, "tn": 172, "recall": 0.7142857142857143, "fpr": 0.18095238095238095}, "arbol": {"tp": 16, "fp": 3, "fn": 5, "tn": 207, "recall": 0.7619047619047619, "fpr": 0.014285714285714285}}
OK m03-03: elegido=arbol recall=0.76 fpr=0.01
```

| | Defectos encontrados | Falsas alarmas |
|--|----------------------|----------------|
| logreg | 15 de 21 (0,71) | 38 de 210 (0,18) |
| árbol | 16 de 21 (0,76) | 3 de 210 (0,01) |

El árbol encuentra uno más y apenas da falsas alarmas.

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
candidatos = {
    "logreg": LogisticRegression(class_weight="balanced", max_iter=400),
    "arbol": DecisionTreeClassifier(max_depth=3, class_weight="balanced", random_state=7),
}
for nombre, modelo in candidatos.items():
    modelo.fit(train[FEATURES], train["defecto"])
    informe[nombre] = _tasas(test["defecto"], modelo.predict(test[FEATURES]))

# Regla: más recall; si empatan, menos falsas alarmas
ganador, datos = max(informe.items(), key=lambda it: (it[1]["recall"], -it[1]["fpr"]))
joblib.dump(datos["modelo"], DATA / "modelo_defecto.joblib")
(DATA / "VERSION").write_text("defecto-0.1\n")
```

</details>

### 2 — Leer lo que quedó escrito

Vas a mirar la versión y el nombre del modelo elegido. Son los ficheros que leerán el servicio y la auditoría.

```bash
cat data/VERSION data/modelo_elegido.txt
```

**Resultado esperado:**

```text
defecto-0.1
arbol
```

## Comprueba tu entendimiento

**La regla**

¿Coincide `modelo_elegido.txt` con lo que imprimió el `OK`?

→ Sí: los dos dicen `arbol`.

## Reto

### 1 — Empate

Si los dos recall fueran iguales, ¿con cuál te quedas?

<details>
<summary>Ver solución</summary>

Con el de menor tasa de falsas alarmas. Es la segunda clave de la regla.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `No such file … limpio.csv` | no está el CSV | lanza `m02-03` |
| `VERSION` vacío | el comando no terminó en `OK` | repite `m03-03` |
