from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from backend.search_engine import search_properties

router = APIRouter()

# =========================
# MODELO REQUEST
# =========================

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

# =========================
# MEMORIA EN RAM
# =========================

SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {}
    return SESSIONS[session_id]

# =========================
# NORMALIZADORES
# =========================

def normalize_comuna(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, dict):
        nombre = value.get("nombre")
        if isinstance(nombre, str):
            return nombre.strip().lower()
    return None

def normalize_operacion(value: Any) -> Optional[str]:
    if isinstance(value, str):
        v = value.lower()
        if v in ("venta", "arriendo"):
            return v
    return None

def normalize_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except Exception:
        return None

# =========================
# EXTRACCIÓN SIMPLE DESDE TEXTO
# =========================

def extract_filters_from_text(text: str) -> Dict[str, Any]:
    t = text.lower()
    filters: Dict[str, Any] = {}

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

    for token in t.replace(".", "").split():
        if token.isdigit():
            val = int(token)
            if val > 100000:
                filters["precio_max_clp"] = val

    return filters

# =========================
# CAMPOS REQUERIDOS
# =========================

def missing_fields(state: Dict[str, Any]) -> list[str]:
    required = ["operacion", "comuna", "precio_max_clp"]
    return [f for f in required if not state.get(f)]

def question_for(field: str) -> str:
    if field == "operacion":
        return "¿La buscas en venta o en arriendo?"
    if field == "comuna":
        return "¿En qué comuna buscas la propiedad?"
    if field == "precio_max_clp":
        return "¿Cuál es tu presupuesto máximo en pesos?"
    return "¿Puedes darme un poco más de información?"

# =========================
# ENDPOINT PRINCIPAL
# =========================

@router.post("/assistant")
def assistant(req: AssistantRequest):
    session_id = req.session_id or "default"
    state = get_session(session_id)

    # 1️⃣ Extraer filtros nuevos
    extracted = extract_filters_from_text(req.message)

    # 2️⃣ Actualizar estado (crudo)
    state.update(extracted)

    # 3️⃣ NORMALIZAR ESTADO (CLAVE)
    state["comuna"] = normalize_comuna(state.get("comuna"))
    state["operacion"] = normalize_operacion(state.get("operacion"))
    state["precio_max_clp"] = normalize_int(state.get("precio_max_clp"))

    # 4️⃣ Preguntar si falta algo
    missing = missing_fields(state)
    if missing:
        field = missing[0]
        return {
            "type": "question",
            "message": question_for(field),
            "state": state,
        }

    # 5️⃣ Ejecutar búsqueda (SEGURO)
    results = search_properties(
        comuna=state.get("comuna"),
        operacion=state.get("operacion"),
        precio_max_clp=state.get("precio_max_clp"),
        precio_max_uf=None,
        amenities=None,
    )

    return {
        "type": "results",
        "filters": state,
        "results": results,
    }


