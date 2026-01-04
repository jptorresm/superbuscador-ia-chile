import json
from pathlib import Path
from openai import OpenAI

# Cliente OpenAI (usa OPENAI_API_KEY del entorno)
client = OpenAI()

# Cargar prompt desde archivo
PROMPT_PATH = Path("prompts/interpretar_busqueda.md")
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


def interpret_message(text: str) -> dict:
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            text={
                "format": {
                    "type": "json"
                }
            }
        )

        return json.loads(response.output_text)

    except Exception as e:
        # Fallback defensivo (NUNCA romper el assistant)
        return {
            "action": "ask",
            "message": "Tuve un problema interpretando el mensaje. ¿Puedes reformularlo?",
            "missing_fields": [],
            "filters_partial": {},
            "error": str(e),
        }

