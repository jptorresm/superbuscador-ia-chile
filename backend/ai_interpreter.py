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

        # 🔑 Extracción ROBUSTA del JSON desde Responses API
        for item in resp.output:
            # Caso 1: output_text directo
            if item.get("type") == "output_text" and "text" in item:
                return json.loads(item["text"])

            # Caso 2: message → content → output_text
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text" and "text" in part:
                        return json.loads(part["text"])

        # Si llegamos aquí, OpenAI respondió pero no con JSON usable
        raise ValueError("No valid JSON found in OpenAI response output")

    except Exception as e:
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
        }
