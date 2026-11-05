# M02 — Captura, integración y preparación de datos

[← Página anterior](../M01-ia-industrial-arquitectura/M01-03-metricas-alertas.md) · [Siguiente página →](M02-01-telemetria.md)

> [!NOTE]
> **Cómo funciona este módulo.** Primero la **teoría**, luego la **demostración guiada**, y después **practicas tú** en los laboratorios.

## Qué aprenderás

- Publicar y consumir telemetría de la estación.
- Leer el mismo hecho por MQTT, OPC-UA y Modbus simulado.
- Dejar un dataset limpio, con unidades y sin huecos escondidos.

## Teoría

El modelo solo ve lo que la integración le entrega. Si la hora está mal, la unidad cambia a mitad de turno o faltan piezas, el entrenamiento aprende ese desastre.

### De dónde sale el dato

En la planta real sería un sensor cableado a un PLC. Aquí el PLC y el sensor son simulados, con la misma forma: un valor, una unidad, una hora y un nombre de variable.

### Tres formas de llevarse el dato

| Protocolo | Idea | Cuándo encaja |
|-----------|------|----------------|
| MQTT | Alguien publica un mensaje en un tema; quien se ha suscrito lo recibe | Eventos y telemetría ligera |
| OPC-UA | Un servidor expone variables con nombre y tipo; un cliente las lee o se suscribe | Integrar con equipos que ya hablan OPC-UA |
| Modbus TCP | Registros numerados en una dirección IP | Equipos sencillos que exponen holding registers |

No son tres verdades distintas. Son tres puertas al mismo hecho de proceso. El laboratorio lo demuestra leyendo la misma estación por las tres.

### Calidad mínima antes de analizar

- Hora presente y ordenable.
- Unidad explícita (°C no mezclados con décimas).
- Identificador de pieza o de ciclo.
- Huecos visibles, no rellenados en silencio.
- Valores imposibles apartados (una temperatura de 9999 es un fallo de sensor, no un pico de proceso).

## Demostración guiada

La misma estación se lee de tres formas. Cambia el modo de acceso, no la física. Después, una tabla pasa de «filas tal cual llegaron» a un dataset limpio.

Todo se lanza desde `infra/`, con mosquitto, sensor y archivador en marcha.

**1. MQTT: el cliente se entera sin preguntar.**

```bash
docker compose exec mosquitto mosquitto_sub -t 'linea/est01/ciclo' -v -C 2
```

**2. OPC-UA y Modbus: la misma temperatura con otros nombres.**

```bash
docker compose up -d opcua modbus
docker compose --profile lab run --rm --no-deps lab m02-02
```

📋 Ficha del comando [`m02-02`](../comandos-lab.md#m02-02): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
estado=63.22 opcua=63.22 modbus=63.2
OK m02-02: MQTT, OPC-UA y Modbus leen la misma temperatura
```

En OPC-UA el dato es el nodo `Estacion.Temperatura`. En Modbus es el registro 0, un entero en décimas (632 → 63,2 °C).

**3. Del crudo al limpio.**

```bash
docker compose --profile lab run --rm --no-deps lab m02-03
head -3 data/crudo.csv
head -3 data/imposibles.csv
```

📋 Ficha del comando [`m02-03`](../comandos-lab.md#m02-03): qué hace, qué lee, qué escribe y cuándo da `OK`.

```text
{"filas_crudo": 800, "filas_limpias": 768, "huecos": 32, "imposibles": 6, "piezas_unicas": 768}
OK m02-03: crudo=800 limpio=768 huecos=32
pieza_id,temperatura_c,vibracion_mm_s,corriente_a,presion_bar,defecto
H0001,61.39,0.286,4.07,5.96,0
H0002,61.45,0.268,4.06,6.0,0
pieza_id,temperatura_c,vibracion_mm_s,corriente_a,presion_bar,defecto
H0059,9999.0,0.218,4.22,6.09,0
H0322,9999.0,0.244,4.15,5.95,1
```

32 piezas sin temperatura y 6 con un sensor clavado en 9999 se quedan fuera del dataset de entrenamiento.

## Ahora practica tú

| Lab | Título | Qué harás |
|-----|--------|-----------|
| M02-01 | [Captura de telemetría industrial](M02-01-telemetria.md) | Publicar lecturas y consumirlas como eventos. |
| M02-02 | [Integración mediante protocolos industriales](M02-02-protocolos.md) | Leer la estación por MQTT, OPC-UA y Modbus. |
| M02-03 | [Preparación de información para analítica](M02-03-preparacion-datos.md) | Limpiar y normalizar hasta tener un dataset usable. |
| M02-04 | [Construir un dataset con datos de la línea](M02-04-dataset-linea.md) | Unir histórico y calidad en un dataset propio y descubrir el criterio de defecto. |

→ Empieza por **[M02-01 — Captura de telemetría industrial](M02-01-telemetria.md)**.

## Conclusiones del módulo

Al terminar los laboratorios de este módulo deberías tener claro que:

- La misma señal llega por varios protocolos (MQTT, OPC-UA, Modbus); integrar es conseguir que cuenten lo mismo.
- Un silencio de la máquina es un dato: no se rellena ni se confunde con un cero.
- Antes de entrenar hay que limpiar el histórico y contar lo que se descarta.
- Un dataset real se construye uniendo cómo se fabricó cada pieza con cómo salió, y la unión necesita una clave que no se repita.
