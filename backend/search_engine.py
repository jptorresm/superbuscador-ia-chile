from typing import List, Optional, Any

from backend.data_loader import load_sources

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
        return nombre.strip() if isinstance(nombre, str) else None
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
# PRECIOS
# =========================

def get_precio_venta(prop: dict):
    precio = prop.get("precio", {}).get("venta", {})
    if not precio.get("activo"):
        return None
    return precio


def get_precio_arriendo(prop: dict):
    precio = prop.get("precio", {}).get("arriendo", {})
    if not precio.get("activo"):
        return None
    return precio


def cumple_precio(prop: dict, filtros: dict) -> bool:
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
# SEARCH PRINCIPAL
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

        if filtro_comuna:
            prop_comuna = comuna_to_str(prop.get("comuna"))
            if not prop_comuna:
                continue
            if prop_comuna.lower() != filtro_comuna.lower():
                continue

        if operacion:
            if not operacion_match(prop, operacion):
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

        if amenities:
            prop_amenities = prop.get("amenities", {})
            if not all(prop_amenities.get(a) for a in amenities):
                continue

        results.append(prop)

    return results
