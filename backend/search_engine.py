# backend/search_engine.py
print("🧠 search_engine imported")

from typing import List, Optional, Any
from backend.data_loader import load_enriched

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

def operacion_match(prop: dict, operacion: Optional[str]) -> bool:
    if not operacion:
        return True
    return prop.get("operacion") == operacion

def cumple_precio(prop: dict, filtros: dict) -> bool:
    # Por ahora, no filtrar por precio (evita edge cases mientras cerramos Render)
    return True

def search_properties(
    comuna: Optional[Any] = None,
    operacion: Optional[str] = None,
    precio_max_uf: Optional[int] = None,
    precio_max_clp: Optional[int] = None,
    amenities: Optional[List[str]] = None,
):
    print("🔍 search_properties called")

    properties = load_enriched()
    results: List[dict] = []

    filtro_comuna = comuna_to_str(comuna)

    for prop in properties:
        if filtro_comuna:
            prop_comuna = comuna_to_str(prop.get("ubicacion", {}).get("comuna"))
            if not prop_comuna or prop_comuna.lower() != filtro_comuna.lower():
                continue

        if operacion and not operacion_match(prop, operacion):
            continue

        if amenities:
            prop_amenities = prop.get("amenities", {})
            if not all(prop_amenities.get(a) for a in amenities):
                continue

        results.append(prop)

    print(f"✅ search_properties results: {len(results)}")
    return results
