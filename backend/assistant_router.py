from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import math
import re

from backend.search_engine import search_properties

router = APIRouter()

# =========================
# MODELOS
# =========================

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


# =========================
# META FEEDBACK (MVP)
# =========================

def build_meta(filters: dict) -> dict:
    """
    Construye feedback humano visible para el usuario.
    No pregunta, no bloquea, solo explica y sugiere.
    """

    operacion = filters.get("operacion")
    comuna = filters.get("comuna")
    precio_max = filters.get("precio_max_clp")
    dormitorios = filters.get("dormitorios")

    # Interpretación principal
    parts = []

    if operacion:
        parts.append("arriendos" if operacion == "arriendo" else "ventas")
    else:
        parts.append("propiedades")

    if comuna:
        parts.append(f"en {comuna.title()}")

    interpretation = "Busqué " + " ".join(parts)

    # Supuestos
    assumptions = []
    suggestions = []

    if not comuna:
        assumptions.append("Sin comuna específica")
        suggestions.append("Indicar una comuna mejora los resultados")

    if not precio_max:
        assumptions.append("Sin presupuesto definido")
        suggestions.append("Puedes agregar un precio máximo")

    if not dormitorios:
        assumptions.append("Sin número de dormitorios")
        suggestions.append("También puedes indicar dormitorios")

    return {
        "interpretation": interpretation,
        "assumptions": assumptions,
        "suggestions": suggestions,
    }


# =========================
# JSON SAFE
# =========================

def clean_for_json(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    return obj


# =========================
# NLP SIMPLE
# =========================

def extract_filters_from_text(text: str) -> Dict[str, Any]:
    t = text.lower()
    filters: Dict[str, Any] = {}

    # Operación
    if "arriendo" in t:
        filters["operacion"] = "arriendo"
    elif "venta" in t:
        filters["operacion"] = "venta"

    # Comuna
    comunas = [
        "providencia", "ñuñoa", "las condes",
        "vitacura", "la reina", "santiago"
    ]
    for c in comunas:
        if c in t:
            filters["comuna"] = c
            break

    # Precio CLP
    nums = re.findall(r"\d{3,}", t.replace(".", ""))
    if nums:
        try:
            filters["precio_max_clp"] = int(nums[0])
        except Exception:
            pass

    return filters


# =========================
# ENDPOINT
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    filters = extract_filters_from_text(req.message or "")

    try:
        results = search_properties(
            comuna=filters.get("comuna"),
            operacion=filters.get("operacion"),
            precio_max_clp=filters.get("precio_max_clp"),
        )
    except Exception:
        return {
            "type": "results",
            "meta": build_meta(filters),
            "filters": filters,
            "results": [],
            "error": "search_engine_error",
        }

    safe_results = clean_for_json(results)

    return {
        "type": "results",
        "meta": build_meta(filters),
        "filters": filters,
        "results": safe_results[:10],  # MVP: máximo 10
    }
