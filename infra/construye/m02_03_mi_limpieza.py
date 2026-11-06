"""Constrúyelo tú (M02-03): tu propia limpieza de datos.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m02_03_mi_limpieza.py
"""
import pandas as pd

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
IMPOSIBLE = 9999            # valor que da el sensor cuando está clavado
DECIMAS_DESDE = 150         # por encima de esto, la temperatura viene en décimas de grado
HUECOS = "excluir"          # "excluir" = quitar la pieza; "media" = rellenar con la media

# --- PASO 1: leer el crudo (ya está hecho) -----------------------------------
crudo = pd.read_csv("/data/crudo.csv")        # en tu equipo: infra/data/crudo.csv
print(f"crudo: {len(crudo)} filas, columnas {list(crudo.columns)}")

# --- PASO 2: contar los problemas ----------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: apartar los valores imposibles ------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: corregir las unidades ---------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: decidir qué hacer con los huecos ----------------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: comprobar contra el limpio del comando ----------------------------
# (pega aquí el bloque del paso 6)
