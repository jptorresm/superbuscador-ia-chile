from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties
from backend.search_explainer import explain_results

router = APIRouter(tags=["assistant"])


# =========================
# MODELO
# =========================

class AssistantRequest(BaseModel):
    message: str


# =========================
# ENDPOINT ÚNICO
# =========================

@router.post("/assistant")
async def assistant(req: AssistantRequest):
    try:
        decision = interpret_message(req.message)
    except Exception as e:
        return {
            "type": "error",
            "message": "Error interpretando el mensaje",
            "detail": str(e),
        }

    if not isinstance(decision, dict):
        return {
            "type": "error",
            "message": "Respuesta inválida del intérprete",
            "debug": decision,
        }

    action = decision.get("action")

    if action == "ask":
        return {
            "type": "question",
            "message": decision.get(
                "message",
                "¿Puedes darme más detalles?"
            ),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
        }

    if action == "search":
        filters = decision.get("filters", {})

        try:
            results = search_properties(**filters)
        except Exception as e:
            return {
                "type": "error",
                "message": "Error ejecutando búsqueda",
                "detail": str(e),
            }

        try:
            summary = explain_results(
                query=req.message,
                filters=filters,
                results=results,
            )
        except Exception:
            summary = ""

        return {
            "type": "results",
            "summary": summary,
            "count": len(results),
            "results": results,
            "filters": filters,
        }

    return {
        "type": "error",
        "message": "No pude procesar la solicitud",
        "debug": decision,
    }
