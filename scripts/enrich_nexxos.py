import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "data" / "nexxos" / "properties.json"
OUTPUT_PATH = BASE_DIR / "data" / "sources" / "nexxos.json"


def normalize_price(item: dict):
    """
    Extrae precio_normalizado y precio_moneda
    desde la estructura REAL del JSON Nexxos
    """

    precio = item.get("precio")
    if not isinstance(precio, dict):
        return None, None

    venta = precio.get("venta")
    if isinstance(venta, dict) and venta.get("activo") is True:
        principal = venta.get("principal")
        divisa = venta.get("divisa")

        if principal is not None and divisa:
            try:
                return int(round(float(principal))), str(divisa).upper()
            except Exception:
                return None, None

    arriendo = precio.get("arriendo")
    if isinstance(arriendo, dict) and arriendo.get("activo") is True:
        principal = arriendo.get("principal")
        if principal is not None:
            try:
                return int(round(float(principal))), "CLP"
            except Exception:
                return None, None

    return None, None


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = []

    for item in data:
        precio_normalizado, precio_moneda = normalize_price(item)

        item["precio_normalizado"] = precio_normalizado
        item["precio_moneda"] = precio_moneda

        enriched.append(item)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    # 🔎 VERIFICACIÓN CLARA
    sample = enriched[0]
    print("DEBUG SAMPLE:")
    print("codigo:", sample.get("codigo"))
    print("precio_normalizado:", sample.get("precio_normalizado"))
    print("precio_moneda:", sample.get("precio_moneda"))
    print(f"✅ Enriquecidas {len(enriched)} propiedades → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
