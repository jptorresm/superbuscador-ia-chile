from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
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
# PRE-FLIGHT CORS (CLAVE)
# =========================

@router.options("/assistant")
async def assistant_options():
    return JSONResponse(
        status_code=200,
        content={"ok": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


# =========================
# ENDPOINT PRINCIPAL
# =========================

@router.post("/assistant")
async def assistant(req: AssistantRequest, request: Request):

    try:
        decision = interpret_message(
            req.message,
            contexto_anterior=req.context
        ) or {}
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "type": "error",
                "message": "Error interpretando mensaje",
                "detail": str(e),
            },
            headers={
                "Access-Control-Allow-Origin": "*",
            },
        )

    action = decision.get("action")

    if action == "ask":
        return JSONResponse(
            status_code=200,
            content={
                "type": "question",
                "message": decision.get("message"),
                "missing_fields": decision.get("missing_fields", []),
                "filters_partial": decision.get("filters_partial", {}),
            },
            headers={
                "Access-Control-Allow-Origin": "*",
            },
        )

    if action == "search":
        raw_filters = decision.get("filters", {})

        try:
            results = search_properties(**raw_filters)
        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={
                    "type": "error",
                    "message": "Error en búsqueda",
                    "detail": str(e),
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                },
            )

        try:
            summary = explain_results(
                query=req.message,
                filters=raw_filters,
                results=results,
            )
        except Exception:
            summary = ""

        return JSONResponse(
            status_code=200,
            content={
                "type": "results",
                "summary": summary,
                "count": len(results),
                "results": results,
                "filters": raw_filters,
            },
            headers={
                "Access-Control-Allow-Origin": "*",
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "type": "error",
            "message": "Acción no reconocida",
        },
        headers={
            "Access-Control-Allow-Origin": "*",
        },
    )
