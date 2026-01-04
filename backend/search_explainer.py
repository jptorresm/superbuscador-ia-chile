from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
Eres un asesor inmobiliario experto en Santiago de Chile.
Tu tarea es explicar resultados de búsqueda inmobiliaria de forma clara,
humana y breve, como si ayudaras a una persona real a decidir.

Reglas:
- No repitas filtros literalmente
- No enumeres propiedades
- Explica si el resultado es poco, normal o ajustado
- Da contexto de mercado
- Usa máximo 4 frases
- Tono cercano, no técnico
"""

def explain_results(query: str, filters: dict, results: list) -> str:
    if not results:
        return (
            "No encontré resultados que coincidan exactamente con tu búsqueda. "
            "Esto suele indicar que los criterios son muy restrictivos para el mercado actual. "
            "Podrías ampliar el presupuesto o considerar comunas cercanas."
        )

    prompt = f"""
Búsqueda del usuario:
"{query}"

Filtros interpretados:
{filters}

Cantidad de resultados:
{len(results)}
"""

    try:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        return resp.output_text.strip()

    except Exception as e:
        print("⚠️ explain_results error:", e)
        return "Encontré algunas opciones que coinciden con lo que buscas."
