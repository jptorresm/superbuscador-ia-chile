from pathlib import Path
import json
import math

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sources"


# =========================
# CARGA DE FUENTES
# =========================

def load_sources() -> list[dict]:
    properties = []

    for file in DATA_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                p["source"] = file.stem
                properties.append(p)

    return properties


ALL_PROPERTIES = load_sources()


# =========================
# UTILIDADES
# =========================

def to_int(value):
    """
    Convierte valores tipo '12.300,00' o '135.114.198,00' a int
    """
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


def extract_price(prop: dict) -> dict:
    """
    Extrae y normaliza el precio desde estructura Nexxos real,
    tolerante a variantes de nombre de campo.
    """

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

    def get_any(prop, keys):
        for k in keys:
            if k in prop and prop[k] not in (None, "", 0):
                return prop[k]
        return None

    # Flags
    en_venta = str(get_any(prop, ["En Venta", "EnVenta", "venta"])).upper() == "SI"
    en_arriendo = str(get_any(prop, ["En Arriendo", "EnArriendo", "arriendo"])).upper() == "SI"

    # Divisa
    divisa = str(
        get_any(prop, ["Divisa ppal.", "Divisa ppal", "Divisa", "moneda"])
        or ""
    ).strip().upper()

    # Precio principal
    precio_ppal = to_int(
        get_any(
            prop,
            [
                "Precio ppal.",
                "Precio ppal",
                "Precio Principal",
                "precio_ppal",
                "precio",
            ],
        )
    )

    # ------------------
    # VENTA
    # ------------------
    if en_venta and precio_ppal:
        if divisa == "UF":
            return {"precio": precio_ppal, "precio_moneda": "UF"}
        if divisa in ("$", "CLP", "PESOS"):
            return {"precio": precio_ppal, "precio_moneda": "CLP"}

    # ------------------
    # ARRIENDO
    # ------------------
    if en_arriendo and precio_ppal:
        return {"precio": precio_ppal, "precio_moneda": "CLP"}

    return {"precio": None, "precio_moneda": None}

    # ------------------
    # VENTA
    # ------------------
    if en_venta and precio_ppal:
        if divisa == "UF":
            return {
                "precio": precio_ppal,
                "precio_moneda": "UF"
            }
        if divisa in ("$", "CLP", "PESOS"):
            return {
                "precio": precio_ppal,
                "precio_moneda": "CLP"
            }

    # ------------------
    # ARRIENDO
    # ------------------
    if en_arriendo and precio_ppal:
        return {
            "precio": precio_ppal,
            "precio_moneda": "CLP"
        }

    return {
        "precio": None,
        "precio_moneda": None
    }


def clean_for_json(obj):
    """
    Limpia NaN para serialización JSON segura
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


# =========================
# FILTRO DE PRECIO
# =========================

def cumple_precio(prop: dict, filtros: dict) -> bool:
    operacion = filtros.get("operacion")

    precio_max_uf = filtros.get("precio_max_uf")
    precio_max_clp = filtros.get("precio_max_clp")

    price_data = extract_price(prop)
    precio = price_data.get("precio")
    moneda = price_data.get("precio_moneda")

    # 🟢 VENTA → UF primero
    if operacion == "venta":
        if precio is None:
            return True

        if moneda == "UF" and precio_max_uf:
            return precio <= precio_max_uf

        if moneda == "CLP" and precio_max_clp:
            return precio <= precio_max_clp

        return True

    # 🟡 ARRIENDO → CLP
    if operacion == "arriendo":
        if precio is None:
            return True

        if precio_max_clp:
            return precio <= precio_max_clp

        return True

    return True


# =========================
# BÚSQUEDA PRINCIPAL
# =========================

def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max_uf: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    results = []

    for prop in ALL_PROPERTIES:

        if comuna and prop.get("comuna", "").lower() != comuna.lower():
            continue

        if operacion and prop.get("operacion") != operacion:
            continue

        if not cumple_precio(
            prop,
            {
                "operacion": operacion,
                "precio_max_uf": precio_max_uf,
                "precio_max_clp": precio_max_clp,
            }
        ):
            continue

        # 💰 Normalizar precio para salida
        price_data = extract_price(prop)
        prop["precio"] = price_data["precio"]
        prop["precio_moneda"] = price_data["precio_moneda"]

        results.append(clean_for_json(prop))

    return results
