import re


# =========================
# CONFIGURACIÓN
# =========================

OPERADORES_VALIDOS = [
    "comuna",
    "operacion",
    "precio_min_uf",
    "precio_max_uf",
    "precio_min_clp",
    "precio_max_clp",
    "dormitorios_min",
    "banos_min",
    "amenities",
]


# =========================
# UTILIDADES
# =========================

def find_number(text):
    match = re.search(r"(\d{1,3}(?:[\.,]\d{3})+|\d+)", text)
    if not match:
        return None
    return int(match.group(1).replace(".", "").replace(",", ""))


def normalize_text(text: str) -> str:
    return text.lower().strip()


# =========================
# INTERPRETADOR PRINCIPAL
# =========================

def interpret_message(message: str) -> dict:
    """
    Interpreta lenguaje natural y decide:
    - preguntar (ask)
    - buscar (search)
    """

    text = normalize_text(message)

    filters = {}
    missing_fields = []

    # -------------------------
    # OPERACIÓN
    # -------------------------
    if "venta" in text:
        filters["operacion"] = "venta"
    elif "arriendo" in text or "alquiler" in text:
        filters["operacion"] = "arriendo"
    else:
        missing_fields.append("operacion")

    # -------------------------
    # COMUNA (simple, explícito)
    # -------------------------
    comunas = [
        "las condes",
        "vitacura",
        "providencia",
        "ñuñoa",
        "la reina",
        "lo barnechea",
        "santiago",
    ]
    for comuna in comunas:
        if comuna in text:
            filters["comuna"] = comuna.title()
            break

    if "comuna" not in filters:
        missing_fields.append("comuna")

    # -------------------------
    # PRECIO
    # -------------------------
    number = find_number(text)

    if number:
        if "uf" in text:
            if "min" in text or "desde" in text:
                filters["precio_min_uf"] = number
            elif "max" in text or "hasta" in text or "menos de" in text:
                filters["precio_max_uf"] = number
            else:
                return {
                    "action": "ask",
                    "message": f"¿Ese precio ({number} UF) es mínimo o máximo?",
                    "missing_fields": ["precio_rango"],
                    "filters_partial": filters,
                }

        if "$" in text or "clp" in text or "pesos" in text:
            if "min" in text or "desde" in text:
                filters["precio_min_clp"] = number
            elif "max" in text or "hasta" in text:
                filters["precio_max_clp"] = number
            else:
                return {
                    "action": "ask",
                    "message": f"¿Ese precio (${number}) es mínimo o máximo?",
                    "missing_fields": ["precio_rango"],
                    "filters_partial": filters,
                }

    # -------------------------
    # DECISIÓN FINAL
    # -------------------------
    if missing_fields:
        return {
            "action": "ask",
            "message": "Necesito un poco más de información para buscar correctamente.",
            "missing_fields": missing_fields,
            "filters_partial": filters,
        }

    # Limpiar filtros no válidos
    filters = {k: v for k, v in filters.items() if k in OPERADORES_VALIDOS}

    return {
        "action": "search",
        "filters": filters,
    }
