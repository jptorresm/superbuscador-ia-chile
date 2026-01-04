from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import math
import unicodedata

app = FastAPI()
from backend.assistant_router import router as assistant_router
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
# UTILIDADES
# =========================
def clean_for_json(obj):
    """Elimina NaN / inf para que JSON no reviente"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    return obj


def normalize_text(text: str) -> str:
    """minúsculas + sin acentos + strip"""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


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
# DATA (MULTI-FUENTE)
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"


def load_properties():
    properties = []

    if not DATA_SOURCES_DIR.exists():
        return properties

    for file in DATA_SOURCES_DIR.glob("*.json"):
        source_name = file.stem
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ Error leyendo {file.name}: {e}")
            continue

        if not isinstance(data, list):
            continue

        for p in data:
            if isinstance(p, dict):
                p["source"] = source_name
                properties.append(p)

    return properties


# =========================
# MATCHERS (FILTROS)
# =========================
def match_comuna(p, comuna):
    if not comuna:
        return True

    prop_comuna = normalize_text(p.get("comuna", ""))
    query_comuna = normalize_text(comuna)

    # ✅ Exact match normalizado
    if prop_comuna == query_comuna:
        return True

    # ✅ fallback útil si una fuente trae variantes tipo "Ñuñoa, Santiago"
    return query_comuna in prop_comuna


def match_operacion(p, operacion):
    if not operacion:
        return True
    return normalize_text(operacion) == normalize_text(p.get("operacion", ""))


def match_precio(p, precio_max):
    if not precio_max:
        return True

    precio = p.get("precio")
    if precio is None or precio == "":
        return False

    try:
        return float(precio) <= float(precio_max)
    except Exception:
        return False


def match_amenities(p, amenities):
    if not amenities:
        return True

    texto = normalize_text(json.dumps(p, ensure_ascii=False))
    return all(normalize_text(a) in texto for a in amenities)


# =========================
# IA (interpreta la query)
# =========================
def safe_interpret_query(query: str) -> dict:
    """
    Importa el intérprete dentro de la función para evitar que un error de import
    te tumbe el servidor en Render.
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
    return {"status": "ok", "service": "SuperBuscador IA Chile"}


@app.post("/search")
def search_properties(req: SearchRequest):
    try:
        # 1) Interpretar query con IA (si vienen campos vacíos)
        ia = safe_interpret_query(req.query) if req.query else {}

        comuna = req.comuna or ia.get("comuna")
        operacion = req.operacion or ia.get("operacion")
        precio_max = req.precio_max or ia.get("precio_max")
        amenities = req.amenities or ia.get("amenities")

        # 2) Cargar propiedades
        properties = load_properties()

        # 3) Filtrar
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
            results.append(p)

        response = {
            "query": req.query,
            "filters_applied": {
                "comuna": comuna,
                "operacion": operacion,
                "precio_max": precio_max,
                "amenities": amenities,
            },
            "total": len(results),
            "results": results[:10],
        }

        return clean_for_json(response)

    except Exception as e:
        return {"error": "internal_error", "message": str(e)}
