from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.search_engine import search_properties

router = APIRouter()

# =========================
# MODELOS
# =========================

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


# =========================
# MEMORIA EN RAM (simple)
# =========================

SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {}
    return SESSIONS[session_id]


# =========================
# UTILIDADES
# =========================

def extract_filters_from_text(text: str) -> Dict[str, Any]:
    t = text.lower()

    filters = {}

    if "arriendo" in t:
        filters["operacion"] = "arriendo"
    elif "venta" in t:
        filters["operacion"] = "venta"

    if "providencia" in t:
        filters["comuna"] = "providencia"
    if "ñuñoa" in t:
        filters["comuna"] = "ñuñoa"
    if "las condes" in t:
        filters["comuna"] = "las condes"

    # precio simple (CLP)
    for token in t.replace(".", "").split():
        if token.isdigit():
            value = int(token)
            if value > 100000:
                filters["precio_max_clp"] = value

    return filters


def missing_fields(state: Dict[str, Any]) -> list[str]:
    required = ["operacion", "comuna", "precio_max_clp"]
    return [f for f in required if f not in state]


def question_for(field: str) -> str:
    if field == "operacion":
        return "¿La buscas en venta o en arriendo?"
    if field == "comuna":
        return "¿En qué comuna buscas la propiedad?"
    if field == "precio_max_clp":
        return "¿Cuál es tu presupuesto máximo en pesos?"
    return "¿Puedes darme un poco más de información?"


# =========================
# ENDPOINT
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    session_id = req.session_id or "default"
    state = get_session(session_id)

    # 1️⃣ Extraer filtros del mensaje actual
    new_filters = extract_filters_from_text(req.message)

    # 2️⃣ Actualizar estado acumulado
    state.update(new_filters)

    # 3️⃣ Ver qué falta
    missing = missing_fields(state)

    if missing:
        field = missing[0]
        return {
            "type": "question",
            "message": question_for(field),
            "state": state,
        }

    # 4️⃣ Ejecutar búsqueda (YA NO LOOPA)
    results = search_properties(state)

    return {
        "type": "results",
        "filters": state,
        "results": results,
    }
