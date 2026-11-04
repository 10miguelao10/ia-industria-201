# M04-01 — Clasificación automática de componentes

[← Página anterior](README.md) · [Siguiente página →](M04-02-deteccion-defectos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Entrenas un clasificador que separa componente correcto y defectuoso, y lo pruebas con imágenes que no vio.

### Prerrequisitos

- Solo `lab`. Genera 80 PNG pequeñas en `infra/data/imagenes/`.
- Sin cámara y sin GPU.

### En qué consiste

Las imágenes son sintéticas: una pieza gris y, en las malas, un rayón blanco. Hay 40 de cada. El 30 % final de cada clase no entra al entrenamiento. El modelo es una regresión logística sobre la imagen reducida a 16×16 píxeles.

### 1 — Generar y entrenar

Vas a generar el juego de imágenes, entrenar con el 70 % y medir el acierto con el 30 % que el modelo no ha visto.

```bash
# Genera las imágenes (si faltan), entrena y guarda modelo_vision.joblib
docker compose --profile lab run --rm --no-deps lab m04-01
```

**Resultado esperado:**

```text
acierto_prueba=0.88
OK m04-01: acierto=0.88 en imágenes no usadas al entrenar
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
def _features_imagen(ruta):
    img = Image.open(ruta).convert("L").resize((16, 16))    # gris y 16×16
    return np.asarray(img, dtype=np.float32).reshape(-1) / 255.0   # 256 números entre 0 y 1

X = np.stack([_features_imagen(r) for r in entreno["ruta"]])
modelo = LogisticRegression(max_iter=400)
modelo.fit(X, entreno["defecto"])                          # cada píxel es una entrada
```

Para el modelo, una imagen es una fila de 256 números: el brillo de cada píxel.

</details>

### 2 — Mirar una de cada

Vas a abrir una imagen buena y una defectuosa. Tienes que ver qué está aprendiendo el modelo: el rayón, no un fondo distinto.

```bash
ls data/imagenes/buenas | head -3        # ok_00.png, ok_01.png…
ls data/imagenes/defectuosas | head -3   # ko_00.png, ko_01.png…
```

Ábrelas en VS Code: `infra/data/imagenes/buenas/ok_00.png` y `infra/data/imagenes/defectuosas/ko_00.png`.

**Resultado esperado:** la defectuosa tiene una línea blanca; la buena, no.

![Pieza buena (izquierda) y defectuosa con rayón blanco (derecha)](../img/M04-01-buena-defectuosa.png)

## Comprueba tu entendimiento

**Imágenes nuevas**

El acierto que imprime el comando, ¿de qué imágenes es?

→ Del 30 % apartado, no de las del entrenamiento.

## Reto

### 1 — Atajo

Si todas las malas tuvieran otro fondo, ¿qué podría aprender el modelo?

<details>
<summary>Ver solución</summary>

El fondo en vez del rayón: acertaría aquí y fallaría en planta. En este generador el fondo cambia un poco entre imágenes pero no según la clase; la diferencia que importa es el rayón.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el clasificador visual no separa las piezas` | las imágenes no se generaron bien | borra `data/imagenes` y repite |
| no encuentras los PNG | los buscas dentro del contenedor | están en el disco del puesto, en `infra/data/imagenes` |
