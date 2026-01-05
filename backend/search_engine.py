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
    """
    Selecciona el precio correcto según:
    - operación (venta / arriendo)
    - moneda explícita u opcional
    """

    precio = p.get("precio", {})
    block = precio.get(operacion)

    if not block or not block.get("activo"):
        return None

    # Moneda explícita solicitada
    if moneda:
        return block.get(moneda.lower())

    # Moneda por defecto
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

    results = []

    for p in PROPERTIES:

        # -----------------------
        # OPERACIÓN
        # -----------------------
        if operacion:
