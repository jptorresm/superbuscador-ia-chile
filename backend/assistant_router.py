from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties
from backend.search_explainer import explain_results

router = APIRouter(tags=["assistant"])


# =========================
# MODELOS
# =========================

class AssistantRequest(BaseModel):
    message: str
    context: dict | None = None


# =========================
# LÓGICA PURA (CLAVE)
# =========================

async def run_assistant_logic(payload: dict) -> dict:
    message = payload.get("message", "")
    context = payload.get("context")

    decision = interpret_message(
        message,
        contexto_anterior=context
    ) or {}

    action = decision.get("action")

    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message"),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
        }

    if action == "search":
        filters = decision.get("filters", {})

        try:
            results = search_properties(**filters)
        except Exception:
            results = []

        try:
            summary = explain_results(
                query=message,
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
    }


# =========================
# ENDPOINT HTTP
# =========================

@router.post("/assistant")
async def assistant(req: AssistantRequest):
    return await run_assistant_logic(req.dict())
