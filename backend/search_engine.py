from typing import List, Optional, Any
from backend.data_loader import load_sources

ALL_PROPERTIES = load_sources()


def comuna_match(prop: dict, comuna: Optional[str]) -> bool:
    if not comuna:
        return True
    ubicacion = prop.get("ubicacion", {})
    return ubicacion.get("comuna", "").lower() == comuna.lower()


def operacion_match(prop: dict, operacion: Optional[str]) -> bool:
    if not operacion:
        return True
    return prop.get("operacion") == operacion


def precio_match(prop: dict, precio_max_clp: Optional[int], precio_max_uf: Optional[int]) -> bool:
    """
    Lógica REAL según enriched:
    - El precio está en precio.valor + precio.moneda
    - Si no hay precio → NO FILTRAR
    """

    precio = prop.get("precio", {})
    valor = precio.get("valor")
    moneda = precio.get("moneda")

    if valor is None or moneda is None:
        return True  # no descartamos

    if moneda == "CLP" and precio_max_clp is not None:
        return valor <= precio_max_clp

    if moneda == "UF" and precio_max_uf is not None:
        return valor <= precio_max_uf

    return True


def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max_clp: Optional[int] = None,
    precio_max_uf: Optional[int] = None,
):
    results: List[dict] = []

    for prop in ALL_PROPERTIES:

        if not comuna_match(prop, comuna):
            continue

        if not operacion_match(prop, operacion):
            continue

        if not precio_match(prop, precio_max_clp, precio_max_uf):
            continue

        results.append(prop)

    return results
