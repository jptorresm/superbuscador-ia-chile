import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
Eres un asistente que interpreta búsquedas inmobiliarias en Chile.

Debes devolver SIEMPRE un JSON válido, sin texto adicional.

Formato esperado:
{
  "action": "search" | "ask",
  "filters": {
    "operation": "venta" | "arriendo" | null,
    "property_type": "casa" | "departamento" | null,
    "comuna": string | null,
    "price_max": number | null
  },
  "missing_fields": [string]
}

Reglas:
- Si tienes suficiente información para buscar, action = "search".
- Si falta información clave, action = "ask" y completa missing_fields.
- Si el usuario menciona una comuna conocida de Chile, interprétala correctamente.
- Si el usuario menciona precios como "2 MM", "2 millones", "2000000", conviértelos a entero CLP.
"""

def interpret_message(text: str) -> dict:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        content = completion.choices[0].message.content
        data = json.loads(content)

        # Normalización defensiva
        action = data.get("action")
        filters = data.get("filters", {}) or {}
        missing = data.get("missing_fields", []) or []

        if action == "ask":
            return {
                "action": "ask",
                "message": "Me falta información para continuar.",
                "missing_fields": missing,
                "filters_partial": filters,
            }

        return {
            "action": "search",
            "filters": filters,
        }

    except Exception as e:
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
        }
