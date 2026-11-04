# M04-02 — Detección automática de defectos

[← Página anterior](M04-01-clasificacion-componentes.md) · [Siguiente página →](M04-03-inspeccion-camara.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Localizas el rayón en la imagen y compruebas que una pieza buena no dispara la misma marca.

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
errores_zona=0 falsos_en_buenas=0
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

## Reto

### 1 — Límite

Este detector busca una línea blanca horizontal. ¿Qué defecto no vería?

<details>
<summary>Ver solución</summary>

Uno oscuro, uno vertical o uno que no cambia el brillo de una fila. Por eso un puesto real no se fía de un solo truco.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: la zona no cae sobre el rayón` | el manifiesto no es el de estas imágenes | borra `data/imagenes` y repite `m04-01` |
| falsos en buenas | se bajó el umbral de brillo | el comando usa 230; no lo bajes para «pillar más» |
