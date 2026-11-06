# M03-02 — Detección temprana de anomalías

[← Página anterior](M03-01-prediccion-defectos.md) · [Siguiente página →](M03-03-comparacion-modelos.md)

> Práctica del módulo. La teoría y la demostración están en el [README del módulo](README.md).
>
> Lanza los comandos desde la carpeta `infra/` del repositorio. Un paso que cuadra termina con una línea que empieza por `OK`.

### Objetivo

Comprender qué es la **detección de [anomalías](../glosario/03-aprendizaje-automatico.md#anomalia)**: cómo se avisa de lo raro sin tener ejemplos de defecto, cómo debe ajustarse un detector, cuáles son sus límites y cómo se mejora.

### Prerrequisitos

- CPU. No usa la [etiqueta](../glosario/03-aprendizaje-automatico.md#etiqueta) de defecto para avisar.
- Unos 0,5 GB en el `run`.

### Qué está pasando

A veces no hay etiqueta que aprender. La máquina hace algo raro que no se había visto nunca: un rodamiento que empieza a fallar, una herramienta que se desgasta. Nadie ha marcado aún esas piezas como defectuosas, pero conviene enterarse **antes** de que lo sean.

Un **detector de anomalías** no aprende qué es un defecto: aprende **cómo es un ciclo normal** y avisa cuando uno se sale de ahí. Lo que mide es cuánto se aleja el ciclo, mirando todas las [señales](../glosario/03-aprendizaje-automatico.md#senal) a la vez, de lo que la estación hace habitualmente.

Para comprobarlo se le pasan 200 ciclos: 180 normales y **20 con una avería simulada**: el laboratorio les ha subido la vibración a propósito, como si un rodamiento empezara a fallar. Cada ciclo lleva la columna `averia_simulada` (1 = avería simulada, 0 = normal). El detector no la ve: solo se usa al final, para contar cuántas averías avisó.

### 1 — Ajustar y avisar

Vas a enseñar al detector cómo es un ciclo normal y a pasarle ciclos nuevos. Una anomalía es «no se parece a lo normal», no «se parece a un defecto que ya conocía».

```bash
# Ajusta con ciclos normales y puntúa 200 ciclos (20 con avería simulada)
docker compose --profile lab run --rm --no-deps lab m03-02
```

📋 Ficha del comando [`m03-02`](../comandos-lab.md#m03-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

**Resultado esperado:**

```text
umbral=13.3 averias_simuladas=20 avisadas=20 avisos_sobre_normales=7 de 180
OK m03-02: averías simuladas avisadas 20/20
```

**Cómo se lee:** avisa los **20 ciclos con avería simulada** y, además, **7 de los 180 normales** (un 4 %): son [falsas alarmas](../glosario/03-aprendizaje-automatico.md#matriz-confusion). Un detector de anomalías siempre da alguna, porque lo normal también tiene sus extremos.

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

¿El modelo recibe la columna `averia_simulada`?

→ No. Si la recibiera, no estaría detectando: estaría leyendo la respuesta.

## Investiga: cuánto se alejan

**Qué ocurre:** el comando deja los 200 ciclos que ha puntuado en `infra/data/vigilancia.csv`, con su distancia y si dio aviso. Ábrelo en VS Code y después resume con `lab sql`:

```bash
docker compose --profile lab run --rm --no-deps lab sql \
  "SELECT averia_simulada, COUNT(*) AS ciclos, ROUND(AVG(vibracion_mm_s), 3) AS vib,
          ROUND(AVG(distancia), 1) AS distancia_media, SUM(aviso) AS avisos
   FROM vigilancia GROUP BY averia_simulada"
```

**Resultado esperado:**

```text
 averia_simulada  ciclos   vib  distancia_media  avisos
               0     180 0.249              4.8       7
               1      20 1.338            235.4      20
```

**Cómo se lee:** los ciclos normales están a una distancia media de 4,8 de «lo normal»; los de avería simulada, a **235**: su vibración es cinco veces la habitual. Aquí la anomalía es muy evidente. En planta, un rodamiento que empieza a fallar da distancias de 15 o 20, muy cerca del límite, y ahí se nota de verdad dónde se pone el [umbral](../glosario/03-aprendizaje-automatico.md#umbral).

## Experimenta: mover el umbral

**Qué ocurre:** el umbral de 13,3 sale de la estadística: con cuatro señales, un ciclo normal solo lo supera 1 de cada 100 veces. Vas a probar uno más bajo y uno más alto.

```bash
docker compose --profile lab run --rm --no-deps lab m03-02 umbral=8
docker compose --profile lab run --rm --no-deps lab m03-02 umbral=25
```

**Resultado esperado:**

```text
umbral=8.0 averias_simuladas=20 avisadas=20 avisos_sobre_normales=34 de 180
```

```text
umbral=25.0 averias_simuladas=20 avisadas=20 avisos_sobre_normales=0 de 180
```

| Umbral | Averías simuladas avisadas | Falsas alarmas sobre normales |
|--------|--------------------|-------------------------------|
| 8 | 20 de 20 | 34 de 180 (19 %) |
| 13,3 | 20 de 20 | 7 de 180 (4 %) |
| 25 | 20 de 20 | 0 de 180 |

**Cómo se lee:** con anomalías tan claras, un umbral alto las sigue viendo todas y elimina las falsas alarmas. Pero ese umbral de 25 solo es «mejor» porque estas anomalías están a 235. Si el rodamiento empezara a fallar poco a poco, con distancias de 15, el umbral de 25 **no avisaría hasta que fuera tarde**. Se elige con anomalías realistas, no con las más fáciles.

## Constrúyelo tú: tu propio detector

**Qué está pasando:** `lab m03-02` usa un detector ya hecho de una librería. Ahora lo construyes tú, **pieza a pieza**, con cuentas que puedes seguir: primero aprendes cómo es un ciclo normal, luego pruebas una regla sencilla señal a señal, después calculas tú la distancia con todas las señales a la vez y, al final, traduces las falsas alarmas a lo que importa en planta: **cuántos avisos recibiría el turno**. Como el código es tuyo, podrás probar lo que el comando no deja: una avería que empieza poco a poco.

**Cómo se trabaja en cada paso:**

1. Lees qué va a hacer el bloque y para qué.
2. Copias el bloque y lo pegas en el fichero, **debajo del comentario de ese paso** (`# --- PASO N …`), en lugar de la línea `# (pega aquí el bloque del paso N)`.
3. Guardas y ejecutas el script. Cada ejecución repite todo desde el principio, así que la salida crece paso a paso: lo nuevo aparece al final.

### 1 — Abrir el fichero y ejecutarlo tal cual

**Qué ocurre:** abres en VS Code el fichero [`infra/construye/m03_02_mi_detector.py`](../../infra/construye/m03_02_mi_detector.py). Arriba están las **decisiones** que cambiarás al final (`UMBRAL`, `VIBRACION_AVERIA`, `CICLOS_POR_TURNO`). El paso 1 ya está escrito: genera **los mismos ciclos que usa `lab m03-02`**, los normales para aprender y los 200 que hay que vigilar, 20 de ellos con una avería simulada (la vibración subida a propósito). Lo ejecutas sin tocar nada.

```bash
# Ejecuta tu script con el Python del contenedor lab (-W ignore oculta avisos de las librerías)
docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_02_mi_detector.py
```

**Resultado esperado:**

```text
ciclos normales para aprender=358 ciclos a vigilar=200 averias_simuladas=20
```

**Cómo se lee:** de 400 ciclos de [histórico](../glosario/01-datos-arquitectura.md#historico), 358 eran sanos: son los que enseñan cómo es lo normal. Los otros 42 se descartan, porque un detector que aprende con ciclos defectuosos dentro aprende que lo defectuoso es normal. La columna `averia_simulada` dice cuáles de los 200 tienen avería simulada, y solo se usa al final para contar.

### 2 — Aprender cómo es lo normal

**Qué ocurre:** calculas, con los ciclos sanos, el **valor habitual** de cada señal (la media) y **cuánto varía** normalmente (la desviación). Con solo estos dos números por señal ya se puede decir si un valor es raro.

Pega debajo de `# --- PASO 2`:

```python
media = normal[SENALES].mean()                        # el valor habitual de cada señal
desviacion = normal[SENALES].std(ddof=0)              # cuánto varía cada señal normalmente
print("señal            media  desviación")
for senal in SENALES:
    print(f"{senal:15s} {media[senal]:6.3f}  {desviacion[senal]:6.3f}")
```

**Resultado esperado** (líneas nuevas):

```text
señal            media  desviación
temperatura_c   61.649   2.045
vibracion_mm_s   0.254   0.072
corriente_a      4.113   0.151
presion_bar      6.000   0.120
```

**Cómo se lee:** un ciclo normal tiene la vibración en torno a 0,254 mm/s, y lo habitual es que se separe unos 0,072 arriba o abajo. Esto **es todo lo que sabe el detector**: [no ha visto](../glosario/03-aprendizaje-automatico.md#particion) ni una sola avería.

### 3 — Un detector sencillo, señal a señal

**Qué ocurre:** antes de usar nada sofisticado, pruebas la regla que pondría cualquiera: para cada ciclo, mides a cuántas desviaciones está cada señal de su media (eso se llama **z**), y avisas si **alguna** está a más de 3. Es la base con la que comparar.

Pega debajo de `# --- PASO 3`:

```python
# z = a cuántas desviaciones está cada señal de su media (0 = justo en la media)
z_vig = (vig[SENALES] - media) / desviacion

# Regla sencilla: avisa si ALGUNA señal está a más de 3 desviaciones de su media
aviso_simple = (z_vig.abs() > 3).any(axis=1)
print(f"señal a señal: averías avisadas={int((aviso_simple & averia).sum())} de {int(averia.sum())}"
      f"  falsas alarmas={int((aviso_simple & ~averia).sum())} de {int((~averia).sum())}")
```

**Resultado esperado** (línea nueva):

```text
señal a señal: averías avisadas=20 de 20  falsas alarmas=8 de 180
```

**Cómo se lee:** con una avería tan clara, la regla sencilla ya la ve entera: la vibración de la avería simulada (1,1 a 1,5 mm/s) está a más de 11 desviaciones de su media. Da 8 falsas alarmas sobre 180 ciclos normales. Si funcionara igual de bien siempre, no haría falta nada más. El paso 6 enseña dónde se queda corta.

### 4 — La distancia, con todas las señales a la vez

**Qué ocurre:** calculas tú la **distancia de [Mahalanobis](../glosario/03-aprendizaje-automatico.md#mahalanobis)**: un solo número por ciclo que dice cuánto se aleja de lo normal teniendo en cuenta las cuatro señales juntas y cómo varían juntas. Es lo que hace por dentro `lab m03-02`. Después miras la distancia de tres ciclos normales y tres con avería simulada.

Pega debajo de `# --- PASO 4`:

```python
# Pasa los ciclos normales a la misma escala (z) y mide cómo varían juntas las señales
z_normal = (normal[SENALES] - media) / desviacion
covarianza = np.cov(z_normal.T, bias=True)            # tabla 4×4: cuánto se mueve cada señal con las otras
inversa = np.linalg.inv(covarianza)

# Distancia de Mahalanobis (al cuadrado) de cada ciclo a «lo normal»
z = z_vig.to_numpy()
vig["distancia"] = ((z @ inversa) * z).sum(axis=1)

columnas = ["pieza_id", "vibracion_mm_s", "distancia", "averia_simulada"]
print(vig[columnas].head(3).round(3).to_string(index=False))    # tres normales
print(vig[columnas].tail(3).round(3).to_string(index=False))    # tres con avería simulada
```

**Resultado esperado** (líneas nuevas):

```text
pieza_id  vibracion_mm_s  distancia  averia_simulada
   H0001           0.276      2.968                0
   H0002           0.227      2.525                0
   H0003           0.283      4.254                0
pieza_id  vibracion_mm_s  distancia  averia_simulada
   H0198           1.274    224.945                1
   H0199           1.462    294.711                1
   H0200           1.339    234.178                1
```

**Cómo se lee:** los ciclos normales están a una distancia de 2 a 4; los de avería simulada, a más de 200. La cuenta es, en esencia, **sumar los z al cuadrado de las cuatro señales**, corrigiendo con la tabla de covarianza las señales que suben y bajan juntas para no contar dos veces lo mismo. En esta línea las cuatro señales varían por separado, así que la corrección es pequeña. Por eso la distancia **crece con el cuadrado**: una vibración a 12 desviaciones aporta 12² = 144.

### 5 — Avisar con un umbral y contar

**Qué ocurre:** avisas cuando la distancia llega al `UMBRAL` (13,3, arriba del fichero) y cuentas aciertos y falsas alarmas con la marca `averia_simulada`.

Pega debajo de `# --- PASO 5`:

```python
aviso = vig["distancia"] >= UMBRAL
avisados = int((aviso & averia).sum())
falsas = int((aviso & ~averia).sum())
print(f"umbral={UMBRAL}: averías avisadas={avisados} de {int(averia.sum())}  falsas alarmas={falsas} de {int((~averia).sum())}")
```

**Resultado esperado** (línea nueva):

```text
umbral=13.3: averías avisadas=20 de 20  falsas alarmas=7 de 180
```

**Cómo se lee:** es **exactamente** lo que daba `lab m03-02`: 20 de 20 y 7 falsas alarmas. Has reconstruido el detector de la librería con una media, una desviación y una tabla de 4 × 4. El 13,3 no es un número a ojo: con cuatro señales, un ciclo normal solo lo supera 1 vez de cada 100.

### 6 — Un ciclo raro en conjunto

**Qué ocurre:** inventas un ciclo en el que **cada señal está algo alta, pero ninguna exagerada**: 2,5 desviaciones por encima de su media. Lo pasas por los dos detectores.

Pega debajo de `# --- PASO 6`:

```python
# Un ciclo inventado: cada señal 2,5 desviaciones por encima de su media.
# Ninguna pasa de 3 por sí sola, pero las cuatro están altas a la vez.
raro = media + 2.5 * desviacion
z_raro = ((raro - media) / desviacion).to_numpy()
print(f"ciclo raro: {raro.round(3).to_dict()}")
print(f"  señal a señal avisa: {bool((np.abs(z_raro) > 3).any())}")
print(f"  distancia={float(z_raro @ inversa @ z_raro):.1f} -> avisa: {float(z_raro @ inversa @ z_raro) >= UMBRAL}")
```

**Resultado esperado** (líneas nuevas):

```text
ciclo raro: {'temperatura_c': 66.762, 'vibracion_mm_s': 0.433, 'corriente_a': 4.489, 'presion_bar': 6.299}
  señal a señal avisa: False
  distancia=24.7 -> avisa: True
```

**Cómo se lee:** la regla señal a señal **no avisa**, porque ninguna señal pasa de 3 desviaciones. La distancia sí, con 24,7: que **las cuatro** estén altas a la vez es muy raro en un ciclo normal, aunque cada una por separado parezca aceptable. Esta es la ventaja de mirar todas las señales juntas.

### 7 — Cuántos avisos daría en un turno

**Qué ocurre:** un porcentaje de falsas alarmas no dice nada al jefe de turno. Lo conviertes en **avisos por turno**, con un ciclo por segundo durante 8 horas (`CICLOS_POR_TURNO`).

Pega debajo de `# --- PASO 7`:

```python
tasa_falsas = falsas / int((~averia).sum())          # fracción de ciclos normales que dan aviso
print(f"falsas alarmas: {tasa_falsas:.1%} de los ciclos normales -> ~{tasa_falsas * CICLOS_POR_TURNO:.0f} avisos falsos por turno")
```

**Resultado esperado** (línea nueva):

```text
falsas alarmas: 3.9% de los ciclos normales -> ~1120 avisos falsos por turno
```

**Cómo se lee:** un 3,9 % parece poco, pero son **más de mil avisos falsos por turno**, casi uno cada 25 segundos. Nadie los mira. Por eso, en planta, un detector así no avisa por cada ciclo suelto: avisa cuando **se repite en varios ciclos seguidos** o cuando la señal **tiende** a salirse, como harás en el M06-03.

### 8 — Decide tú: el umbral «perfecto»

**Qué ocurre:** con 13,3 hay demasiadas falsas alarmas. Cambias `UMBRAL = 13.3` por `UMBRAL = 25`, arriba del fichero, y ejecutas.

**Resultado esperado** (líneas que cambian):

```text
umbral=25: averías avisadas=20 de 20  falsas alarmas=0 de 180
falsas alarmas: 0.0% de los ciclos normales -> ~0 avisos falsos por turno
```

**Cómo se lee:** parece perfecto: todas las averías y ni un aviso falso. Pero esta avería está a más de 200. Ahora pruébalo con una avería que **empieza**: deja `UMBRAL = 25` y cambia `VIBRACION_AVERIA = None` por `VIBRACION_AVERIA = 0.55`, una vibración solo algo más alta de lo normal en los 20 ciclos con avería simulada.

**Predice:** ¿cuántas de las 20 avisará con el umbral de 25? ¿Y con 13,3?

**Resultado esperado** (con 25 y después con 13,3):

```text
umbral=25: averías avisadas=2 de 20  falsas alarmas=0 de 180
```

```text
umbral=13.3: averías avisadas=20 de 20  falsas alarmas=7 de 180
```

| Avería | Umbral | Averías avisadas | Avisos falsos por turno |
|--------|--------|------------------|-------------------------|
| Clara (vibración ~1,3) | 13,3 | 20 de 20 | ~1 120 |
| Clara (vibración ~1,3) | 25 | 20 de 20 | 0 |
| Empieza (vibración 0,55) | 13,3 | 20 de 20 | ~1 120 |
| Empieza (vibración 0,55) | 25 | **2 de 20** | 0 |

**Cómo se lee:** el umbral de 25 solo era «perfecto» con una avería que ya es evidente. Cuando la avería empieza, que es cuando interesa enterarse, **se le escapan 18 de 20**. El umbral se elige con las averías que quieres ver a tiempo, no con las más fáciles.

### 9 — Decide tú: una avería aún más temprana

**Qué ocurre:** cambias a `VIBRACION_AVERIA = 0.45`, muy cerca del borde de lo normal, y pruebas con `UMBRAL = 13.3` y con `UMBRAL = 8`.

**Resultado esperado** (con 13,3 y después con 8):

```text
umbral=13.3: averías avisadas=4 de 20  falsas alarmas=7 de 180
falsas alarmas: 3.9% de los ciclos normales -> ~1120 avisos falsos por turno
```

```text
umbral=8: averías avisadas=18 de 20  falsas alarmas=34 de 180
falsas alarmas: 18.9% de los ciclos normales -> ~5440 avisos falsos por turno
```

**Cómo se lee:** con una avería metida en el ruido normal, **ningún umbral la resuelve**: o se escapa (4 de 20) o el turno recibe más de cinco mil avisos falsos. Mirar un solo ciclo no da para más. Lo que funciona es mirar **la tendencia de muchos ciclos**: una vibración que sube poco a poco durante una hora es una señal clara, aunque cada ciclo suelto parezca normal. En el reto 2 lo pruebas con una regla de repetición. Vuelve a dejar `UMBRAL = 13.3` y `VIBRACION_AVERIA = None`.

## Reto

Los dos retos se hacen con tu script de «Constrúyelo tú»: cambias algo, ejecutas y compruebas el resultado. Al acabar, vuelve a dejar `UMBRAL = 13.3` y `VIBRACION_AVERIA = None`.

### 1 — El umbral más alto que no pierde la avería que empieza

**La situación:** con el umbral de 13,3, el detector da ~1 120 avisos falsos por turno (paso 7), y el jefe de turno quiere subirlo. Mantenimiento pone una condición: no se puede perder la avería que empieza, la de vibración 0,55 mm/s del paso 8.

**Qué haces:** arriba del fichero pones `VIBRACION_AVERIA = 0.55` y pruebas, uno tras otro, `UMBRAL = 15`, `17`, `18` y `20`. Ejecuta después de cada cambio y apunta, de las líneas `umbral=…` y `falsas alarmas: …`, cuántas averías avisa y cuántos avisos falsos daría por turno.

**Lo que buscas:** el umbral **más alto** que todavía avisa las **20 de 20**. ¿Cuántos avisos falsos por turno quedan con él?

<details>
<summary>Ver solución</summary>

Las dos líneas de cada ejecución, juntas en una:

```text
umbral=15: averías avisadas=20 de 20  falsas alarmas=4 de 180    -> ~640 avisos falsos por turno
umbral=17: averías avisadas=20 de 20  falsas alarmas=3 de 180    -> ~480 avisos falsos por turno
umbral=18: averías avisadas=17 de 20  falsas alarmas=3 de 180    -> ~480 avisos falsos por turno
umbral=20: averías avisadas=13 de 20  falsas alarmas=2 de 180    -> ~320 avisos falsos por turno
```

**El umbral más alto es 17**: avisa las 20 y deja **~480 avisos falsos por turno**. A partir de 18 empiezan a escaparse averías.

**Cómo se lee:** subir el umbral solo te lleva de 1 120 a 480 avisos falsos antes de empezar a perder averías. Siguen siendo uno por minuto: el umbral, por sí solo, no resuelve el problema. Hace falta otra idea, la del reto 2.

</details>

### 2 — Avisar solo si se repite

**La situación:** una falsa alarma es un ciclo normal que, por azar, sale algo lejos de lo normal; el siguiente ciclo vuelve a ser normal. Una avería, en cambio, **dura**: en tus datos, los 20 ciclos con avería simulada van seguidos, al final (H0181 a H0200), como pasaría con un rodamiento que empieza a fallar.

**Qué haces:** añades al final del script una regla nueva: **avisar solo cuando el ciclo y los dos anteriores pasan el umbral**. Y la pruebas con el caso que en el paso 9 no tenía arreglo: `VIBRACION_AVERIA = 0.45` y `UMBRAL = 8`, que daba más de 5 000 avisos falsos por turno.

**Pistas:**

- `aviso` (del paso 5) tiene un valor por ciclo: `True` si ese ciclo pasa el umbral.
- `aviso.shift(1, fill_value=False)` da, para cada ciclo, el aviso **del ciclo anterior**; con `shift(2, …)`, el de dos ciclos antes.
- `&` es «y»: `a & b` es `True` solo si los dos lo son.
- Imprime las averías avisadas y las falsas alarmas igual que en el paso 5.

**Lo que buscas:** que las falsas alarmas bajen mucho sin dejar de ver la avería.

<details>
<summary>Ver solución</summary>

Al final del fichero:

```python
# Reto 2: avisar solo si el ciclo y los dos anteriores pasan el umbral
seguidos = aviso & aviso.shift(1, fill_value=False) & aviso.shift(2, fill_value=False)
print(f"umbral={UMBRAL} con 3 seguidos: averías avisadas={int((seguidos & averia).sum())} de {int(averia.sum())}"
      f"  falsas alarmas={int((seguidos & ~averia).sum())} de {int((~averia).sum())}")

# En un turno: tres falsas alarmas sueltas seguidas, si caen al azar, pasan con probabilidad tasa³
print(f"  en un turno: ~{tasa_falsas ** 3 * CICLOS_POR_TURNO:.0f} avisos falsos con la regla de 3 seguidos "
      f"(frente a ~{tasa_falsas * CICLOS_POR_TURNO:.0f} sin ella)")
```

**Resultado** (con `VIBRACION_AVERIA = 0.45` y `UMBRAL = 8`):

```text
umbral=8: averías avisadas=18 de 20  falsas alarmas=34 de 180
falsas alarmas: 18.9% de los ciclos normales -> ~5440 avisos falsos por turno
umbral=8 con 3 seguidos: averías avisadas=13 de 20  falsas alarmas=0 de 180
  en un turno: ~194 avisos falsos con la regla de 3 seguidos (frente a ~5440 sin ella)
```

Y con el detector del lab (`VIBRACION_AVERIA = None`, `UMBRAL = 13.3`):

```text
umbral=13.3 con 3 seguidos: averías avisadas=18 de 20  falsas alarmas=0 de 180
  en un turno: ~2 avisos falsos con la regla de 3 seguidos (frente a ~1120 sin ella)
```

**Cómo se lee:**

- **La avería que no tenía arreglo ahora se ve**: 13 ciclos avisados de 20, y ninguna falsa alarma en los 200 ciclos.
- **El precio es un pequeño retraso**: los dos primeros ciclos de la avería no pueden avisar, porque la regla espera a tres seguidos. Con un ciclo por segundo, son 2 segundos.
- **Cero en 200 ciclos no es cero en un turno.** La última línea lo calcula para 28 800 ciclos: con el umbral de 8 quedan ~194 avisos falsos, frente a ~5 440; con el de 13,3, **~2 por turno frente a ~1 120**, y la avería del lab se sigue viendo.

**La regla:** un detector útil combina **cuánto se aleja** un ciclo (el umbral) con **cuánto dura** (la repetición). Es la misma idea que el tiempo `for` de las [alertas](../glosario/02-observabilidad.md#alerta) de Prometheus del M01-03: la condición tiene que mantenerse un rato antes de avisar.

</details>

## Errores frecuentes

| Síntoma | Causa probable | Cómo arreglarlo |
|---------|----------------|-----------------|
| `FALLO: el detector no ve las averías simuladas` | se ajustó con ciclos raros dentro | el comando separa los normales de las averías simuladas; relánzalo |
| `FALLO` sin número | la imagen está a medias | `docker compose build` otra vez |
| `NameError: name 'media' is not defined` (o `z_vig`, `inversa`, `falsas`) | pegaste un bloque en el hueco de otro paso, o te saltaste uno | cada bloque va debajo de su `# --- PASO N`, en orden |
| `IndentationError` | el bloque quedó con espacios de más o de menos al pegarlo | las líneas de cada bloque empiezan en la columna 0, salvo las de dentro del `for` |
| `ModuleNotFoundError: No module named 'linea'` | ejecutaste el script con el Python de tu equipo | ejecútalo con el comando del paso 1, dentro del contenedor `lab` |
| tu paso 5 no da 20 / 7 | cambiaste `UMBRAL` o `VIBRACION_AVERIA` arriba del fichero | vuelve a `UMBRAL = 13.3` y `VIBRACION_AVERIA = None` |

## Conclusiones

### Qué es detectar anomalías

Es avisar cuando un ciclo **no se parece a lo normal**, aunque nunca se haya visto ese fallo. El detector no aprende qué es un defecto: aprende cómo son los ciclos sanos, y mide cuánto se aleja cada ciclo nuevo de ellos, con todas las señales a la vez.

### Cómo debe ajustarse un detector

| Requisito | Cómo se cumple en el lab |
|-----------|--------------------------|
| Aprender solo de lo normal | Se ajusta con piezas sin defecto. Si se ajustara con anomalías dentro, aprendería que son normales (lo verás en el M06-03) |
| Mirar las señales juntas | La distancia de Mahalanobis tiene en cuenta cómo varían juntas |
| Un umbral con sentido | 13,3: un ciclo normal solo lo supera 1 de cada 100 veces |
| Evaluarlo sin hacer trampa | La columna `averia_simulada` solo se usa al final, para contar aciertos |

Resultado: avisó los **20 ciclos** con avería simulada, con 7 falsas alarmas sobre 180 normales.

### Sus límites

| Límite | Qué provoca |
|--------|-------------|
| Avisa de lo raro, no de lo defectuoso | Un cambio legítimo (otra referencia, otra herramienta) también dispara avisos |
| El umbral es un compromiso | Más bajo: avisos sobre ciclos normales. Más alto: anomalías sin avisar |
| Depende de que «lo normal» sea representativo | Si se ajusta con ciclos que ya eran raros, deja de verlos |
| Un porcentaje pequeño son muchos avisos | Un 3,9 % de falsas alarmas, con un ciclo por segundo, son ~1 120 avisos falsos por turno |
| Las averías tempranas se esconden en el ruido | Con una vibración de 0,45 mm/s, el umbral de 13,3 solo avisa 4 de 20 |

### Cómo se mejora

- **Revisar cada aviso** y, cuando se confirme la causa, convertirlo en un ejemplo etiquetado para un modelo como el de M03-01.
- **Reajustar lo normal** cuando cambie legítimamente el proceso.
- **Medir los avisos por turno**, para que el umbral no llene el día de alarmas que nadie mira.
- **Avisar por repetición o por tendencia**, no por un ciclo suelto: es lo que separa una avería que empieza del ruido normal.
- **Elegir el umbral con averías realistas**: el de 25 parecía perfecto con la avería del lab y dejaba escapar 18 de 20 cuando la avería empezaba.

### En una frase

> 🔑 Una anomalía no es un defecto: es «esto no se parece a lo de siempre». Sirve para mirar a tiempo, no para rechazar piezas sola.
