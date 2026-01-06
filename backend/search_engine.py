from pathlib import Path
import json
from typing import List, Optional

# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "sources"

# =========================
# CARGA DE DATOS
# =========================

def load_sources() -> List[dict]:
    """
    Carga todos los JSON de propiedades desde data/sources
    y asegura que cada propiedad tenga source definido.
    """
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
# UTILIDADES DE PRECIO
# =========================

def get_precio_venta(prop: dict):
    precio = prop.get("precio", {}).get("venta", {})
    if not precio.get("activo"):
        return None
    return {
        "uf": precio.get("uf"),
        "pesos": precio.get("pesos"),
        "divisa": precio.get("divisa"),
    }


def get_precio_arriendo(prop: dict):
    precio = prop.get("precio", {}).get("arriendo", {})
    if not precio.get("activo"):
        return None
    return {
        "uf": precio.get("uf"),
        "pesos": precio.get("pesos"),
        "divisa": precio.get("divisa"),
    }


def cumple_precio(prop: dict, filtros: dict) -> bool:
    """
    Regla ÚNICA y clara (tu lógica original):

    - Venta:
        * Comparar UF si existe
        * Si no, comparar CLP
        * Si no hay datos suficientes → NO descartar

    - Arriendo:
        * Comparar CLP
        * UF solo si explícitamente viene

    - Si no hay filtros de precio → NO descartar
    """

    operacion = filtros.get("operacion")
    max_uf = filtros.get("precio_max_uf")
    max_clp = filtros.get("precio_max_clp")

    if operacion == "venta":
        precio = get_precio_venta(prop)
        if not precio:
            return False

        if max_uf is not None and precio.get("uf") is not None:
            return precio["uf"] <= max_uf

        if max_clp is not None and precio.get("pesos") is not None:
            return precio["pesos"] <= max_clp

        return True

    if operacion == "arriendo":
        precio = get_precio_arriendo(prop)
        if not precio:
            return False

        if max_clp is not None and precio.get("pesos") is not None:
            return precio["pesos"] <= max_clp

        if max_uf is not None and precio.get("uf") is not None:
            return precio["uf"] <= max_uf

        return True

    return True

# =========================
# SEARCH ENGINE PRINCIPAL
# =========================

def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max_uf: Optional[int] = None,
    precio_max_clp: Optional[int] = None,
    amenities: Optional[List[str]] = None,
):
    """
    Motor de búsqueda REAL.
    Toda la lógica de filtrado vive aquí.
    El assistant SOLO decide cuándo llamar y con qué parámetros.
    """

    results = []

    for prop in ALL_PROPERTIES:

        # -----------------------
        # Comuna (robusta)
        # -----------------------
        if comuna:
            prop_comuna = prop.get("comuna")

            if not prop_comuna:
                continue

            # Si viene como dict, extraer nombre
            if isinstance(prop_comuna, dict):
                prop_comuna = prop_comuna.get("nombre")

            if not isinstance(prop_comuna, str):
                continue

            if prop_comuna.lower() != comuna.lower():
                continue


        # -----------------------
        # Operación
        # -----------------------
        if operacion:
            if prop.get("operacion") != operacion:
                continue

        # -----------------------
        # Precio (núcleo del sistema)
        # -----------------------
        if not cumple_precio(
            prop,
            {
                "operacion": operacion,
                "precio_max_uf": precio_max_uf,
                "precio_max_clp": precio_max_clp,
            }
        ):
            continue

        # -----------------------
        # Amenities
        # -----------------------
        if amenities:
            prop_amenities = prop.get("amenities", {})
            if not all(prop_amenities.get(a) for a in amenities):
                continue

        results.append(prop)

    return results
