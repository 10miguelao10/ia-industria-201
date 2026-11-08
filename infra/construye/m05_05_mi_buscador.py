"""Constrúyelo tú (M05-05): tu propio buscador por significado (embeddings).

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_05_mi_buscador.py
"""
import re

import numpy as np
from llama_cpp import Llama

from linea.cli import _Silencio            # calla los mensajes internos de llama.cpp

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
PREGUNTA = "¿Cuánto calor aguanta el eje antes de avisar?"
MINIMO_PARECIDO = 0.0                      # parecido mínimo para dar un párrafo por bueno (0 = cualquiera)

# --- PASO 1: el modelo de embeddings y su licencia (ya está hecho) -----------
with _Silencio():
    modelo = Llama(model_path="/modelos/qwen3-embedding-0.6b-q8_0.gguf", embedding=True, n_ctx=512, verbose=False)
print(f"modelo: {modelo.metadata.get('general.name')}  licencia (escrita en el propio fichero): {modelo.metadata.get('general.license')}")

# --- PASO 2: un texto convertido en números ------------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: los párrafos del procedimiento, en números ------------------------
# (pega aquí el bloque del paso 3)

# --- PASO 4: buscar por significado --------------------------------------------
# (pega aquí el bloque del paso 4)

# --- PASO 5: comparar con la búsqueda por palabras -----------------------------
# (pega aquí el bloque del paso 5)
