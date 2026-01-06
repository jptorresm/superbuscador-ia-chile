import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "sources" / "nexxos.json"
OUTPUT_DIR = BASE_DIR / "data" / "enriched"
OUTPUT_FILE = OUTPUT_DIR / "nexxos_enriched.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def to_bool(val):
    return str(val).strip().lower() in ("sí", "si", "true", "1")


def enrich_property(raw: dict) -> dict:
    # Flags de operación desde Nexxos
    en_venta = to_bool(raw.get("Venta"))
    en_arriendo = to_bool(raw.get("Arriendo"))

    precio_ppal = raw.get("Precio ppal.")
    moneda = raw.get("Divisa ppal.")

    precio = {
        "venta": None,
        "arriendo": None
    }

    if en_venta and precio_ppal:
        precio["venta"] = {
            "valor": precio_ppal,
            "moneda": moneda
        }

    if en_arriendo and precio_ppal:
        precio["arriendo"] = {
            "valor": precio_ppal,
            "moneda": moneda
        }

    return {
        "id": raw.get("id") or raw.get("codigo"),
        "source": "nexxos",
        "source_id": raw.get("codigo"),
        "link": raw.get("link"),
        "estado": raw.get("estado", "").lower(),
        "publicada_web": to_bool(raw.get("publicada_web")),
        "operacion": "venta" if en_venta else "arriendo" if en_arriendo else None,

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
