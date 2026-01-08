from backend.data_bootstrap import bootstrap_data

# Cache simple en memoria (evita re-bootstrapping en cada request)
_DATA_CACHE = None


def load_sources(force_reload: bool = False):
    """
    Carga las propiedades ya enriquecidas y normalizadas.
    Esta es la ÚNICA puerta de entrada de datos al sistema.
    """

    global _DATA_CACHE

    if _DATA_CACHE is None or force_reload:
        _DATA_CACHE = bootstrap_data()

    return _DATA_CACHE
