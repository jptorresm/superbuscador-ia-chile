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
    action = decision.get("action")

    return {
        "action": action,
        "decision": decision
    }


# 🟡 CASO: FALTAN DATOS
if action == "ask":
    return {
        "type": "question",
        "message": decision.get("message"),
        "missing_fields": decision.get("missing_fields", []),
        "filters_partial": decision.get("filters_partial", {}),
    }

# 🟢 CASO: BUSCAR
if action == "search":
    results = search_properties(**decision.get("filters", {}))

    return {
        "type": "results",
        "results": results,
        "count": len(results),
        "filters": decision.get("filters", {}),
    }

# 🔴 CASO: ERROR / FALLBACK
return {
    "type": "error",
    "message": decision.get("message", "No pude procesar la solicitud"),
}
