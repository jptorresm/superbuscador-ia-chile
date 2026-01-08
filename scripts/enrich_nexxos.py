import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "sources" / "nexxos.json"
OUTPUT_DIR = BASE_DIR / "data" / "enriched"
OUTPUT_FILE = OUTPUT_DIR / "nexxos_enriched.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_float(val):
    try:
        v = float(val)
        return v if v > 0 else None
    except Exception:
        return None


def enrich_property(raw: dict) -> dict:
    operacion = raw.get("operacion")
    precio_raw = raw.get("precio", {})

    precio_final = {
        "operacion": operacion,
        "valor": None,
        "moneda": None,
        "visible": False,
        "uf": None,
        "clp": None,
    }

    # -----------------------
    # EXTRAER PRECIOS
    # -----------------------
    if operacion == "venta":
        venta = precio_raw.get("venta", {})
        if venta.get("activo"):
            uf = safe_float(venta.get("uf"))
            clp = safe_float(venta.get("pesos"))

            precio_final["uf"] = uf
            precio_final["clp"] = clp

            # preferencia UF
            if uf:
                precio_final.update({
                    "valor": uf,
                    "moneda": "UF",
                    "visible": True,
                })
            elif clp:
                precio_final.update({
                    "valor": clp,
                    "moneda": "CLP",
                    "visible": True,
                })

    elif operacion == "arriendo":
        arriendo = precio_raw.get("arriendo", {})
        if arriendo.get("activo"):
            clp = safe_float(arriendo.get("pesos"))
            uf = safe_float(arriendo.get("uf"))

            precio_final["uf"] = uf
            precio_final["clp"] = clp

            # preferencia CLP
            if clp:
                precio_final.update({
                    "valor": clp,
                    "moneda": "CLP",
                    "visible": True,
                })
            elif uf:
                precio_final.update({
                    "valor": uf,
                    "moneda": "UF",
                    "visible": True,
                })

    return {
        "id": raw.get("id"),
        "source": raw.get("source"),
        "source_id": raw.get("source_id"),
        "link": raw.get("link"),
        "estado": str(raw.get("estado", "")).lower(),
        "publicada_web": str(raw.get("publicada_web")).lower() in ("si", "sí", "true"),
        "operacion": operacion,

        # 🔥 PRECIO NORMALIZADO CORRECTO
        "precio": precio_final,

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
        "raw": raw,
    }


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = [enrich_property(p) for p in data]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"✅ Enriched generado: {OUTPUT_FILE} ({len(enriched)} propiedades)")


if __name__ == "__main__":
    main()
