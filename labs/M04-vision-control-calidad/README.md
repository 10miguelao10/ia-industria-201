# M04 — Visión artificial para control de calidad

[← Página anterior](../M03-ml-prediccion-anomalias/M03-03-comparacion-modelos.md) · [Siguiente página →](M04-01-clasificacion-componentes.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Entrenar un clasificador visual de pieza correcta y defectuosa.
- Ver qué pasa cuando el defecto es pequeño o el dataset está sesgado.
- Cerrar un ciclo de inspección: imagen, dictamen, registro.

## Teoría

La cámara no «ve calidad». Ve una imagen. El modelo propone una clase o señala una zona. Alguien, o un automatismo, convierte eso en aceptar, revisar o rechazar.

### Dos tareas

| Tarea | Salida | Cuándo |
|-------|--------|--------|
| Clasificación de la imagen | Pieza correcta o defectuosa | El defecto cambia el aspecto general y basta un sí o un no |
| Detección del defecto | Zona de la imagen donde está el problema | Hace falta decir dónde está, no solo que la pieza está mal |

Las dos fallan si el dataset miente: pocas piezas malas, luz distinta a la de línea, o fotos de laboratorio que no se parecen al puesto.

### Qué limita la precisión

- Pocas imágenes del defecto que de verdad importa.
- Fondo, reflejo o posición que el modelo usa como atajo.
- Un umbral de aceptación demasiado alegre: deja pasar defectos.
- Un umbral demasiado duro: manda a revisión casi todo.

El laboratorio mide ese compromiso. No busca un porcentaje redondo.

## Demostración guiada

Se enseñan imágenes de componente correctas y defectuosas, un modelo que clasifica imágenes nuevas, una detección que dice dónde está el defecto y un lote que sale con dictamen por pieza.

Todo se lanza desde `infra/`.

**1. Clasificar.**

```bash
docker compose --profile lab run --rm --no-deps lab m04-01
```

```text
acierto_prueba=0.88
OK m04-01: acierto=0.88 en imágenes no usadas al entrenar
```

Abre `infra/data/imagenes/buenas/ok_00.png` y `infra/data/imagenes/defectuosas/ko_00.png`:

![Pieza buena y defectuosa](../img/M04-01-buena-defectuosa.png)

**2. Localizar el defecto.**

```bash
docker compose --profile lab run --rm --no-deps lab m04-02
```

```text
errores_zona=0 falsos_en_buenas=0
OK m04-02: zona correcta en 5 defectos; buenas sin marca=0
```

**3. Inspeccionar un lote.**

```bash
docker compose --profile lab run --rm --no-deps lab m04-03
```

```text
   imagen  probabilidad_defecto decision
ok_00.png                 0.345  aceptar
ok_01.png                 0.269  aceptar
ok_02.png                 0.314  aceptar
ko_00.png                 0.493  aceptar
ko_01.png                 0.657  revisar
ko_02.png                 0.714  revisar
OK m04-03: registro=6 revisar=2
```

`ko_00.png` es defectuosa y se acepta por poco (0,493 frente al umbral de 0,5). Un modelo con un 88 % de acierto deja escapar piezas: hay que decidir dónde poner el umbral.

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M04-01 | [Clasificación automática de componentes](M04-01-clasificacion-componentes.md) | Separar imágenes de pieza correcta y defectuosa. |
| M04-02 | [Detección automática de defectos](M04-02-deteccion-defectos.md) | Localizar el defecto, no solo clasificar la pieza. |
| M04-03 | [Sistema de inspección basado en cámara](M04-03-inspeccion-camara.md) | Analizar imágenes y dejar un dictamen automático. |

→ Empieza por **[M04-01 — Clasificación automática de componentes](M04-01-clasificacion-componentes.md)**.
