from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
import math
import unicodedata

# ======================================================
# APP
# ======================================================

app = FastAPI()

# ======================================================
# CORS (ODOO + WEB)
# ======================================================

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

# ======================================================
# UTILIDADES
# ======================================================

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
    """Normaliza texto: minúsculas + sin acentos"""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# ======================================================
# MODELOS
# ======================================================

class SearchRequest(BaseModel):
    query: str
    comuna: str | None = None
    operacion: str | None = None
    precio_max: int | None = None
    amenities: list[str] | None = None


# ======================================================
# DATA (MULTI-FUENTE)
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"


def load_properties():
    """Carga todas las fuentes JSON"""
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


# ======================================================
# MATCHERS (FILTROS)
# ======================================================

def match_comuna(p, comuna):
    if not comuna:
        return True

    prop_comuna = normalize_text(p.get("comuna", ""))
    query_comuna = normalize_text(comuna)

    return prop_comuna == query_comuna


def match_operacion(p, operacion):
    if not operacion:
        return True

    return normalize_text(operacion) == normalize_text(p.get("operacion", ""))


def match_precio(p, precio_max):
    if not precio_max:
        return True

    precio = p.get("precio")
    if precio is None:
        return False

    try:
        return float(precio) <= float(precio_max)
    except Exception:
        return False


def match_amenities(p, amenities):
    if not amenities:
        return True

    texto = normalize_text(json.dumps(p))
    return all(normalize_text(a) in texto for a in amenities)


# ======================================================
# ENDPOINTS
# ======================================================

@app.get("/")
def root():
    return {"status": "ok", "service": "SuperBuscador IA Chile"}


@app.post("/search")
def search_properties(req: SearchRequest):
    try:
        properties = load_properties()

        results = []
        for p in properties:
            if not match_comuna(p, req.comuna):
                continue
            if not match_operacion(p, req.operacion):
                continue
            if not match_precio(p, req.precio_max):
                continue
            if not match_amenities(p, req.amenities):
                continue
            results.append(p)

        response = {
            "query": req.query,
            "filters": {
                "comuna": req.comuna,
                "operacion": req.operacion,
                "precio_max": req.precio_max,
                "amenities": req.amenities,
            },
            "total": len(results),
            "results": results[:10],
        }

        return clean_for_json(response)

    except Exception as e:
        return {
            "error": "internal_error",
            "message": str(e),
        }
