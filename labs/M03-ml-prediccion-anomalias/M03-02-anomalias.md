# M03-02 — Detección temprana de anomalías

[← Página anterior](M03-01-prediccion-defectos.md) · [Siguiente página →](M03-03-comparacion-modelos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Ajustas un detector solo con ciclos normales y cuentas cuántos de los ciclos raros inyectados avisa.

### Prerrequisitos

- CPU. No usa la etiqueta de defecto para avisar.
- Unos 0,5 GB en el `run`.

### Qué está pasando

A veces no hay etiqueta que aprender. La máquina hace algo raro que no se había visto nunca: un rodamiento que empieza a fallar, una herramienta que se desgasta. Nadie ha marcado aún esas piezas como defectuosas, pero conviene enterarse **antes** de que lo sean.

Un **detector de anomalías** no aprende qué es un defecto: aprende **cómo es un ciclo normal** y avisa cuando uno se sale de ahí. Lo que mide es cuánto se aleja el ciclo, mirando todas las señales a la vez, de lo que la estación hace habitualmente.

Para comprobarlo se le pasan 200 ciclos: 180 normales y **20 con la vibración subida a propósito**, como si un rodamiento empezara a fallar. La marca de cuáles están alterados solo se usa al final, para contar cuántos avisó.

### 1 — Ajustar y avisar

Vas a enseñar al detector cómo es un ciclo normal y a pasarle ciclos nuevos. Una anomalía es «no se parece a lo normal», no «se parece a un defecto que ya conocía».

```bash
# Ajusta con ciclos normales y puntúa 200 ciclos (20 alterados)
docker compose --profile lab run --rm --no-deps lab m03-02
```

📋 Ficha del comando [`m03-02`](../comandos-lab.md#m03-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
inyectados=20 detectados=20
OK m03-02: avisos sobre inyectados 20/20
```

<details>
<summary>Qué hace por dentro (<code>infra/linea/cli.py</code>)</summary>

```python
normal = base[base["defecto"] == 0]                 # solo ciclos sanos
escala = StandardScaler()                           # cada señal en su escala (media 0, desviación 1)
base_z = escala.fit_transform(normal[FEATURES])
detector = EmpiricalCovariance().fit(base_z)        # aprende cómo varían juntas las señales
distancias = detector.mahalanobis(escala.transform(vig[FEATURES]))
marcas = np.where(distancias >= 13.3, -1, 1)        # -1 = aviso
```

13,3 es el percentil 99 de una chi-cuadrado con 4 señales: un ciclo normal solo lo supera 1 vez de cada 100.

</details>

## Comprueba tu entendimiento

**Para qué es la marca**

¿El modelo recibe la columna `inyectada`?

→ No. Si la recibiera, no estaría detectando: estaría leyendo la respuesta.

## Reto

### 1 — Umbral más duro

¿Qué pasa si subes o bajas el umbral de 13,3?

<details>
<summary>Ver solución</summary>

Subirlo esconde ciclos raros. Bajarlo llena el turno de avisos sobre ciclos normales, y un detector que avisa la mitad del día deja de ser una alerta.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el detector no ve los ciclos inyectados` | se ajustó con ciclos raros dentro | el comando separa normales e inyectados; relánzalo |
| `FALLO` sin número | la imagen está a medias | `docker compose build` otra vez |
