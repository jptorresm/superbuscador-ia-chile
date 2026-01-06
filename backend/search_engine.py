from typing import List, Optional, Any
from backend.data_loader import load_sources

# =========================
# DATA
# =========================

ALL_PROPERTIES = load_sources()

# =========================
# NORMALIZADORES
# =========================

def comuna_to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        nombre = value.get("nombre")
        if isinstance(nombre, str):
            return nombre.strip()
    return None


def operacion_match(prop: dict, operacion: str) -> bool:
    if not operacion:
        return True

    if prop.get("operacion") == operacion:
        return True

    if operacion == "arriendo" and prop.get("Arriendo") == "Sí":
        return True

    if operacion == "venta" and prop.get("Venta") == "Sí":
        return True

    return False

# =========================
# PRECIOS (BLINDADO)
# =========================

def get_precio_venta(prop: dict):
    precio_root = prop.get("precio")
    if not isinstance(precio_root, dict):
        return None

    precio = precio_root.get("venta")
    if not isinstance(precio, dict):
        return None

    if not precio.get("activo"):
        return None

    return precio


def get_precio_arriendo(prop: dict):
    precio_root = prop.get("precio")
    if not isinstance(precio_root, dict):
        return None

    precio = precio_root.get("arriendo")
    if not isinstance(precio, dict):
        return None

    if not precio.get("activo"):
        return None

    return precio


def cumple_precio(prop: dict, filtros: dict) -> bool:
    """
    Lógica ORIGINAL:
    - Venta → UF primero, luego CLP
    - Arriendo → CLP primero
    - Si no hay datos suficientes → NO descartar
    """

    operacion = filtros.get("operacion")
    max_uf = filtros.get("precio_max_uf")
    max_clp = filtros.get("precio_max_clp")

    # -----------------------
    # VENTA
    # -----------------------
    if operacion == "venta":
        precio = get_precio_venta(prop)
        if not precio:
            return False

        uf = precio.get("uf")
        clp = precio.get("pesos")

        if max_uf is not None and uf is not None:
            return uf <= max_uf

        if max_clp is not None and clp is not None:
            return clp <= max_clp

        return True

    # -----------------------
    # ARRIENDO
    # -----------------------
    if operacion == "arriendo":
        precio = get_precio_arriendo(prop)
        if not precio:
            return False

        clp = precio.get("pesos")
        uf = precio.get("uf")

        if max_clp is not None and clp is not None:
            return clp <= max_clp

        if max_uf is not None and uf is not None:
            return uf <= max_uf

        return True

    return True

# =========================
# SEARCH ENGINE
# =========================

def search_properties(
    comuna: Optional[Any] = None,
    operacion: Optional[str] = None,
    precio_max_uf: Optional[int] = None,
    precio_max_clp: Optional[int] = None,
    amenities: Optional[List[str]] = None,
):
    results: List[dict] = []

    filtro_comuna = comuna_to_str(comuna)

    for prop in ALL_PROPERTIES:

        # -----------------------
        # Comuna
        # -----------------------
        if filtro_comuna:
            prop_comuna = comuna_to_str(prop.get("comuna"))
            if not prop_comuna:
                continue
            if prop_comuna.lower() != filtro_comuna.lower():
                continue

        # -----------------------
        # Operación
        # -----------------------
        if operacion:
            if not operacion_match(prop, operacion):
                continue

        # -----------------------
        # Precio
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
