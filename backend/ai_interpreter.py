import re

# =========================
# DEFINICIÓN DECLARATIVA
# =========================

FIELD_DEFINITIONS = {
    "comuna": {
        "required": True,
        "priority": 1,
        "question": "¿En qué comuna buscas la propiedad?",
    },
    "operacion": {
        "required": True,
        "priority": 2,
        "question": "¿La buscas en venta o en arriendo?",
    },
    "precio_max_clp": {
        "required": False,
        "priority": 3,
        "question": "¿Cuál es tu presupuesto máximo?",
    },
    "precio_max_uf": {
        "required": False,
        "priority": 3,
        "question": "¿Cuál es tu presupuesto máximo en UF?",
    },
    # 👇 futuros campos se agregan AQUÍ, sin tocar lógica
    # "amoblado": {...}
    # "mascotas": {...}
}

# =========================
# EXTRACCIÓN BÁSICA
# =========================

def extract_comuna(text):
    comunas = [
        "providencia", "las condes", "vitacura", "ñuñoa",
        "la reina", "macul", "peñalolén", "santiago"
    ]
    for c in comunas:
        if c in text:
            return c.title()
    return None


def extract_operacion(text):
    if "arriendo" in text:
        return "arriendo"
    if "venta" in text:
        return "venta"
    return None


def extract_precio(text):
    text = text.lower()

    match_uf = re.search(r"([\d\.]+)\s*uf", text)
    if match_uf:
        return {"precio_max_uf": int(match_uf.group(1).replace(".", ""))}

    match_clp = re.search(r"([\d\.]{5,})", text)
    if match_clp:
        return {"precio_max_clp": int(match_clp.group(1).replace(".", ""))}

    return {}

# =========================
# INTERPRETADOR GENÉRICO
# =========================

def interpret_message(message: str, contexto_anterior: dict | None = None) -> dict:
    text = message.lower().strip()
    context = contexto_anterior.copy() if contexto_anterior else {}

    # --- extracción incremental ---
    comuna = extract_comuna(text)
    if comuna:
        context["comuna"] = comuna

    operacion = extract_operacion(text)
    if operacion:
        context["operacion"] = operacion

    context.update(extract_precio(text))

    # --- decidir siguiente paso ---
    pending = []

    for field, meta in FIELD_DEFINITIONS.items():
        if field not in context:
            if meta["required"]:
                pending.append((meta["priority"], field))
            else:
                pending.append((meta["priority"] + 10, field))

    if pending:
        pending.sort()
        next_field = pending[0][1]
        return {
            "action": "ask",
            "message": FIELD_DEFINITIONS[next_field]["question"],
            "missing_fields": [next_field],
            "filters_partial": context,
        }

    # --- listo para buscar ---
    return {
        "action": "search",
        "filters": context,
    }
