"""Constrúyelo tú (M03-02): tu propio detector de anomalías.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m03_02_mi_detector.py
"""
import numpy as np
from linea.datos import generar_limpio, vigilancia   # los mismos generadores que usa lab m03-02

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
SENALES = ["temperatura_c", "vibracion_mm_s", "corriente_a", "presion_bar"]
UMBRAL = 13.3                 # distancia a partir de la cual se avisa
VIBRACION_ALTERADA = None     # None = la avería del lab (vibración ~1,3 mm/s); un número = otra avería
CICLOS_POR_TURNO = 8 * 3600   # un ciclo por segundo durante un turno de 8 h

# --- PASO 1: los ciclos (ya está hecho) --------------------------------------
base = generar_limpio(400, seed=3)
normal = base[base["defecto"] == 0]                   # solo ciclos sanos: con esto aprende
vig = vigilancia()                                    # 200 ciclos nuevos que hay que vigilar
if VIBRACION_ALTERADA is not None:                    # otra avería: cambia la vibración de los 20 alterados
    vig.loc[vig["inyectada"] == 1, "vibracion_mm_s"] = VIBRACION_ALTERADA
alterado = vig["inyectada"] == 1                      # la marca: solo se usa para contar al final
print(f"ciclos normales para aprender={len(normal)} ciclos a vigilar={len(vig)} alterados={int(alterado.sum())}")

# --- PASO 2: aprender cómo es lo normal --------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: un detector sencillo, señal a señal -----------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: la distancia, con todas las señales a la vez --------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: avisar con un umbral y contar ------------------------------------
# (pega aquí el bloque del paso 5)

# --- PASO 6: un ciclo raro en conjunto ----------------------------------------
# (pega aquí el bloque del paso 6)

# --- PASO 7: cuántos avisos daría en un turno ---------------------------------
# (pega aquí el bloque del paso 7)
