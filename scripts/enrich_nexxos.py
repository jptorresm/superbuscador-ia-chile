import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "nexxos" / "properties.json"
OUTPUT_PATH = BASE_DIR / "data" / "sources" / "nexxos.json"


def to_int(value):
    try:
        if value is None:
            return None
        value = str(value).strip()
        if value == "":
            return None
        value = value.replace(".", "").replace(",", ".")
        return int(float(value))
    except Exception:
        return None


def normalize_price(item: dict):
    """
    Normaliza precio desde estructura:
    item["precio"]["venta" | "arriendo"]
    """
    precio = item.get("precio")
    if not isinstance(precio, dict):
        item["precio_normalizado"] = None
        item["precio_moneda"] = None
        return item

    # -------- VENTA --------
    venta = precio.get("venta")
    if isinstance(venta, dict) and venta.get("activo") is True:
        principal = to_int(venta.get("principal"))
        divisa = str(venta.get("divisa", "")).upper()

        if principal:
            item["precio_normalizado"] = principal
            item["precio_moneda"] = "UF" if divisa == "UF" else "CLP"
            return item

    # ------ ARRIENDO -------
    arriendo = precio.get("arriendo")
    if isinstance(arriendo, dict) and arriendo.get("activo") is True:
        principal = to_int(arriendo.get("principal"))
        if principal:
            item["precio_normalizado"] = principal
            item["precio_moneda"] = "CLP"
            return item

    item["precio_normalizado"] = None
    item["precio_moneda"] = None
    return item


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"No existe {INPUT_PATH}")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = []
    for item in data:
        item = normalize_price(item)
        enriched.append(item)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"✅ Enriquecidas {len(enriched)} propiedades → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
