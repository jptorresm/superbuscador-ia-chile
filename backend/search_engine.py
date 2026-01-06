from pathlib import Path
import json
import math

# =========================
# CARGA DE DATA
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sources"


def load_sources() -> list[dict]:
    properties = []

    for file in DATA_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for p in data:
                        if isinstance(p, dict):
                            p["source"] = file.stem
                            properties.append(p)
        except Exception:
            continue

    return properties


ALL_PROPERTIES = load_sources()

# =========================
# UTILIDADES
# =========================

def safe_int(value):
    try:
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        return int(value)
    except Exception:
        return None


# =========================
# BUSCADOR ROBUSTO
# =========================

def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max_uf: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    results = []

    for prop in ALL_PROPERTIES:

        if not isinstance(prop, dict):
            continue

        # -----------------------
        # FILTROS BÁSICOS
        # -----------------------
        if comuna and prop.get("comuna") != comuna:
            continue

        if operacion and prop.get("operacion") != operacion:
            continue

        # -----------------------
        # PRECIO NORMALIZADO
        # -----------------------
        precio = safe_int(prop.get("precio_normalizado"))

        if precio_max_clp and precio:
            if precio > precio_max_clp:
                continue

        if precio_max_uf and precio:
            if precio > precio_max_uf:
                continue

        # -----------------------
        # OK
        # -----------------------
        results.append(prop)

    return results
