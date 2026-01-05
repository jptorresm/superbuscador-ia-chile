import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_DATA_PATH = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"


# =========================
# UTILS
# =========================
def normalize_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return (
        str(value)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


def sanitize_for_json(obj):
    """
    Reemplaza NaN / inf por None de forma recursiva
    (JSON no soporta NaN)
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]

    return obj


# =========================
# LOAD DATA (SAFE)
# =========================
def load_properties() -> List[Dict[str, Any]]:
    try:
        print("ENRICHED_DATA_PATH:", ENRICHED_DATA_PATH)
        print("EXISTS:", ENRICHED_DATA_PATH.exists())

        if not ENRICHED_DATA_PATH.exists():
            return []

        with open(ENRICHED_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print("TOTAL ENRICHED PROPERTIES:", len(data))
                return data

    except Exception as e:
        print("❌ ERROR loading enriched data:", e)

    return []


# ⚠️ IMPORTANTE:
# La carga se hace una vez y NO debe romper el módulo
ALL_PROPERTIES: List[Dict[str, Any]] = load_properties()


# =========================
# MAIN SEARCH
# =========================
def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max: Optional[int] = None,  # reservado para paso siguiente
    amenities: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    comuna_n = normalize_text(comuna)
    operacion_n = normalize_text(operacion)

    for p in ALL_PROPERTIES:

        # -----------------------
        # COMUNA (enriched)
        # -----------------------
        if comuna_n:
            p_comuna = normalize_text(
                (p.get("ubicacion") or {}).get("comuna")
            )
            if p_comuna != comuna_n:
                continue

        # -----------------------
        # OPERACION (enriched)
        # -----------------------
        if operacion_n:
            if normalize_text(p.get("operacion")) != operacion_n:
                continue

        # -----------------------
        # TIPO (enriched, opcional)
        # -----------------------
        filtro_tipo = None
        if isinstance(amenities, dict):
            filtro_tipo = normalize_text(amenities.get("tipo"))

        if filtro_tipo:
            if normalize_text(p.get("tipo")) != filtro_tipo:
                continue

        # -----------------------
        # PASA FILTROS
        # -----------------------
        results.append(p)

    # ⚠️ CRÍTICO:
    # limpiar NaN antes de serializar a JSON
    return sanitize_for_json(results)

