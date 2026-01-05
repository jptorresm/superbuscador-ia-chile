import re
import unicodedata


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8").lower()


def interpret_message(message: str) -> dict:
    text = normalize(message)

    filters = {}
    missing_fields = []

    # -------------------------
    # OPERACIÓN
    # -------------------------
    if "venta" in text or "vender" in text:
        operacion = "venta"
    elif "arriendo" in text or "arrendar" in text:
        operacion = "arriendo"
    else:
        missing_fields.append("operacion")
        operacion = None

    if operacion:
        filters["operacion"] = operacion

    # -------------------------
    # COMUNA (básico, luego mejoramos)
    # -------------------------
    comunas = [
        "las condes", "vitacura", "lo barnechea",
        "nunoa", "providencia", "la reina", "santiago"
    ]

    for c in comunas:
        if c in text:
            filters["comuna"] = c.title()
            break

    if "comuna" not in filters:
        missing_fields.append("comuna")

    # -------------------------
    # PRECIO
    # -------------------------
    # UF
    match_uf = re.search(r"(\d{1,3}(?:\.\d{3})*)\s*uf", text)
    # CLP
    match_clp = re.search(r"(\d{3,})\s*(millones|mm|m)", text)

    if match_uf:
        value = int(match_uf.group(1).replace(".", ""))
        if operacion == "venta":
            filters["precio_max_uf"] = value
        else:
            # UF en arriendo es raro → ignoramos
            pass

    elif match_clp:
        value = int(match_clp.group(1)) * 1_000_000
        filters["precio_max_clp"] = value

    # -------------------------
    # DECISIÓN
    # -------------------------
    if missing_fields:
        return {
            "action": "ask",
            "message": "¿Puedes indicar comuna y tipo de operación?",
            "missing_fields": missing_fields,
            "filters_partial": filters,
        }

    return {
        "action": "search",
        "filters": filters,
    }
