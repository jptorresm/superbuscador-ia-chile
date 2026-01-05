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


ALL_PROPERTIES = load_sources()


def cumple_precio(prop: dict, filtros: dict) -> bool:
    operacion = filtros.get("operacion")

    precio_max_uf = filtros.get("precio_max_uf")
    precio_max_clp = filtros.get("precio_max_clp")

    precio_uf = prop.get("precio_uf")
    precio_clp = prop.get("precio_clp")

    # 🟢 VENTA → UF primero
    if operacion == "venta":
        if precio_max_uf and precio_uf:
            return precio_uf <= precio_max_uf
        if precio_max_clp and precio_clp:
            return precio_clp <= precio_max_clp
        return True  # NO descartar si no hay comparación válida

    # 🟡 ARRIENDO → CLP
    if operacion == "arriendo":
        if precio_max_clp and precio_clp:
            return precio_clp <= precio_max_clp
        return True

    return True


def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max_uf: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    results = []

    for prop in ALL_PROPERTIES:

        if comuna and prop.get("comuna", "").lower() != comuna.lower():
            continue

        if operacion and prop.get("operacion") != operacion:
            continue

        if not cumple_precio(
            prop,
            {
                "operacion": operacion,
                "precio_max_uf": precio_max_uf,
                "precio_max_clp": precio_max_clp,
            }
        ):
            continue

        results.append(prop)

    return results
