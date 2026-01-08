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
# UTILIDADES
# =========================

def safe_lower(val):
    return val.lower() if isinstance(val, str) else ""


def extract_filters_from_text(text: str) -> Dict[str, Any]:
    """
    Parser SIMPLE y DETERMINISTA.
    Nada de magia aún.
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
    # Comunas (hardcode inicial)
    # -----------------------
    COMUNAS = [
        "providencia",
        "las condes",
        "vitacura",
        "ñuñoa",
        "la reina",
        "santiago",
        "macul",
        "peñalolén",
        "san miguel",
        "san joaquín",
    ]

    for c in COMUNAS:
        if c in t:
            filters["comuna"] = c
            break

    # -----------------------
    # Precio máximo CLP (opcional)
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
    Endpoint estable:
    - NO lanza 500
    - NO hace loops
    - Siempre responde JSON
    """

    message = req.message or ""

    # 1️⃣ Extraer filtros
    filters = extract_filters_from_text(message)

    # 2️⃣ Buscar propiedades
    try:
        results = search_properties(
            operacion=filters.get("operacion"),
            comuna=filters.get("comuna"),
            precio_max_clp=filters.get("precio_max_clp"),
        )
    except Exception as e:
        return {
            "type": "results",
            "filters": filters,
            "results": [],
            "error": "Error interno al buscar propiedades",
        }

    # 3️⃣ Respuesta estándar
    return {
        "type": "results",
        "filters": filters,
        "results": results,
    }
