import subprocess
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ENRICHED = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"

UF_REFERENCIA = 37000


def run_enrichment():
    """
    Ejecuta el script de enriquecimiento (NO lo toca)
    """
    script = BASE_DIR / "scripts" / "enrich_nexxos.py"
    if script.exists():
        subprocess.run(["python", str(script)], check=True)


def normalize_precio(prop: dict) -> dict:
    """
    Fuente única de verdad del precio.
    Interpreta correctamente venta / arriendo y monedas.
    """

    precio_raw = prop.get("raw", {}).get("precio", {})
    operacion = prop.get("operacion")

    bloque = precio_raw.get(operacion) if operacion else None
    if not isinstance(bloque, dict) or not bloque.get("activo"):
        return {
            "operacion": operacion,
            "valor": None,
            "moneda": None,
            "uf": None,
            "clp": None,
            "visible": False,
        }

    moneda = bloque.get("divisa")
    uf = bloque.get("uf")
    clp = bloque.get("pesos")
    valor = bloque.get("principal")

    try:
        if moneda == "UF" and uf:
            return {
                "operacion": operacion,
                "valor": uf,
                "moneda": "UF",
                "uf": uf,
                "clp": int(uf * UF_REFERENCIA),
                "visible": True,
            }

        if moneda in ("$", "CLP") and clp:
            return {
                "operacion": operacion,
                "valor": clp,
                "moneda": "CLP",
                "uf": round(clp / UF_REFERENCIA, 2),
                "clp": clp,
                "visible": True,
            }
    except Exception:
        pass

    return {
        "operacion": operacion,
        "valor": None,
        "moneda": None,
        "uf": None,
        "clp": None,
        "visible": False,
    }


def bootstrap_data():
    """
    Aplica normalización FINAL sobre la data enriquecida
    """
    if not DATA_ENRICHED.exists():
        return []

    data = json.loads(DATA_ENRICHED.read_text(encoding="utf-8"))

    for p in data:
        p["precio"] = normalize_precio(p)

    return data
