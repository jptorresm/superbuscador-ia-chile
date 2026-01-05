from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sources"


# =========================
# CARGA DE FUENTES
# =========================

def load_sources() -> list[dict]:
    properties = []

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"No existe el directorio {DATA_DIR}")

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                p["source"] = file.stem
                properties.append(p)

    return properties


ALL_PROPERTIES = load_sources()


# =========================
# FILTRO DE PRECIO
# =========================

def cumple_precio(prop: dict, filtros: dict) -> bool:
    """
    Usa SOLO precio_normalizado y precio_moneda.
    Asume que vienen enriquecidos.
    """

    precio = prop.get("precio_normalizado")
    moneda = prop.get("precio_moneda")

    if precio is None or moneda is None:
        return True  # no descartamos si no hay precio

    # Venta en UF
    if moneda == "UF" and filtros.get("precio_max_uf"):
        return precio <= filtros["precio_max_uf"]

    # CLP (venta o arriendo)
    if moneda == "CLP" and filtros.get("precio_max_clp"):
        return precio <= filtros["precio_max_clp"]

    return True


# =========================
# BÚSQUEDA PRINCIPAL
# =========================

def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max_uf: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    """
    Búsqueda simple sobre data enriquecida.
    """

    filtros = {
        "precio_max_uf": precio_max_uf,
        "precio_max_clp": precio_max_clp,
    }

    results = []

    for prop in ALL_PROPERTIES:

        # Comuna
        if comuna and prop.get("comuna", "").lower() != comuna.lower():
            continue

        # Operación
        if operacion and prop.get("operacion") != operacion:
            continue

        # Precio
        if not cumple_precio(prop, filtros):
            continue

        # Amenities (AND lógico)
        if amenities:
            prop_amenities = prop.get("amenities", {})
            if not all(prop_amenities.get(a) is True for a in amenities):
                continue

        results.append(prop)

    return results
