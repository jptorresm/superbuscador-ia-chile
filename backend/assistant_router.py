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

    # operación
    if "arriendo" in t:
        filters["operacion"] = "arriendo"
    elif "venta" in t:
        filters["operacion"] = "venta"

    # comuna
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
    except Exception as e:
        return {
            "type": "results",
            "filters": filters,
            "results": [],
            "error": "search_engine_error",
        }

    # 🔥 LIMPIEZA OBLIGATORIA
    safe_results = clean_for_json(results)

    return {
        "type": "results",
        "filters": filters,
        "results": safe_results,
    }
