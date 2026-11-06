"""Constrúyelo tú (M05-02): tu propia aplicación que sabe fallar.

Lo construyes paso a paso: en cada PASO del lab te dan un bloque de código.
Pégalo debajo del comentario de ese paso, guarda y ejecuta desde infra/:

    docker compose --profile lab run --rm --no-deps --entrypoint python lab -W ignore /construye/m05_02_mi_aplicacion.py
"""
import httpx

# --- Decisiones tuyas (las cambiarás en los pasos finales) -------------------
SERVICIO = "http://llm:8088"     # dónde está el modelo
MAX_TOKENS = 60                  # longitud máxima de la respuesta
TIEMPO_MAX_S = 20                # cuánto espera la aplicación antes de rendirse

# --- PASO 1: la petición que manda la aplicación (ya está hecho) -------------
def peticion(pregunta):
    return {"messages": [{"role": "system", "content": "Responde en español, en una o dos frases."},
                         {"role": "user", "content": pregunta}],
            "max_tokens": MAX_TOKENS}

print("la aplicación preguntará a", SERVICIO, "con un máximo de", MAX_TOKENS, "tokens y", TIEMPO_MAX_S, "s de espera")

# --- PASO 2: preguntar y leer por qué terminó ----------------------------------
# (pega aquí el bloque del paso 2)

# --- PASO 3: un mensaje claro para cada caso -----------------------------------
# (pega aquí el bloque del paso 3)
