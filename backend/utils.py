# backend/utils.py
import math

def clean_for_json(obj):
    """
    Limpia cualquier estructura (dict / list) eliminando:
    - NaN
    - Infinity
    - -Infinity

    FastAPI / JSON NO soportan estos valores.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]

    return obj
