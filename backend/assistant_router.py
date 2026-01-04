from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties  # ajusta si el nombre difiere

router = APIRouter(prefix="", tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str


@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint conversacional:
    - interpreta el mensaje
    - decide preguntar o buscar
    - traduce la decisión a formato frontend
    """

    decision = interpret_message(req.message)

    # 🟡 CASO: FALTAN DATOS → PREGUNTAR
    if decision.action == "ask":
        return {
            "type": "question",
            "message": decision.message,
            "missing_fields": decision.missing_fields,
            "filters_partial": decision.filters_partial
        }

    # 🟢 CASO: DATOS SUFICIENTES → BUSCAR
    if decision.action == "search":
        results = search_properties(decision.filters)

        return {
            "type": "results",
            "results": results,
            "count": len(results),
            "filters": decision.filters
        }

    # 🔴 CASO: ERROR / DESCONOCIDO
    return {
        "type": "error",
        "message": decision.message or "No pude procesar la solicitud"
    }
