from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
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
# JSON SAFE (CRÍTICO)
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
# NLP SIMPLE (MPV)
# =========================

def extract_filters_from_text(text: str) -> Dict[str, Any]:
    t = (text or "").lower()
    filters: Dict[str, Any] = {}

    # operación
    if "arriendo" in t:
        filters["operacion"] = "arriendo"
    elif "venta" in t:
        filters["operacion"] = "venta"

    # comunas básicas
    comunas = [
        "providencia", "ñuñoa", "las condes",
        "vitacura", "la reina", "santiago"
    ]
    for c in comunas:
        if c in t:
            filters["comuna"] = c
            break

    # precio CLP
    nums = re.findall(r"\d{3,}", t.replace(".", ""))
    if nums:
        try:
            filters["precio_max_clp"] = int(nums[0])
        except Exception:
            pass

    return filters


# =========================
# META (INTELIGENCIA VISIBLE)
# =========================

def build_meta(filters: Dict[str, Any], results_count: int) -> Dict[str, Any]:
    interpretation_parts: List[str] = []

    operacion = filters.get("operacion")
    comuna = filters.get("comuna")
    precio = filters.get("precio_max_clp")

    # interpretación principal
    if operacion == "arriendo":
        interpretation_parts.append("arriendos")
    elif operacion == "venta":
        interpretation_parts.append("ventas")
    else:
        interpretation_parts.append("propiedades")

    if comuna:
        interpretation_parts.append(f"en {comuna.title()}")

    interpretation = "Busqué " + " ".join(interpretation_parts)

    # supuestos detectados
    assumptions = []
    suggestions = []

    if not comuna:
        assumptions.append("No indicaste comuna")
        suggestions.append("Indicar comuna (ej: Providencia, Ñuñoa)")

    if not precio:
        assumptions.append("No indicaste presupuesto")
        suggestions.append("Agregar precio máximo")

    if results_count > 20:
        suggestions.append("Agregar más filtros para acotar resultados")

    if results_count == 0:
        suggestions.append("Probar otra comuna o aumentar presupuesto")

    return {
        "interpretation": interpretation,
        "assumptions": assumptions,
        "suggestions": suggestions
    }


# =========================
# ENDPOINT PRINCIPAL
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    filters = extract_filters_from_text(req.message)

    try:
        results = search_properties(
            comuna=filters.get("comuna"),
            operacion=filters.get("operacion"),
            precio_max_clp=filters.get("precio_max_clp"),
        )
    except Exception:
        # blindaje total: nunca 500
        return {
            "type": "results",
            "filters": filters,
            "meta": {
                "interpretation": "No pude ejecutar la búsqueda",
                "assumptions": [],
                "suggestions": ["Intenta reformular la búsqueda"]
            },
            "results": []
        }

    safe_results = clean_for_json(results)

    return {
        "type": "results",
        "filters": filters,
        "meta": build_meta(filters, len(safe_results)),
        "results": safe_results
    }
