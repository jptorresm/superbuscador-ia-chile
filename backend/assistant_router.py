from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties
from backend.search_explainer import explain_results

router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str
    context: dict | None = None


@router.post("/assistant")
def assistant(req: AssistantRequest):

    decision = interpret_message(
        req.message,
        contexto_anterior=req.context
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
       except Exception as e:
        return {
        "type": "results",
        "summary": "No se pudieron filtrar resultados con los criterios actuales.",
        "count": 0,
        "results": [],
        "filters": raw_filters,
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
        "message": "No pude interpretar la solicitud."
    }
