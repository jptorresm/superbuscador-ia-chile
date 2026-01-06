from typing import List, Optional, Any
from backend.data_loader import load_sources

# =========================
# DATA
# =========================

ALL_PROPERTIES = load_sources()

UF_REFERENCIA = 37000  # valor de referencia estable

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
    """
    Acepta múltiples formas reales de Nexxos / enriched
    """
    if not operacion:
        return True

    # forma directa
    if prop.get("operacion") == operacion:
        return True

    # formas típicas Nexxos
    if operacion == "arriendo":
        return prop.get("Arriendo") == "Sí" or prop.get("arriendo") is True

    if operacion == "venta":
        return prop.get("Venta") == "Sí" or prop.get("venta") is True

    return False

# =========================
# PRECIOS (CONTRATO REAL ENRICHED)
# =========================

def get_precio_bloque(prop: dict, operacion: str) -> Optional[dict]:
    """
    En enriched:
    - si existe precio.principal > 0 → es válido
    - NO dependemos de flags 'activo'
    """
    precio_root = prop.get("precio")
    if not isinstance(precio_root, dict):
        return None

    bloque = precio_root.get(operacion)
    if not isinstance(bloque, dict):
        return None

    principal = bloque.get("principal")
    if isinstance(principal, (int, float)) and principal > 0:
        return bloque

    return None


def cumple_precio(prop: dict, filtros: dict) -> bool:
    operacion = filtros.get("operacion")
    max_uf = filtros.get("precio_max_uf")
    max_clp = filtros.get("precio_max_clp")

    if not operacion:
        return True

    bloque = get_precio_bloque(prop, operacion)
    if not bloque:
        return False

    valor = bloque.get("principal")
    divisa = bloque.get("divisa")

    if not isinstance(valor, (int, float)) or valor <= 0:
        return False

    # -----------------------
    # FILTRO EN CLP
    # -----------------------
    if max_clp is not None:
        if divisa == "UF":
            return valor * UF_REFERENCIA <= max_clp
        return valor <= max_clp

    # -----------------------
    # FILTRO EN UF
    # -----------------------
    if max_uf is not None:
        if divisa == "UF":
            return valor <= max_uf
        return (valor / UF_REFERENCIA) <= max_uf

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
        # Comuna (tolerante)
        # -----------------------
        if filtro_comuna:
            prop_comuna = comuna_to_str(prop.get("comuna"))
            if not prop_comuna:
                continue
            if filtro_comuna.lower() not in prop_comuna.lower():
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

# =========================
# JSON SAFE (ANTI-NaN)
# =========================

import math

def clean_for_json(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    else:
        return obj
