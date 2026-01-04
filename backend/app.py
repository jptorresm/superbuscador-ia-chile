from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

def build_property_url(p: dict) -> str | None:
    source = p.get("source")
    codigo = p.get("codigo")

    if source == "nexxos" and codigo:
        return f"https://nexxospropiedades.cl/fichaPropiedad.aspx?i={codigo}"

    # futuras fuentes
    # if source == "portal_x":
    #     return ...

    return None


# 🔹 Importa el search engine reutilizable
from backend.search_engine import search_properties

# 🔹 Router del assistant
from backend.assistant_router import router as assistant_router

# =========================
# APP
# =========================
app = FastAPI(title="SuperBuscador IA Chile")

# Registrar router del assistant
app.include_router(assistant_router)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.t4global.cl",
        "https://t4global.cl","https://www.nexxoschile.cl",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELOS
# =========================
class SearchRequest(BaseModel):
    query: str
    comuna: str | None = None
    operacion: str | None = None
    precio_max: int | None = None
    amenities: list[str] | None = None

# =========================
# IA (INTÉRPRETE SEGURO)
# =========================
def safe_interpret_query(query: str) -> dict:
    """
    Importa el intérprete dentro de la función para evitar
    que un error de import rompa el deploy en Render.
    """
    try:
        from backend.ai_interpreter import interpret_query
        out = interpret_query(query)
        return out if isinstance(out, dict) else {}
    except Exception as e:
        print("⚠️ IA interpret_query error:", e)
        return {}
# =========================
# DATA + SEARCH ENGINE
# =========================
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"


def load_properties():
    properties = []

    if not DATA_SOURCES_DIR.exists():
        return properties

    for file in DATA_SOURCES_DIR.glob("*.json"):
        source_name = file.stem
        data = json.loads(file.read_text(encoding="utf-8"))

        for p in data:
            p["source"] = source_name
            properties.append(p)

    return properties


def match_comuna(p, comuna):
    if not comuna:
        return True
    return comuna.lower() in p.get("comuna", "").lower()


def match_operacion(p, operacion):
    if not operacion:
        return True
    return operacion.lower() in p.get("operacion", "").lower()


def match_precio(p, precio_max):
    if not precio_max:
        return True
    precio = p.get("precio")
    try:
        return float(precio) <= float(precio_max)
    except Exception:
        return False


def match_amenities(p, amenities):
    if not amenities:
        return True
    texto = json.dumps(p, ensure_ascii=False).lower()
    return all(a.lower() in texto for a in amenities)


def search_properties(
    comuna=None,
    operacion=None,
    precio_max=None,
    amenities=None,
    limit=10,
):
    properties = load_properties()
    results = []

    for p in properties:
        if not match_comuna(p, comuna):
            continue
        if not match_operacion(p, operacion):
            continue
        if not match_precio(p, precio_max):
            continue
        if not match_amenities(p, amenities):
            continue

        # 👉 AQUÍ se construye el link
        p["url"] = build_property_url(p)
        results.append(p)

        if len(results) >= limit:
            break

    return results

# =========================
# ENDPOINTS
# =========================
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SuperBuscador IA Chile"
    }

@app.post("/search")
def search(req: SearchRequest):
    """
    Endpoint de búsqueda estructurada.
    Usa el mismo search_engine que el assistant.
    """

    # 1️⃣ Interpretación IA (solo si faltan campos)
    ia = safe_interpret_query(req.query) if req.query else {}

    comuna = req.comuna or ia.get("comuna")
    operacion = req.operacion or ia.get("operacion")
    precio_max = req.precio_max or ia.get("precio_max")
    amenities = req.amenities or ia.get("amenities")

    # 2️⃣ Búsqueda real
    results = search_properties(
        comuna=comuna,
        operacion=operacion,
        precio_max=precio_max,
        amenities=amenities,
        limit=10,
    )

    # 3️⃣ Respuesta
    return {
        "query": req.query,
        "filters_applied": {
            "comuna": comuna,
            "operacion": operacion,
            "precio_max": precio_max,
            "amenities": amenities,
        },
        "total": len(results),
        "results": results,
    }
