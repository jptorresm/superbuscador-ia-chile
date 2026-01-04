from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties

router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str


@router.post("/assistant")
def assistant(req: AssistantRequest):
    decision = interpret_message(req.message)
    action = decision.get("action")

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
        filters = decision.get("filters", {}) or {}

        # 🔁 Mapear filtros IA → search_engine
        mapped_filters = {
            "comuna": filters.get("comuna"),
            "operacion": filters.get("operation"),   # 👈 CLAVE
            "precio_max": filters.get("price_max"),
            "amenities": filters.get("amenities"),
        }

        results = search_properties(**mapped_filters)

        return {
            "type": "results",
            "count": len(results),
            "results": results,
            "filters": mapped_filters,
        }

    # 🔴 CASO: ERROR / FALLBACK
    return {
        "type": "error",
        "message": decision.get("message", "No pude procesar la solicitud"),
    }
