from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path

# 👉 IMPORTA EL INTÉRPRETE IA
from backend.ai_interpreter import interpret_query


# ======================================================
# APP
# ======================================================

app = FastAPI()


# ======================================================
# CORS (TEMPORAL ABIERTO PARA PRUEBAS CON ODOO)
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
# MODELOS
# ======================================================

class SearchRequest(BaseModel):
    query: str
    comuna: str | None = None
    operacion: str | None = None
    precio_max: int | None = None
    amenities: list[str] | None = None


# ======================================================
# DATA
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"


def load_properties():
    properties = []

    if not DATA_SOURCES_DIR.exists():
        raise FileNotFoundError("No data sources directory found")

    for file in DATA_SOURCES_DIR.glob("*.json"):
        source_name = file.stem

        data = json.loads(file.read_text(encoding="utf-8"))

        for p in data:
            p["source"] = source_name
            properties.append(p)

    return properties

def sanitize(properties):
    """Elimina NaN o valores raros"""
    clean = []
    for p in properties:
        clean.append({k: v for k, v in p.items() if v not in ["", None]})
    return clean


# ======================================================
# MATCHERS
# ======================================================

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
    if not precio:
        return False
    try:
        return float(precio) <= float(precio_max)
    except:
        return False


def match_amenities(p, amenities):
    if not amenities:
        return True
    texto = json.dumps(p).lower()
    return all(a.lower() in texto for a in amenities)


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

        return {
            "query": req.query,
            "total": len(results),
            "results": results[:10],
        }

    except Exception as e:
        # 👇 CLAVE: devolver el error real
        return {
            "error": "internal_error",
            "message": str(e),
        }
