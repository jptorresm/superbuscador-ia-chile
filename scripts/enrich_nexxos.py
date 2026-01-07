# scripts/enrich_nexxos.py

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "sources" / "nexxos.json"
OUTPUT_DIR = BASE_DIR / "data" / "enriched"
OUTPUT_FILE = OUTPUT_DIR / "nexxos_enriched.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------
# Helpers
# -------------------------

def to_bool(val):
    return str(val).strip().lower() in ("sí", "si", "true", "1")


def normalize_number(val):
    """
    Convierte a float válido.
    - 0.0, None, NaN → None
    """
    try:
        if val is None:
            return None
        val = float(val)
        if val == 0.0:
            return None
        return val
    except Exception:
        return None


def normalize_operacion(raw: dict) -> str | None:
    """
    Nexxos puede traer flags o campo operacion directo.
    """
    op = raw.get("operacion")
    if isinstance(op, str):
        op = op.lower().strip()
        if op in ("venta", "arriendo"):
            return op

    if to_bool(raw.get("Venta")):
        return "venta"
    if to_bool(raw.get("Arriendo")):
        return "arriendo"

    return None


def extract_precio(raw: dict, operacion: str | None) -> dict:
    """
    Regla clave:
    - Se usa SOLO el bloque correspondiente a la operación
    - 0.0 o valores inválidos → None
    """
    precio_raw = raw.get("precio", {})

    if not isinstance(precio_raw, dict) or operacion not in ("venta", "arriendo"):
        return {"valor": None, "moneda": None}

    bloque = precio_raw.get(operacion)
    if not isinstance(bloque, dict):
        return {"valor": None, "moneda": None}

    if not bloque.get("activo"):
        return {"valor": None, "moneda": None}

    valor = (
        normalize_number(bloque.get("principal"))
        or normalize_number(bloque.get("uf"))
        or normalize_number(bloque.get("pesos"))
    )

    moneda = bloque.get("divisa")

    if valor is None or moneda is None:
        return {"valor": None, "moneda": None}

    return {
        "valor": valor,
        "moneda": moneda
    }


# -------------------------
# Enrich
# -------------------------

def enrich_property(raw: dict) -> dict:
    operacion = normalize_operacion(raw)
    precio = extract_precio(raw, operacion)

    return {
        "id": raw.get("id") or f"nexxos-{raw.get('codigo')}",
        "source": "nexxos",
        "source_id": raw.get("codigo"),
        "link": raw.get("link"),
        "estado": str(raw.get("estado", "")).lower(),
        "publicada_web": to_bool(raw.get("publicada_web")),
        "operacion": operacion,

        # ✅ CONTRATO ÚNICO
        "precio": precio,

        "ubicacion": {
            "region": raw.get("region"),
            "comuna": raw.get("comuna"),
            "sector": raw.get("sector"),
        },

        "caracteristicas": {
            "dormitorios": raw.get("dormitorios"),
            "banos": raw.get("banos"),
            "gastos_comunes_clp": normalize_number(raw.get("gastos_comunes")),
        },

        "amenities": raw.get("amenities", {}),
        "raw": raw
    }


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    enriched = [enrich_property(p) for p in raw_data]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"✅ Enriched generado: {OUTPUT_FILE}")
    print(f"   Total propiedades: {len(enriched)}")

    # sanity check
    ventas = sum(1 for x in enriched if x["operacion"] == "venta")
    arriendos = sum(1 for x in enriched if x["operacion"] == "arriendo")

    print(f"   Ventas: {ventas}")
    print(f"   Arriendos: {arriendos}")


if __name__ == "__main__":
    main()
