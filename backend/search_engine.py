# backend/search_engine.py

from pathlib import Path
import json
import math
import unicodedata

# =========================
# UTILIDADES
# =========================
def clean_for_json(obj):
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
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# =========================
# DATA
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
        except Exception:
            continue

        if not isinstance(data, list):
            continue

        for p in data:
            if isinstance(p, dict):
                p["source"] = source_name
                properties.append(p)

    return properties


# =========================
# MATCHERS
# =========================
def match_comuna(p, comuna):
    if not comuna:
        return True

    prop_comuna = normalize_text(p.get("comuna", ""))
    query_comuna = normalize_text(comuna)

    if prop_comuna == query_comuna:
        return True

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
# FUNCIÓN CENTRAL REUTILIZABLE
# =========================
def search_properties(
    *,
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
        results.append(p)

    return clean_for_json(results[:limit])
