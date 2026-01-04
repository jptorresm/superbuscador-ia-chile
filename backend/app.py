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
    allow_origins=["*"],  # luego lo cerraremos a t4global.cl
    allow_credentials=True,
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

DATA_PATH = Path("data/propiedades.json")


def load_properties():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


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
    properties = sanitize(load_properties())

    # 👉 USAR IA SI SOLO VIENE TEXTO
    if not any([req.comuna, req.operacion, req.precio_max, req.amenities]):
        try:
            ia = interpret_query(req.query)
            req.comuna = ia.get("comuna")
            req.operacion = ia.get("operacion")
            req.precio_max = ia.get("precio_max")
            req.amenities = ia.get("amenities")
        except Exception as e:
            print("⚠️ Error IA:", e)

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
        "filters_applied": {
            "comuna": req.comuna,
            "operacion": req.operacion,
            "precio_max": req.precio_max,
            "amenities": req.amenities,
        },
        "total": len(results),
        "results": results[:10],
    }
