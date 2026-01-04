from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==================================================
# APP
# ==================================================
app = FastAPI(title="SuperBuscador IA Chile")

# ==================================================
# CORS (DEBE IR ANTES DE LOS ROUTERS)
# ==================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.t4global.cl",
        "https://t4global.cl",
        "https://www.nexxoschile.cl",
        "http://localhost:8069",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# HELPERS
# ==================================================
def build_property_url(p: dict) -> str | None:
    source = p.get("source")
    codigo = p.get("codigo")

    if source == "nexxos" and codigo:
        return f"https://nexxospropiedades.cl/fichaPropiedad.aspx?i={codigo}"

    return None

# ==================================================
# IMPORTS INTERNOS (DESPUÉS DE APP + CORS)
# ==================================================
from backend.search_engine import search_properties
from backend.assistant_router import router as assistant_router

# ==================================================
# ROUTERS
# ==================================================
app.include_router(assistant_router)

# ==================================================
# MODELOS
# ==================================================
class SearchRequest(BaseModel):
    query: str
    comuna: str | None = None
    operacion: str | None = None
    precio_max: int | None = None
    amenities: list[str] | None = None

# ==================================================
# IA (INTÉRPRETE SEGURO)
# ==================================================
def safe_interpret_query(query: str) -> dict:
    """
    Importa el intérprete dentro de la función para evitar
    que un error de import rompa el deploy en Render.
    """
    try:
        from backend.ai_interpreter import interpret_message
        out = interpret_message(query)
        return out if isinstance(out, dict) else {}
    except Exception as e:
        print("⚠️ IA interpret_message error:", e)
        return {}

# ==================================================
# ENDPOINTS
# ==================================================
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

    ia = safe_interpret_query(req.query) if req.query else {}

    comuna = req.comuna or ia.get("filters", {}).get("comuna")
    operacion = req.operacion or ia.get("filters", {}).get("operation")
    precio_max = req.precio_max or ia.get("filters", {}).get("price_max")
    amenities = req.amenities

    results = search_properties(
        comuna=comuna,
        operacion=operacion,
        precio_max=precio_max,
        amenities=amenities,
        limit=10,
    )

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
