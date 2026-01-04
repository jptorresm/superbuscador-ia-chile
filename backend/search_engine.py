from pathlib import Path
import json
import unicodedata
from typing import List, Dict, Optional

# =========================
# PATHS (estructura real)
# =========================
# Repo:
# project-root/
# ├── backend/
# │   └── search_engine.py
# └── data/
#     └── sources/
#         └── *.json

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"


# =========================
# UTILIDADES
# =========================

def normalize_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = str(text).lower().strip()
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def safe_int(value) -> Optional[int]:
    try:
        return int(float(value))
    except Exception:
        return None


# =========================
# CARGA DE DATA
# =========================

def load_properties() -> List[Dict]:
    properties: List[Dict] = []

    print("BASE_DIR:", BASE_DIR)
    print("DATA_SOURCES_DIR:", DATA_SOURCES_DIR)
    print("EXISTS:", DATA_SOURCES_DIR.exists())

    if not DATA_SOURCES_DIR.exists():
        return properties

    for file in DATA_SOURCES_DIR.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

                if not isinstance(data, list):
                    print(f"WARNING: {file.name} no es una lista")
                    continue

                for p in data:
                    if isinstance(p, dict):
                        p["_source"] = file.stem
                        properties.append(p)
        except Exception as e:
            print(f"ERROR loading {file.name}:", e)

    print("TOTAL PROPERTIES LOADED:", len(properties))
    return properties


ALL_PROPERTIES: List[Dict] = load_properties()


# =========================
# BUSCADOR PRINCIPAL
# =========================

def search_properties(
    comuna: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max: Optional[int] = None,
    amenities: Optional[List[str]] = None,
) -> List[Dict]:

    results: List[Dict] = []

    comuna_n = normalize_text(comuna)
    operacion_n = normalize_text(operacion)

    for p in ALL_PROPERTIES:

        # -----------------
        # COMUNA
        # -----------------
        if comuna_n:
            p_comuna = normalize_text(
                p.get("Comuna") or
                p.get("comuna") or
                p.get("COMUNA")
            )
            if p_comuna != comuna_n:
                continue

        # -----------------
        # OPERACIÓN
        # -----------------
        if operacion_n:
            venta = normalize_text(p.get("Venta"))
            arriendo = normalize_text(p.get("Arriendo"))

            if operacion_n == "venta" and venta != "si":
                continue
            if operacion_n == "arriendo" and arriendo != "si":
                continue

        # -----------------
        # PRECIO
        # -----------------
        if precio_max is not None:
            precio = (
                p.get("Precio") or
                p.get("precio") or
                p.get("Precio CLP")
            )

            precio_i = safe_int(precio)
            if precio_i is None:
                continue

            if precio_i > precio_max:
                continue

        # -----------------
        # AMENITIES (básico)
        # -----------------
        if amenities:
            descripcion = normalize_text(
                p.get("Descripcion") or p.get("descripcion")
            ) or ""
            if not all(normalize_text(a) in descripcion for a in amenities):
                continue

        results.append(p)

    return results
