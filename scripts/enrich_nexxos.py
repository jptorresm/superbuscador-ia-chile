import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "sources" / "nexxos.json"
OUTPUT_DIR = BASE_DIR / "data" / "enriched"
OUTPUT_FILE = OUTPUT_DIR / "nexxos_enriched.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def to_bool(val):
    return str(val).strip().lower() in ("sí", "si", "true", "1")


def normalize_operacion(raw: dict) -> str | None:
    """
    Nexxos YA trae la operación normalizada
    """
    op = raw.get("operacion")
    if isinstance(op, str):
        op = op.strip().lower()
        if op in ("venta", "arriendo"):
            return op
    return None


def normalize_precio(raw: dict) -> dict:
    """
    Usamos precio_normalizado + precio_moneda
    No reinterpretamos venta/arriendo
    """
    valor = raw.get("precio_normalizado")
    moneda = raw.get("precio_moneda")

    if valor is None or moneda is None:
        return {
            "valor": None,
            "moneda": None
        }

    try:
        valor = float(valor)
    except Exception:
        valor = None

    return {
        "valor": valor,
        "moneda": moneda
    }


def enrich_property(raw: dict) -> dict:
    operacion = normalize_operacion(raw)
    precio = normalize_precio(raw)

    return {
        "id": raw.get("id") or f"nexxos-{raw.get('codigo')}",
        "source": "nexxos",
        "source_id": raw.get("source_id") or raw.get("codigo"),
        "link": raw.get("link"),
        "estado": str(raw.get("estado", "")).lower(),
        "publicada_web": to_bool(raw.get("publicada_web")),
        "operacion": operacion,

        # 👇 CONTRATO ÚNICO Y SIMPLE
        "precio": precio,

        "ubicacion": {
            "region": raw.get("region"),
            "comuna": raw.get("comuna"),
            "sector": raw.get("sector"),
        },

        "caracteristicas": {
            "dormitorios": raw.get("dormitorios"),
            "banos": raw.get("banos"),
            "gastos_comunes_clp": raw.get("gastos_comunes"),
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

    print(f"✅ Enriched generado: {OUTPUT_FILE} ({len(enriched)} propiedades)")


if __name__ == "__main__":
    main()

