from backend.search_engine import clean_for_json
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
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
# UTILIDADES ROBUSTAS
# =========================

def safe_lower(val):
    return val.lower() if isinstance(val, str) else ""


def extract_filters_from_text(text: str) -> Dict[str, Any]:
    """
    Parser tolerante a lenguaje natural real.
    Nunca lanza excepción.
    """
    t = safe_lower(text)
    filters: Dict[str, Any] = {}

    # -----------------------
    # Operación
    # -----------------------
    if "arriendo" in t:
        filters["operacion"] = "arriendo"
    elif "venta" in t:
        filters["operacion"] = "venta"

    # -----------------------
    # Comuna
    # -----------------------
    comunas = ["providencia", "ñuñoa", "las condes", "vitacura", "la reina"]
    for c in comunas:
        if c in t:
            filters["comuna"] = c
            break

    # -----------------------
    # Precio CLP
    # -----------------------
    numbers = re.findall(r"\d{3,}", t.replace(".", ""))
    if numbers:
        try:
            value = int(numbers[0])
            if value > 100000:
                filters["precio_max_clp"] = value
        except Exception:
            pass

    return filters


# =========================
# ENDPOINT
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint BLINDADO:
    - Nunca pregunta
    - Nunca hace loop
    - Nunca lanza 500 por texto raro
    - Siempre intenta buscar
    """

    message = req.message or ""

    # 1️⃣ Extraer filtros desde texto libre
    filters = extract_filters_from_text(message)

    # 2️⃣ Ejecutar búsqueda con lo que haya
    try:
        results = search_properties(
            comuna=filters.get("comuna"),
            operacion=filters.get("operacion"),
            precio_max_clp=filters.get("precio_max_clp"),
        )
    except Exception:
        return clean_for_json({
            "type": "results",
            "filters": filters,
            "results": [],
            "error": "Error interno al buscar propiedades",
        })

    # 3️⃣ Respuesta estándar (SANITIZADA)
    return clean_for_json({
        "type": "results",
        "filters": filters,
        "results": results,
    })

