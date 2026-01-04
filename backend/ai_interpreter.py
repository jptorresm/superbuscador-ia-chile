import json
from pathlib import Path
from openai import OpenAI

# Cliente OpenAI (usa OPENAI_API_KEY del entorno)
client = OpenAI()

# -------------------------------------------------
# Cargar prompt de forma robusta (funciona en Render)
# -------------------------------------------------
SYSTEM_PROMPT = """
Eres un asistente que interpreta búsquedas inmobiliarias en Chile.
Devuelve SOLO un JSON válido.

Campos:
- action: "ask" o "search"
- filters: objeto con posibles claves:
  - comuna
  - operation ("venta" o "arriendo")
  - property_type ("casa" o "departamento")
  - price_max (entero CLP)

Si puedes buscar, action = "search".
Si falta información crítica, action = "ask".
"""


# -------------------------------------------------
# JSON Schema estricto para Structured Outputs
# -------------------------------------------------
SCHEMA = {
    "name": "RealEstateIntent",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {
                "type": "string",
                "enum": ["ask", "search"],
            },
            "message": {"type": "string"},
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
            },
            "filters_partial": {"type": "object"},
            "filters": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operation": {
                        "type": ["string", "null"],
                        "enum": ["venta", "arriendo", None],
                    },
                    "property_type": {
                        "type": ["string", "null"],
                        "enum": ["casa", "departamento", None],
                    },
                    "comuna": {"type": ["string", "null"]},
                    "price_max": {"type": ["integer", "null"]},
                },
            },
        },
        "required": ["action"],
    },
}

# -------------------------------------------------
# Interpreter principal
# -------------------------------------------------
def interpret_message(text: str) -> dict:
    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "json_schema": SCHEMA,
                    "strict": True,
                }
            },
        )

        # ---------------------------------------------
        # Extracción robusta del JSON desde Responses API
        # ---------------------------------------------
        for item in resp.output:
            # Caso 1: output_text directo
            if item.get("type") == "output_text" and "text" in item:
                return json.loads(item["text"])

            # Caso 2: message → content → output_text
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text" and "text" in part:
                        return json.loads(part["text"])

        # Si OpenAI respondió pero no entregó JSON usable
        raise ValueError("No valid JSON found in OpenAI response")

    except Exception as e:
        # Fallback defensivo (el sistema nunca se cae)
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
        }
