import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
Eres un asistente experto en interpretación de búsquedas inmobiliarias en Chile.

Tu tarea es interpretar lo que el usuario quiere buscar y transformar su mensaje
en una instrucción clara y ejecutable para un sistema de búsqueda de propiedades.

Debes pensar como un asesor inmobiliario humano, no como un parser técnico.

---

OBJETIVO

Dado un mensaje en lenguaje natural, debes:

1. Entender la intención real del usuario
2. Inferir correctamente los filtros de búsqueda
3. Asumir valores razonables cuando sea posible
4. Explicar tus supuestos
5. Decidir si se puede buscar o si falta información crítica

---

FORMATO DE RESPUESTA (OBLIGATORIO)

Debes responder SIEMPRE con un JSON válido, sin texto adicional fuera del JSON.

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

---

REGLAS IMPORTANTES

- Si tienes información suficiente para buscar, usa action = "search"
- Si falta información crítica (por ejemplo operación o comuna), usa action = "ask"
- Interpreta precios como "2 MM", "2 millones", "2.000.000" como pesos chilenos
- Prefiere asumir de forma razonable antes que bloquear
- Registra todos los supuestos relevantes en "assumptions"
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

        # Validación mínima (infraestructura, no lógica)
        action = data.get("action")
        filters = data.get("filters", {}) or {}

        if action == "ask":
            return {
                "action": "ask",
                "message": "Necesito un poco más de información para continuar.",
                "missing_fields": data.get("missing_fields", []),
                "filters_partial": filters,
            }

        return {
            "action": "search",
            "filters": filters,
            "assumptions": data.get("assumptions", []),
            "confidence": data.get("confidence", 0.5),
        }

    except Exception as e:
        print("ERROR interpret_message:", repr(e))

        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
        }

