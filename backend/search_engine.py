from pathlib import Path
import json
import unicodedata
from typing import Optional, List, Dict

# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_DATA_PATH = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"


# =========================
# UTILIDADES
# =========================

def normalize_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = str(text).lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def parse_number(value) -> Optional[float]:
    """
    Convierte valores tipo:
    - "1.200.000"
    - "$1.200.000"
    - "35 UF"
    - "35"
    a float
    """
    if value is None:
        return None

    s = str(value).lower().strip()
    s = s.replace("$", "")
    s = s.replace(".", "")
    s = s.replace(",", ".")
    s = s.replace("uf", "").strip()

    try:
        return float(s)
    except Exception:
        return None


def pick_first(d: dict, keys: List[str]):
    for k in keys:
        if k in d and d.get(k) not in (None, "", 0, "0"):
            return d.get(k)
    return None


# =========================
# CARGA DE PROPIEDADES
# =========================

def load_properties():
    print("ENRICHED_DATA_PATH:", ENRICHED_DATA_PATH)
    print("EXISTS:", ENRICHED_DATA_PATH.exists())

    if not ENRICHED_DATA_PATH.exists():
        return []

    try:
        with open(ENRICHED_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print("TOTAL ENRICHED PROPERTIES:", len(data))
                return data
    except Exception as e:
        print("ERROR loading enriched data:", e)

    return []

ALL_PROPERTIES: List[Dict] = load_properties()


# =========================
# PRECIO (MAPEO EXPLÍCITO)
# =========================

def get_price_for_property(p: dict, operacion: Optional[str]):
    """
    Devuelve (valor, moneda)
    moneda: 'clp', 'uf' o None
    """

    op = normalize_text(operacion)

    # 🔹 AJUSTADAS PARA DATA REAL (robusto)
    ARRIENDO_UF_KEYS = [
        "Precio Arriendo UF",
        "Arriendo UF",
        "Canon UF",
    ]

    ARRIENDO_CLP_KEYS = [
        "Precio Arriendo",
        "Arriendo CLP",
        "Canon",
        "Precio Arriendo CLP",
        "Precio Arriendo $",
    ]

    VENTA_UF_KEYS = [
        "Precio Venta UF",
        "Venta UF",
        "Precio UF",
    ]

    VENTA_CLP_KEYS = [
        "Precio Venta",
        "Venta CLP",
        "Precio CLP",
        "Precio Venta CLP",
        "Precio Venta $",
    ]

    if op == "arriendo":
        raw = pick_first(p, ARRIENDO_UF_KEYS)
        if raw is not None:
            val = parse_number(raw)
            return (val, "uf") if val is not None else (None, None)

        raw = pick_first(p, ARRIENDO_CLP_KEYS)
        if raw is not None:
            val = parse_number(raw)
            return (val, "clp") if val is not None else (None, None)

    if op == "venta":
        raw = pick_first(p, VENTA_UF_KEYS)
        if raw is not None:
            val = parse_number(raw)
            return (val, "uf") if val is not None else (None, None)

        raw = pick_first(p, VENTA_CLP_KEYS)
        if raw is not None:
            val = parse_number(raw)
            return (val, "clp") if val is not None else (None, None)

    # fallback genérico
    raw = pick_first(p, ["Precio", "precio", "Valor", "valor"])
    val = parse_number(raw)
    return (val, None) if val is not None else (None, None)


# =========================
# BUSCADOR PRINCIPAL
# =========================

def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max: Optional[int] = None,
    amenities: Optional[List[str]] = None,
) -> List[Dict]:

    results: List[Dict] = []

    comuna_n = normalize_text(comuna)
    operacion_n = normalize_text(operacion)

    for p in ALL_PROPERTIES:

        # --- COMUNA ---
        if comuna_n:
            p_comuna = normalize_text(
                p.get("Comuna") or p.get("comuna")
            )
            if p_comuna != comuna_n:
                continue

        # --- OPERACIÓN ---
        if operacion_n:
            venta = normalize_text(p.get("Venta"))
            arriendo = normalize_text(p.get("Arriendo"))

            if operacion_n == "venta" and venta != "si":
                continue
            if operacion_n == "arriendo" and arriendo != "si":
                continue

        # --- PRECIO ---
        if precio_max is not None:
            val, moneda = get_price_for_property(p, operacion_n)

            # si no se puede leer el precio, NO rompe, solo descarta
            if val is None:
                continue

            # ⚠️ por ahora NO convertimos UF → CLP
            # (lo haremos explícito después)
            if val > precio_max:
                continue

        # --- AMENITIES ---
        if amenities:
            desc = normalize_text(p.get("Descripcion")) or ""
            if not all(normalize_text(a) in desc for a in amenities):
                continue

        results.append(p)

    return results
