import json
from pathlib import Path

# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_SOURCES_DIR = BASE_DIR / "data" / "sources"

# UF de referencia (luego se puede conectar a API real)
UF_REFERENCIA = 37000


# =========================
# UTILIDADES
# =========================

def uf_to_clp(uf_value) -> int | None:
    try:
        return int(float(uf_value) * UF_REFERENCIA)
    except Exception:
        return None


def normalize_price(p: dict, operacion: str | None) -> int | None:
    """
    Decide el precio correcto según la estructura Nexxos:
    - Venta / Arriendo = Sí / No
    - Precio en CLP o UF
    """

    if not operacion:
        return None

    # Normalizar valores texto
    venta = str(p.get("Venta", "")).strip().lower()
    arriendo = str(p.get("Arriendo", "")).strip().lower()

    # -----------------------
    # ARRIENDO
    # -----------------------
    if operacion == "arriendo" and arriendo == "si":
        if p.get("Precio Arriendo CLP"):
            return int(p["Precio Arriendo CLP"])
        if p.get("Precio Arriendo UF"):
            return uf_to_clp(p["Precio Arriendo UF"])

    # -----------------------
    # VENTA
    # -----------------------
    if operacion == "venta" and venta == "si":
        if p.get("Precio Venta CLP"):
            return int(p["Precio Venta CLP"])
        if p.get("Precio Venta UF"):
            return uf_to_clp(p["Precio Venta UF"])

    return None


def build_property_url(p: dict) -> str | None:
    source = p.get("source")
    codigo = p.get("Codigo") or p.get("codigo")

    if source == "nexxos" and codigo:
        return f"https://nexxospropiedades.cl/fichaPropiedad.aspx?i={codigo}"

    return None


# =========================
# CARGA DE DATOS
# =========================

def load_properties():
    properties = []

    if not DATA_SOURCES_DIR.exists():
        return properties

    for file in DATA_SOURCES_DIR.glob("*.json"):
        source_name = file.stem
        data = json.loads(file.read_text(encoding="utf-8"))

        for p in data:
            p["source"] = source_name
            properties.append(p)

    return properties


# =========================
# MATCHERS
# =========================

def match_comuna(p, comuna):
    if not comuna:
        return True
    return comuna.lower() in str(p.get("Comuna", "")).lower()


def match_operacion(p, operacion):
    if not operacion:
        return True

    if operacion == "venta":
        return str(p.get("Venta", "")).lower() == "si"

    if operacion == "arriendo":
        return str(p.get("Arriendo", "")).lower() == "si"

    return False


# =========================
# SEARCH ENGINE
# =========================

def search_properties(
    comuna: str | None = None,
    operacion: str | None = None,
    precio_max: int | None = None,
    limit: int = 10,
):
    properties = load_properties()
    results = []

    for p in properties:
        # Filtro comuna
        if not match_comuna(p, comuna):
            continue

        # Filtro operación
        if not match_operacion(p, operacion):
            continue

        # Normalizar precio según operación
        precio = normalize_price(p, operacion)

        # Si hay presupuesto, validar
        if precio_max is not None:
        # si no logro determinar precio, NO filtro
        if precio is not None and precio > precio_max:
        continue


        # 👉 NORMALIZACIÓN FINAL PARA FRONTEND
        p_out = {
            "titulo": p.get("Titulo") or "Propiedad",
            "comuna": p.get("Comuna"),
            "precio": precio,
            "dormitorios": p.get("Dormitorios"),
            "banos": p.get("Baños") or p.get("Banos"),
            "source": p.get("source"),
            "url": build_property_url(p),
        }

        results.append(p_out)

        if len(results) >= limit:
            break

    return results
