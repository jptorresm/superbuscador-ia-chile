from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties
from backend.search_explainer import explain_results

router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str


@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint IA-first:
    - La IA interpreta
    - El sistema ejecuta
    - La IA explica
    """

    decision = interpret_message(req.message)
    action = decision.get("action")

    # 🟡 CASO: FALTAN DATOS
    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message"),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
            "confidence": decision.get("confidence"),
        }

    # 🟢 CASO: BUSCAR
    if action == "search":
        filters = decision.get("filters", {}) or {}

        # Ejecutar búsqueda (el sistema NO piensa)
        results = search_properties(**filters)

        # Explicación IA (valor diferencial)
        summary = explain_results(
            query=req.message,
            filters=filters,
            results=results,
            assumptions=decision.get("assumptions", []),
            confidence=decision.get("confidence"),
        )

        return {
            "type": "results",
            "summary": summary,
            "confidence": decision.get("confidence"),
            "assumptions": decision.get("assumptions", []),
            "filters": filters,
            "count": len(results),
            "results": results,
        }

    # 🔴 FALLBACK (nunca debería pasar)
    return {
        "type": "error",
        "message": "No pude procesar la solicitud.",
    }
