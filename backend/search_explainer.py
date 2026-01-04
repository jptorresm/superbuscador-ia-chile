from openai import OpenAI
import json

client = OpenAI()

SYSTEM_PROMPT = """
Eres un asesor inmobiliario experto en el mercado chileno.

Tu tarea es explicar los resultados de una búsqueda inmobiliaria
como lo haría un corredor profesional: claro, humano y orientado a ayudar.

No enumeres resultados ni repitas datos técnicos.
Analiza, contextualiza y recomienda.

---

DEBES:
- Explicar cómo se interpretó la búsqueda
- Leer la cantidad y tipo de resultados
- Comentar brevemente el contexto (escasez, rango de precios, tipo de oferta)
- Sugerir un siguiente paso útil

TONO:
- Cercano
- Profesional
- Claro
- Sin jerga técnica
- Sin mencionar IA, modelos ni sistemas

EXTENSIÓN:
- 3 a 5 frases máximo
"""

def explain_results(
    query: str,
    filters: dict,
    results: list,
    assumptions: list = None,
    confidence: float | None = None,
) -> str:
    try:
        payload = {
            "query": query,
            "filters": filters,
            "result_count": len(results),
            "sample_results": results[:3],  # solo contexto, no listado
            "assumptions": assumptions or [],
            "confidence": confidence,
        }

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Explica los resultados de esta búsqueda inmobiliaria:\n\n"
                        + json.dumps(payload, ensure_ascii=False)
                    ),
                },
            ],
            temperature=0.4,
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("ERROR explain_results:", repr(e))
        return (
            "Encontré algunas opciones que coinciden con tu búsqueda. "
            "Si quieres, puedo ayudarte a ajustar los criterios o comparar alternativas."
        )
