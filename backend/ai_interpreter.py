import json
from pathlib import Path
from openai import OpenAI

# Ruta al prompt
PROMPT_PATH = Path("prompts/interpretar_busqueda.md")

# Cliente OpenAI (usa la API key del entorno)
client = OpenAI()

def interpret_query(query: str) -> dict:
    """
    Toma una búsqueda en texto libre y devuelve
    un diccionario con filtros estructurados.
    """
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    # Convertimos el texto JSON a dict Python
    return json.loads(content)
