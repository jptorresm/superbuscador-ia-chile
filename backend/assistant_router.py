from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["assistant"])


class AssistantRequest(BaseModel):
    message: str


@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint IA-first BLINDADO:
    - Nunca lanza 500
    - Siempre devuelve JSON
    - Permite que CORS funcione
    """

    try:
        from backend.ai_interpreter import interpret_message
        decision = interpret_message(req.message)
    except Exception as e:
        print("❌ ERROR interpret_message:", repr(e))
        return {
            "type": "error",
            "message": "Error interpretando la búsqueda.",
        }

    action = decision.get("action")

    # ─────────────────────────────
    # CASO: FALTAN DATOS
    # ─────────────────────────────
    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message", "Necesito más información."),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
            "confidence": decision.get("confidence"),
        }

    # ─────────────────────────────
    # CASO: BUSCAR
    # ─────────────────────────────
    if action == "search":
        try:
            from backend.search_engine import search_properties
            filters = decision.get("filters", {}) or {}

            # 🔁 MAPEO DEFENSIVO
            mapped_filters = {
                "comuna": filters.get("comuna"),
                "operacion": filters.get("operacion"),
                "precio_max": filters.get("precio_max"),
            }

            results = search_properties(**mapped_filters)
        except Exception as e:
            print("❌ ERROR search_properties:", repr(e))
            return {
                "type": "error",
                "message": "Error ejecutando la búsqueda.",
            }

        # Explicación IA (si falla, no rompe)
        summary = None
        try:
            from backend.search_explainer import explain_results
            summary = explain_results(
                query=req.message,
                filters=mapped_filters,
                results=results,
                assumptions=decision.get("assumptions", []),
                confidence=decision.get("confidence"),
            )
        except Exception as e:
            print("⚠️ ERROR explain_results:", repr(e))

        return {
            "type": "results",
            "summary": summary,
            "confidence": decision.get("confidence"),
            "assumptions": decision.get("assumptions", []),
            "filters": mapped_filters,
            "count": len(results),
            "results": results,
        }

    # ─────────────────────────────
    # FALLBACK FINAL
    # ─────────────────────────────
    return {
        "type": "error",
        "message": "No pude procesar la solicitud.",
    }
