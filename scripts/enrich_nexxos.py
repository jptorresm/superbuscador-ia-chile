from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = BASE_DIR / "data" / "sources" / "nexxos.json"
OUT_DIR = BASE_DIR / "data" / "enriched"
OUT_PATH = OUT_DIR / "nexxos_enriched.json"


# =========================
# HELPERS
# =========================
def to_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("si", "sí", "true", "1", "yes"):
        return True
    if s in ("no", "false", "0"):
        return False
    return None


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except Exception:
        return None


def pick(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d.get(k) not in (None, "", {}):
            return d.get(k)
    return None


def normalize_operacion(op: Any) -> Optional[str]:
    if not op:
        return None
    s = str(op).strip().lower()
    if s in ("venta",):
        return "venta"
    if s in ("arriendo", "arriendo mensual", "rent"):
        return "arriendo"
    return s


def normalize_tipo(t: Any) -> Optional[str]:
    if not t:
        return None
    s = str(t).strip().lower()
    # Puedes ampliar después
    mapping = {
        "depto": "departamento",
        "departamento": "departamento",
        "casa": "casa",
        "oficina": "oficina",
        "terreno": "terreno",
        "local": "local",
        "bodega": "bodega",
    }
    return mapping.get(s, s)


def macro_zona_from_comuna(comuna: Optional[str]) -> Optional[str]:
    # MVP: lo dejamos simple; luego hacemos una tabla real.
    if not comuna:
        return None
    # Ejemplos mínimos, amplías cuando quieras
    sur = {"san joaquin", "la florida", "puente alto", "san miguel", "la cisterna"}
    oriente = {"las condes", "vitacura", "providencia", "lo barnechea", "la reina", "nunoa", "ñuñoa"}
    centro = {"santiago", "estacion central", "independencia", "recoleta"}

    c = comuna.strip().lower()
    if c in sur:
        return "Santiago Sur"
    if c in oriente:
        return "Santiago Oriente"
    if c in centro:
        return "Santiago Centro"
    return None


# =========================
# ENRICH
# =========================
def enrich_one(p: Dict[str, Any]) -> Dict[str, Any]:
    source = pick(p, "source") or "nexxos"
    source_id = pick(p, "source_id", "codigo")
    pid = pick(p, "id") or (f"{source}-{source_id}" if source_id else None)

    operacion = normalize_operacion(pick(p, "operacion", "Operacion"))
    moneda = pick(p, "moneda", "Moneda")

    comuna = pick(p, "comuna", "Comuna")
    region = pick(p, "region", "Region")
    sector = pick(p, "sector", "Sector")

    precio = {
    "venta": {
        "activo": bool(precio_venta.get("uf") or precio_venta.get("pesos")),
        "uf": precio_venta.get("uf"),
        "pesos": precio_venta.get("pesos"),
    },
    "arriendo": {
        "activo": bool(precio_arriendo.get("pesos") or precio_arriendo.get("uf")),
        "pesos": precio_arriendo.get("pesos"),
        "uf": precio_arriendo.get("uf"),
    },
}


    enriched = {
        "id": pid,
        "source": source,
        "source_id": str(source_id) if source_id is not None else None,
        "link": pick(p, "link"),

        "estado": (pick(p, "estado") or "").strip().lower() or None,
        "publicada_web": to_bool(pick(p, "publicada_web")),

        "operacion": operacion,
        "tipo": normalize_tipo(pick(p, "tipo", "Tipo")),

        "precio": precio,

        "ubicacion": {
            "region": region,
            "comuna": comuna,
            "sector": sector,
            "macro_zona": macro_zona_from_comuna(comuna),
            "cercano_metro": None,  # lo calculamos después si traes metro/coords/texto
            "lat": pick(p, "lat", "latitude"),
            "lng": pick(p, "lng", "longitude"),
        },

        "caracteristicas": {
            "dormitorios": safe_int(pick(p, "dormitorios", "Dormitorios")),
            "banos": safe_int(pick(p, "banos", "Baños", "Banos")),
            "superficie_util_m2": safe_int(pick(p, "superficie_util_m2", "util_m2", "m2_util")),
            "superficie_total_m2": safe_int(pick(p, "superficie_total_m2", "total_m2", "m2_total")),
            "estacionamientos": safe_int(pick(p, "estacionamientos", "Estacionamientos")),
            "bodegas": safe_int(pick(p, "bodegas", "Bodegas")),
            "gastos_comunes_clp": safe_int(pick(p, "gastos_comunes")),
        },

        # amenities: si viene dict, lo pasamos tal cual (luego lo normalizamos)
        "amenities": pick(p, "amenities") if isinstance(pick(p, "amenities"), dict) else {},

        # capa IA para más adelante
        "perfil_ia": {
            "orientacion": [],
            "target": [],
            "nivel_precio": None,
            "liquidez_estimada": None,
        },

        "flags": {},

        # siempre guardamos raw para auditoría
        "raw": p,
    }

    return enriched


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"No existe {RAW_PATH}")

    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("nexxos.json debe ser una lista de propiedades")

    enriched = [enrich_one(p) for p in raw if isinstance(p, dict)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: generado {OUT_PATH}")
    print(f"Registros: {len(enriched)}")


if __name__ == "__main__":
    main()
