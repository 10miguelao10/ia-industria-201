# M03 — Machine learning para predicción y detección de incidencias

[← Página anterior](../M02-captura-integracion-datos/M02-04-dataset-linea.md) · [Siguiente página →](M03-01-prediccion-defectos.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Entrenar un modelo que relacione condiciones de proceso con un defecto posterior.
- Detectar ciclos raros sin esperar a la etiqueta de calidad.
- Comparar modelos con métricas que importan cuando el defecto es escaso.

## Teoría

Aquí el modelo aprende de ejemplos. No programa umbrales a mano: los ajusta con históricos de la línea simulada.

### Tres tareas distintas

| Tarea | Pregunta | Qué necesitas |
|-------|----------|----------------|
| Clasificación | ¿Esta pieza acabará como defecto? | Histórico con la etiqueta de calidad |
| Regresión | ¿Qué valor numérico tendrá esta señal? | Histórico del valor a estimar |
| Anomalía | ¿Este ciclo no se parece a los normales? | Sobre todo ciclos buenos; el fallo puede no estar etiquetado |

No se sustituyen. Un detector de anomalías avisa de «esto es raro». Un clasificador avisa de «esto se parece a los defectos que ya vimos».

### Cómo saber si sirve

Si el defecto es raro, acertar siempre «pieza buena» da un porcentaje alto y no detecta nada. Hay que mirar cuántos defectos reales encontró el modelo y cuántas alarmas falsas generó.

También hay que separar datos de entrenamiento y datos de prueba por tiempo o por lote. Si la misma pieza entra en los dos sitios, el resultado miente.

## Demostración guiada

Se entrena un clasificador con las señales de proceso, se detectan anomalías sin usar la etiqueta y se comparan dos modelos sobre el mismo corte temporal.

Todo se lanza desde `infra/`, con `data/limpio.csv` ya generado (M02-03).

**1. Predecir defectos y leer la matriz de confusión.**

```bash
docker compose --profile lab run --rm --no-deps lab m03-01
```

📋 Ficha del comando [`m03-01`](../comandos-lab.md#m03-01): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
{"tp": 15, "fp": 38, "fn": 6, "tn": 172, "recall": 0.7142857142857143, "fpr": 0.18095238095238095}
OK m03-01: recall_defecto=0.71 falsas_alarmas=0.18
```

De 231 piezas nuevas, 21 son defectuosas: el modelo encuentra 15 y da 38 falsas alarmas. El acierto global sería (15 + 172) / 231 = 81 %, un número que no dice cuántos defectos se escapan.

**2. Avisar de lo raro sin etiqueta.**

```bash
docker compose --profile lab run --rm --no-deps lab m03-02
```

📋 Ficha del comando [`m03-02`](../comandos-lab.md#m03-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
inyectados=20 detectados=20
OK m03-02: avisos sobre inyectados 20/20
```

**3. Comparar dos modelos con la misma vara.**

```bash
docker compose --profile lab run --rm --no-deps lab m03-03
```

📋 Ficha del comando [`m03-03`](../comandos-lab.md#m03-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
OK m03-03: elegido=arbol recall=0.76 fpr=0.01
```

El árbol encuentra 16 de 21 defectos con 3 falsas alarmas; la regresión logística, 15 con 38. Mismo corte, regla escrita de antemano.

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M03-01 | [Predicción de defectos de fabricación](M03-01-prediccion-defectos.md) | Entrenar y evaluar un clasificador de defecto. |
| M03-02 | [Detección temprana de anomalías](M03-02-anomalias.md) | Marcar ciclos raros y convertirlos en aviso. |
| M03-03 | [Comparación de modelos predictivos](M03-03-comparacion-modelos.md) | Elegir entre enfoques con los mismos datos, red neuronal incluida. |
| M03-04 | [Entrenar con los datos de tu línea](M03-04-entrenar-datos-linea.md) | Entrenar con el dataset propio y comprobar que el modelo entiende el proceso. |

→ Empieza por **[M03-01 — Predicción de defectos de fabricación](M03-01-prediccion-defectos.md)**.

## Conclusiones del módulo

Al terminar los laboratorios de este módulo deberías tener claro que:

- Un modelo se mide por los defectos que encuentra y por las piezas buenas que para, no por un porcentaje global.
- Sin etiquetas también se puede avisar de lo raro, comparando con lo normal.
- El modelo que va a la línea se elige con una regla escrita de antemano y queda con nombre y versión.
- Con datos de la propia línea, un modelo puede descubrir el criterio del proceso; con pocos defectos, sus porcentajes no son fiables.
