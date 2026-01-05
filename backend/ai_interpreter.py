import re

# =========================
# CONFIGURACIÓN BASE
# =========================

CAMPOS_REQUERIDOS = [
    "comuna",
    "operacion",
]

# Preguntas específicas por campo
PREGUNTAS = {
    "comuna": "¿En qué comuna buscas la propiedad?",
    "operacion": "¿La buscas en venta o en arriendo?",
    "precio_max_clp": "¿Cuál es tu presupuesto máximo en pesos?",
    "precio_max_uf": "¿Cuál es tu presupuesto máximo en UF?",
}

# =========================
# EXTRACCIÓN BÁSICA
# =========================

def extraer_comuna(texto: str):
    comunas = [
        "providencia", "las condes", "vitacura", "ñuñoa",
        "la reina", "santiago", "macul", "peñalolén"
    ]
    for c in comunas:
        if c in texto:
            return c.title()
    return None


def extraer_operacion(texto: str):
    if "arriendo" in texto or "arrendar" in texto:
        return "arriendo"
    if "venta" in texto or "vender" in texto:
        return "venta"
    return None


def extraer_precio(texto: str):
    """
    Detecta precios tipo:
    - 900.000
    - 900000
    - 900 mil
    - 10.000 uf
    """
    texto = texto.lower()

    # UF
    match_uf = re.search(r"([\d\.]+)\s*uf", texto)
    if match_uf:
        valor = match_uf.group(1).replace(".", "")
        return {
            "precio_max_uf": int(valor)
        }

    # CLP
    match_clp = re.search(r"([\d\.]+)", texto)
    if match_clp:
        valor = match_clp.group(1).replace(".", "")
        if len(valor) >= 5:
            return {
                "precio_max_clp": int(valor)
            }

    return {}


# =========================
# INTERPRETADOR PRINCIPAL
# =========================

def interpret_message(message: str, contexto_anterior: dict | None = None) -> dict:
    """
    Interpreta el mensaje del usuario de forma acumulativa.
    """

    texto = message.lower().strip()
    filtros = contexto_anterior.copy() if contexto_anterior else {}

    # -------------------------
    # EXTRAER INTENCIÓN
    # -------------------------

    comuna = extraer_comuna(texto)
    if comuna:
        filtros["comuna"] = comuna

    operacion = extraer_operacion(texto)
    if operacion:
        filtros["operacion"] = operacion

    precio = extraer_precio(texto)
    filtros.update(precio)

    # -------------------------
    # VALIDAR CAMPOS CLAVE
    # -------------------------

    faltantes = []

    for campo in CAMPOS_REQUERIDOS:
        if campo not in filtros:
            faltantes.append(campo)

    # -------------------------
    # DECISIÓN FINAL
    # -------------------------

    # Caso 1: faltan campos → preguntar algo CONCRETO
    if faltantes:
        campo = faltantes[0]
        return {
            "action": "ask",
            "message": PREGUNTAS.get(
                campo,
                "¿Puedes darme un poco más de información?"
            ),
            "missing_fields": faltantes,
            "filters_partial": filtros,
        }

    # Caso 2: ya tenemos lo mínimo → buscar
    return {
        "action": "search",
        "filters": filtros
    }
