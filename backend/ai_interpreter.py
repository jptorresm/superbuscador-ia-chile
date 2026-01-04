import json
import re
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
- NO expliques nada, solo devuelve JSON.
"""

# 🔢 Normalización determinística de precios
def normalize_price(text: str) -> int | None:
    t = text.lower()

    # 2 MM, 2mm, 2 millones
    mm_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(mm|millones|millon)', t)
    if mm_match:
        value = float(mm_match.group(1).replace(",", "."))
        return int(value * 1_000_000)

    # $2.000.000 o 2.000.000
    money_match = re.search(r'\$?\s*(\d{1,3}(?:[.,]\d{3})+)', t)
    if money_match:
        return int(
            money_match.group(1)
            .replace(".", "")
            .replace(",", "")
        )

    return None


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

        action = data.get("action")
        filters = data.get("filters", {}) or {}
        missing = data.get("missing_fields", []) or []

        # 🔒 Refuerzo backend: precio desde el texto original
        price_from_text = normalize_price(text)
        if price_from_text:
            filters["price_max"] = price_from_text

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
