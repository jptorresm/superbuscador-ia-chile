from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
        "https://t4global.cl",
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
