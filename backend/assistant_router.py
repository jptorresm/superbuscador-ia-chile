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


# =========================
# ENDPOINT PRINCIPAL
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint conversacional único.
    - La IA interpreta intención y filtros
    - Decide preguntar o buscar
    - Ejecuta búsqueda real
    - Devuelve resultados estructurados
    """

    # 1️⃣ Interpretación IA
    decision = interpret_message(req.message) or {}
    action = decision.get("action")

    # -------------------------
    # 🟡 CASO: FALTAN DATOS
    # -------------------------
    if action == "ask":
        return {
            "type": "question",
            "message": decision.get("message", "¿Puedes darme más información?"),
            "missing_fields": decision.get("missing_fields", []),
            "filters_partial": decision.get("filters_partial", {}),
        }

    # -------------------------
    # 🟢 CASO: BUSCAR
    # -------------------------
    if action == "search":
        raw_filters = decision.get("filters") or {}

        # 🔁 Mapeo explícito (sin nombres ambiguos)
        mapped_filters = {
            "comuna": raw_filters.get("comuna"),
            "operacion": raw_filters.get("operacion"),
            "precio_max": raw_filters.get("precio_max"),
            "amenities": raw_filters.get("amenities"),
        }

        # 🧹 Limpiar filtros vacíos
        mapped_filters = {
            k: v for k, v in mapped_filters.items()
            if v is not None and v != ""
        }

        # 🛑 Si no hay filtros útiles, volver a preguntar
        if not mapped_filters:
            return {
                "type": "question",
                "message": "¿En qué comuna y para qué tipo de operación buscas?",
                "missing_fields": ["comuna", "operacion"],
                "filters_partial": {},
            }

        # 🔍 Ejecutar búsqueda REAL
        try:
            results = search_properties(**mapped_filters)
        except Exception as e:
            # 🔴 Error real visible (no oculto)
            return {
                "type": "error",
                "message": f"Error ejecutando la búsqueda: {str(e)}",
            }

        # 🧠 Explicación (no bloqueante)
        try:
            summary = explain_results(
                query=req.message,
                filters=mapped_filters,
                results=results,
            )
        except Exception:
            summary = ""

        return {
            "type": "results",
            "summary": summary,
            "count": len(results),
            "results": results,
            "filters": mapped_filters,
        }

    # -------------------------
    # 🔴 FALLBACK FINAL
    # -------------------------
    return {
        "type": "error",
        "message": decision.get(
            "message",
            "No pude procesar la solicitud. ¿Puedes reformularla?"
        ),
    }
