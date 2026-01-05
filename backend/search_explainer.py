def explain_results(query: str, filters: dict, results: list[dict]) -> str:
    """
    Explicación descriptiva y neutra de resultados.
    """

    count = len(results)

    if count == 0:
        return (
            "No se encontraron propiedades que coincidan con los criterios "
            "de búsqueda indicados."
        )

    parts = []

    # Operación
    operacion = filters.get("operacion")
    if operacion:
        parts.append(f"en {operacion}")

    # Comuna
    comuna = filters.get("comuna")
    if comuna:
        parts.append(f"en {comuna}")

    # Precio
    if filters.get("precio_min_uf"):
        parts.append(f"desde {filters['precio_min_uf']} UF")
    if filters.get("precio_max_uf"):
        parts.append(f"hasta {filters['precio_max_uf']} UF")

    if filters.get("precio_min_clp"):
        parts.append(f"desde ${filters['precio_min_clp']}")
    if filters.get("precio_max_clp"):
        parts.append(f"hasta ${filters['precio_max_clp']}")

    criteria = " ".join(parts)

    return f"Se encontraron {count} propiedades {criteria}."
