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
    Devuelve (precio_normalizado, precio_moneda)
    basado en item["precio"]
    """

    precio = item.get("precio")
    if not isinstance(precio, dict):
        return None, None

    # ----------------
    # VENTA
    # ----------------
    venta = precio.get("venta")
    if isinstance(venta, dict) and venta.get("activo") is True:
        principal = to_int(venta.get("principal"))
        divisa = str(venta.get("divisa", "")).upper()

        if principal:
            if divisa == "UF":
                return principal, "UF"
            if divisa in ("$", "CLP", "PESOS"):
                return principal, "CLP"

    # ----------------
    # ARRIENDO
    # ----------------
    arriendo = precio.get("arriendo")
    if isinstance(arriendo, dict) and arriendo.get("activo") is True:
        principal = to_int(arriendo.get("principal"))
        if principal:
            return principal, "CLP"

    return None, None


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"No existe {INPUT_PATH}")

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

    # 🔎 DEBUG CLARO
    sample = enriched[0]
    print("DEBUG sample enriquecido:")
    print("codigo:", sample.get("codigo"))
    print("precio_normalizado:", sample.get("precio_normalizado"))
    print("precio_moneda:", sample.get("precio_moneda"))

    print(f"✅ Enriquecidas {len(enriched)} propiedades → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
