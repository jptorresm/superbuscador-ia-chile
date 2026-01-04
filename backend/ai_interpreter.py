import json
from pathlib import Path
from openai import OpenAI

client = OpenAI()

# Cargar prompt
PROMPT_PATH = Path("prompts/interpretar_busqueda.md")
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

# JSON Schema estricto
SCHEMA = {
    "name": "RealEstateIntent",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "action": {"type": "string", "enum": ["ask", "search"]},
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


def interpret_message(text: str) -> dict:
    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
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

        # 🔑 Forma correcta de extraer el JSON
        # Responses API devuelve una lista estructurada en resp.output
        for item in resp.output:
            if item["type"] == "output_text":
                return json.loads(item["text"])

        # Si no encontramos output_text válido
        raise ValueError("No JSON output_text found in OpenAI response")

    except Exception as e:
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
        }
