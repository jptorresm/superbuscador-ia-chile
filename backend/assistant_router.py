from fastapi import APIRouter
from pydantic import BaseModel

from backend.ai_interpreter import interpret_message
from backend.search_engine import search_properties
from backend.search_explainer import explain_results

router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str
    context: dict | None = None


SEARCH_FIELDS = {
    "comuna",
    "operacion",
    "precio_max_uf",
    "precio_max_clp",
    "amenities",
}


@router.post("/assistant")
def assistant(req: AssistantRequest):

    try:
        decision = interpret_message(
            req.message,
            contexto_anterior=req.context
        ) or {}
    except Exception:
        return {
            "type": "results",
            "summary": "No se pudo interpretar la búsqueda.",
            "count": 0,
            "results": [],
            "filters": req.context or {},
        }

    action = decision.get("action")

    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message"),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
        }

    if action == "search":
        raw_filters = decision.get("filters", {})

        filters = {
            k: v for k, v in raw_filters.items()
            if k in SEARCH_FIELDS and v is not None
        }

        try:
            results = search_properties(**filters)
        except Exception:
            results = []

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
            "filters": raw_filters,
        }

    return {
        "type": "results",
        "summary": "No se encontraron resultados.",
        "count": 0,
        "results": [],
        "filters": req.context or {},
    }
