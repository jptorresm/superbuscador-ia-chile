from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sources"


def load_sources() -> list[dict]:
    properties = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                p["source"] = file.stem
                properties.append(p)

    return properties


def cumple_precio(prop: dict, filtros: dict) -> bool:
    precio = prop.get("precio_normalizado")
    moneda = prop.get("precio_moneda")

    if precio is None or moneda is None:
        return True

    if moneda == "UF":
        if filtros.get("precio_min_uf") is not None and precio < filtros["precio_min_uf"]:
            return False
        if filtros.get("precio_max_uf") is not None and precio > filtros["precio_max_uf"]:
            return False

    if moneda == "CLP":
        if filtros.get("precio_min_clp") is not None and precio < filtros["precio_min_clp"]:
            return False
        if filtros.get("precio_max_clp") is not None and precio > filtros["precio_max_clp"]:
            return False

    return True


def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_min_uf: int | None = None,
    precio_max_uf: int | None = None,
    precio_min_clp: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    all_properties = load_sources()

    filtros_precio = {
        "precio_min_uf": precio_min_uf,
        "precio_max_uf": precio_max_uf,
        "precio_min_clp": precio_min_clp,
        "precio_max_clp": precio_max_clp,
    }

    results = []

    for prop in all_properties:

        if comuna and prop.get("comuna", "").lower() != comuna.lower():
            continue

        if operacion and prop.get("operacion") != operacion:
            continue

        if not cumple_precio(prop, filtros_precio):
            continue

        if amenities:
            prop_amenities = prop.get("amenities", {})
            if not all(prop_amenities.get(a) is True for a in amenities):
                continue

        results.append(prop)

    return results
