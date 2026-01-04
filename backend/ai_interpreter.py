import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
Eres un Asesor Inmobiliario Digital experto en el mercado inmobiliario chileno.

Interpretas búsquedas inmobiliarias en lenguaje natural y las transformas
en filtros claros para un sistema de búsqueda.

Debes pensar como un corredor humano, no como un parser técnico.

Devuelve SIEMPRE un JSON válido, sin texto adicional.

Formato esperado:

{
  "action": "search" | "ask",
  "filters": {
    "operacion": "venta" | "arriendo" | null,
    "tipo": "casa" | "departamento" | null,
    "comuna": string | null,
    "precio_max": number | null
  },
  "assumptions": [string],
  "missing_fields": [string],
  "confidence": number
}

Reglas:
- Usa action="search" si la intención es suficientemente clara.
- Usa action="ask" si falta información crítica.
- Convierte precios como "2 MM", "2 millones", "2000000" a CLP entero.
- Reconoce comunas de Chile aunque estén mal escritas.
- No inventes información.
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

        # Normalización mínima defensiva
        action = data.get("action")
        filters = data.get("filters", {}) or {}
        assumptions = data.get("assumptions", []) or []
        missing = data.get("missing_fields", []) or []
        confidence = data.get("confidence")

        if action == "ask":
            return {
                "action": "ask",
                "message": "Necesito un poco más de información para continuar.",
                "missing_fields": missing,
                "filters_partial": filters,
                "assumptions": assumptions,
                "confidence": confidence,
            }

        return {
            "action": "search",
            "filters": filters,
            "assumptions": assumptions,
            "confidence": confidence,
        }

    except Exception as e:
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
            "assumptions": [],
            "confidence": 0.0,
        }
