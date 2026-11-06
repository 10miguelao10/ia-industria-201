# Inteligencia Artificial Aplicada a Entornos Industriales

[Siguiente página →](labs/M01-ia-industrial-arquitectura/README.md)

Formación práctica sobre una línea de fabricación simulada. Recorres el ciclo completo: el dato sale del proceso, un modelo lo interpreta y el resultado vuelve a operación.

## Cómo funciona el curso

Sigue este README como índice y avanza **página a página** con **← Página anterior · Siguiente página →**.

Cada módulo tiene dos niveles: el **README del módulo**, organizado en bloques con la **teoría** y una
**demostración** de cada concepto, y los **laboratorios** donde practicas tú a tu ritmo (enlazados
desde cada bloque).

## Antes de empezar

| Requisito | Dónde |
|-----------|--------|
| Preparar el entorno | [infra/README.md](infra/README.md) — contenedores, datos y requisitos por laboratorio |
| Qué hace cada comando `lab …` | [Fichas de los comandos](labs/comandos-lab.md) |
| Primer caso | [M01](labs/M01-ia-industrial-arquitectura/README.md) |

## Guarda tu trabajo: tu propio fork

En los laboratorios vas a modificar ficheros: el panel, el archivador, las reglas de alerta, los prompts… Para no perder esos cambios y llevártelos al acabar el curso, trabaja sobre **tu propia copia del repositorio en GitHub** (un *fork*). Necesitas una cuenta de GitHub.

**1. Una sola vez, al empezar.** Desde la carpeta del repositorio:

```bash
# Inicia sesión en GitHub desde la terminal (sigue las instrucciones del navegador)
gh auth login

# Crea tu fork en GitHub y lo deja como «origin»; el repositorio del curso pasa a llamarse «upstream»
gh repo fork --remote

# Comprueba los dos remotos
git remote -v
```

**Resultado esperado:**

```text
origin    https://github.com/<tu-usuario>/ia-industria-201.git (fetch)
origin    https://github.com/<tu-usuario>/ia-industria-201.git (push)
upstream  https://github.com/my-it-labs/ia-industria-201.git (fetch)
upstream  https://github.com/my-it-labs/ia-industria-201.git (push)
```

**2. Al terminar cada laboratorio.** Guarda tus cambios con un mensaje que diga qué hiciste:

```bash
git add -A
git commit -m "M01-02: el panel avisa cuando los datos no son actuales"
git push
```

Lo que generan los laboratorios en `infra/data/` (histórico, modelos, CSV) y el fichero del modelo de lenguaje **no se suben**: están excluidos a propósito. Solo se guarda lo que tú cambias.

**3. Si el formador publica una corrección.** Tráela del repositorio del curso:

```bash
git pull upstream main
```

Si has cambiado el mismo fichero, Git te pedirá resolver el conflicto; pide ayuda al formador.

## Módulos

| # | Módulo | Índice |
|---|--------|--------|
| M01 | Introducción a la IA industrial y arquitecturas basadas en datos | [labs/M01-ia-industrial-arquitectura/](labs/M01-ia-industrial-arquitectura/README.md) |
| M02 | Captura, integración y preparación de datos | [labs/M02-captura-integracion-datos/](labs/M02-captura-integracion-datos/README.md) |
| M03 | Machine learning para predicción y detección de incidencias | [labs/M03-ml-prediccion-anomalias/](labs/M03-ml-prediccion-anomalias/README.md) |
| M04 | Visión artificial para control de calidad | [labs/M04-vision-control-calidad/](labs/M04-vision-control-calidad/README.md) |
| M05 | Inteligencia artificial generativa | [labs/M05-ia-generativa/](labs/M05-ia-generativa/README.md) |
| M06 | Edge AI e integración industrial | [labs/M06-edge-integracion-ot/](labs/M06-edge-integracion-ot/README.md) |
| M07 | Operación, MLOps y observabilidad | [labs/M07-mlops-observabilidad/](labs/M07-mlops-observabilidad/README.md) |
| M08 | Ciberseguridad y gobierno de IA | [labs/M08-ciberseguridad-gobierno/](labs/M08-ciberseguridad-gobierno/README.md) |

## Empieza aquí

→ **[M01 — Introducción a la IA industrial](labs/M01-ia-industrial-arquitectura/README.md)**
