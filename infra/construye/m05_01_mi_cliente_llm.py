"""Constrúyelo tú (M05-01): tu propio cliente del modelo local.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_01_mi_cliente_llm.py
"""
import time

import httpx

LLM = "http://llm:8088"        # el contenedor llm, por su nombre en la red de Docker

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
PREGUNTA = "Explica en una frase qué es el mantenimiento preventivo."
LONGITUDES = (20, 80, 200)     # máximos de tokens que se prueban en el paso 4

# --- PASO 1: ¿está vivo el servicio? (ya está hecho) -------------------------
print("salud:", httpx.get(f"{LLM}/salud", timeout=10).json())

# --- PASO 2: hacer una pregunta ------------------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: contar los tokens -------------------------------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: cómo crece el tiempo con la longitud ------------------------------
# (pega aquí el bloque del paso 4)
