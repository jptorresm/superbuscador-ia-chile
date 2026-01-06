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
# LÓGICA PURA (BLINDADA)
# =========================

async def run_assistant_logic(payload: dict) -> dict:
    try:
        message = payload.get("message", "")
        context = payload.get("context")

        decision = interpret_message(
            message,
            contexto_anterior=context
        )

        if not isinstance(decision, dict):
            raise ValueError("interpret_message no retornó dict")

        action = decision.get("action")

        # -------------------------
        # CASO: PREGUNTAR
        # -------------------------
        if action == "ask":
            return {
                "type": "question",
                "message": decision.get("message", "¿Puedes darme más información?"),
                "missing_fields": decision.get("missing_fields", []),
                "filters_partial": decision.get("filters_partial", {}),
            }

        # -------------------------
        # CASO: BUSCAR
        # -------------------------
        if action == "search":
            filters = decision.get("filters", {})

            try:
                results = search_properties(**filters)
            except Exception as e:
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

        # -------------------------
        # FALLBACK
        # -------------------------
        return {
            "type": "error",
            "message": "No pude interpretar la solicitud",
            "debug": decision,
        }

    except Exception as e:
        # ⛔ JAMÁS LANZAMOS EXCEPCIÓN
        return {
            "type": "error",
            "message": "Error interno del asistente",
            "detail": str(e),
        }


# =========================
# ENDPOINT HTTP
# =========================

@router.post("/assistant")
async def assistant(req: AssistantRequest):
    return await run_assistant_logic(req.dict())
