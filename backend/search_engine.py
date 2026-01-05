import json
from pathlib import Path
from typing import List, Optional, Dict, Any

# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_DATA_PATH = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"

# =========================
# LOAD DATA
# =========================

def load_properties() -> List[Dict[str, Any]]:
    if not ENRICHED_DATA_PATH.exists():
        print(f"❌ ENRICHED_DATA_PATH no existe: {ENRICHED_DATA_PATH}")
        return []

    with open(ENRICHED_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✅ TOTAL ENRICHED PROPERTIES: {len(data)}")
    return data


PROPERTIES = load_properties()

# =========================
# PRICE SELECTION
# =========================

def get_price(
    p: Dict[str, Any],
    operacion: str,
    moneda: Optional[str] = None,
) -> Optional[float]:
    precio = p.get("precio", {})
    block = precio.get(operacion)

    if not block or not block.get("activo"):
        return None

    if moneda:
        return block.get(moneda.lower())

    if operacion == "venta":
        return block.get("uf")

    if operacion == "arriendo":
        return block.get("pesos")

    return None

# =========================
# SEARCH ENGINE
# =========================

def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max: Optional[float] = None,
    moneda: Optional[str] = None,
    amenities: Optional[List[str]] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    for p in PROPERTIES:

        # -----------------------
        # OPERACIÓN
        # -----------------------
        if operacion:
            precio_block = p.get("precio", {}).get(operacion)
            if not precio_block or not precio_block.get("activo"):
                continue

        # -----------------------
        # COMUNA
        # -----------------------
        if comuna:
            if p.get("comuna", "").lower() != comuna.lower():
                continue

        # -----------------------
        # AMENITIES
        # -----------------------
        if amenities:
            prop_amenities = p.get("amenities", {})
            if not all(prop_amenities.get(a) for a in amenities):
                continue

        # -----------------------
        # PRECIO
        # -----------------------
        precio = None
        if operacion:
            precio = get_price(p, operacion, moneda)
            if precio is None:
                continue
            if precio_max is not None and precio > precio_max:
                continue

        # -----------------------
        # RESULT OBJECT
        # -----------------------
        result = {
            "id": p.get("id"),
            "codigo": p.get("codigo"),
            "comuna": p.get("comuna"),
            "sector": p.get("sector"),
            "operacion": operacion,
            "precio": {
                "valor": precio,
                "moneda": moneda
                if moneda
                else ("UF" if operacion == "venta" else "CLP"),
            },
            "dormitorios": p.get("dormitorios"),
            "banos": p.get("banos"),
            "amenities": p.get("amenities"),
            "link": p.get("link"),
            "source": p.get("source"),
        }

        results.append(result)

        if len(results) >= limit:
            break

    return results
