import json
from pathlib import Path
from openai import OpenAI

# Ruta al prompt
PROMPT_PATH = Path("prompts/interpretar_busqueda.md")

# Cliente OpenAI (usa la API key del entorno)
client = OpenAI()

def interpret_message(text: str) -> dict:
    text_l = text.lower()

    filters = {
        "operation": "arriendo" if "arriendo" in text_l else ("venta" if "venta" in text_l else None),
        "property_type": "casa" if "casa" in text_l else ("departamento" if "depto" in text_l or "departamento" in text_l else None),
        "comuna": "La Reina" if "la reina" in text_l else None,
        "price_max": None,
    }

    missing = [k for k, v in filters.items() if v is None]

    if missing:
        return {
            "action": "ask",
            "message": f"Me falta: {', '.join(missing)}. ¿Me lo indicas?",
            "missing_fields": missing,
            "filters_partial": filters
        }

    return {
        "action": "search",
        "filters": filters
    }
