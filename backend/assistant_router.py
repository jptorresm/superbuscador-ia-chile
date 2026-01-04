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

    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message"),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
        }

    if action == "search":
        filters = decision.get("filters", {})
        results = search_properties(**filters)

        return {
            "type": "results",
            "count": len(results),
            "results": results,
            "filters": filters,
        }

    return {
        "type": "error",
        "message": decision.get("message", "No pude procesar la solicitud"),
    }
