"""Constrúyelo tú (M05-03): tu propio asistente con el procedimiento (RAG).

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_03_mi_asistente.py
"""
import re

import httpx

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
PREGUNTA = "¿A qué par se aprieta el tornillo de la brida?"
VACIAS = {"a", "al", "de", "del", "el", "la", "las", "los", "lo", "un", "una", "y", "o", "en", "se", "que",
          "qué", "es", "por", "para", "con", "hay", "cómo", "cuánto", "cuál", "si", "no", "su", "sus"}
MINIMO_PALABRAS = 1      # palabras en común que tiene que tener un párrafo para usarlo

# --- PASO 1: el procedimiento, en párrafos (ya está hecho) -------------------
documento = open("/opt/linea/docs/procedimiento-est01.md", encoding="utf-8").read()   # infra/linea/docs/
parrafos = [p.strip() for p in documento.split("\n\n") if p.strip() and not p.startswith("#")]
print(f"el procedimiento tiene {len(parrafos)} párrafos (sin contar los títulos)")

# --- PASO 2: las palabras que importan -----------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: elegir el párrafo -------------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: preguntar con el párrafo delante ----------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: comprobar que no se ha inventado nada -----------------------------
# (pega aquí el bloque del paso 5)
