def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max_uf: int | None = None,
    precio_max_clp: int | None = None,
    amenities: list[str] | None = None,
):
    results = []

    for prop in ALL_PROPERTIES:

        # 🔒 Seguridad básica
        if not isinstance(prop, dict):
            continue

        # -----------------------
        # FILTROS BÁSICOS
        # -----------------------
        if comuna and prop.get("comuna") != comuna:
            continue

        if operacion and prop.get("operacion") != operacion:
            continue

        # -----------------------
        # PRECIO (TOLERANTE)
        # -----------------------
        precio = prop.get("precio_normalizado")

        if precio is not None:
            try:
                precio = int(precio)
            except Exception:
                precio = None

        if precio_max_clp and precio:
            if precio > precio_max_clp:
                continue

        if precio_max_uf and precio:
            if precio > precio_max_uf:
                continue

        results.append(prop)

    return results
