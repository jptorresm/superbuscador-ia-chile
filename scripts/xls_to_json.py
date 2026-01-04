import pandas as pd
import json
import sys
import re
from pathlib import Path

BASE_URL = "https://nexxospropiedades.cl/fichaPropiedad.aspx?i="

AMENITIES_KEYWORDS = {
    "piscina": ["piscina", "pileta"],
    "gimnasio": ["gimnasio", "gym"],
    "quincho": ["quincho", "parrilla", "asadera"],
    "terraza": ["terraza"],
    "patio": ["patio"],
    "bodega": ["bodega"],
    "loggia": ["loggia", "lavandería"],
    "amoblado": ["amoblado", "equipado"],
    "areas_verdes": ["áreas verdes", "jardín", "parque"],
    "ascensor": ["ascensor", "elevador"],
    "conserjeria": ["conserjería", "conserje", "portero"]
}

def clean_codigo(value):
    if pd.isna(value):
        return None
    return str(value).replace(".", "").replace("-", "").replace(" ", "").strip()

def to_bool(value):
    if pd.isna(value):
        return False
    return str(value).strip().lower() in ["si", "sí", "x", "true", "1"]

def extract_amenities(text):
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return {}
    text = str(text).lower().strip()
    if not text:
        return {}

    amenities = {}
    for amenity, keywords in AMENITIES_KEYWORDS.items():
        amenities[amenity] = any(
            re.search(rf"\b{re.escape(k)}\b", text) for k in keywords
        )
    return amenities

def load_column_map():
    with open("scripts/column_map.json", "r", encoding="utf-8") as f:
        return json.load(f)

def find_column(df_columns, possible_names):
    for col in df_columns:
        if col in possible_names:
            return col
    return None

def main(excel_path: str):
    # Encabezados están en la fila 7 -> header=6 (0-index)
    df = pd.read_excel(excel_path, header=6)

    # Elimina columnas "Unnamed"
    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed")]

    column_map = load_column_map()
    results = []

    for _, row in df.iterrows():
        item = {}

        # Copia campos según el mapeo
        for field, possible_cols in column_map.items():
            col = find_column(df.columns, possible_cols)
            if col:
                item[field] = row[col]

        # Código (obligatorio)
        codigo = clean_codigo(item.get("codigo"))
        if not codigo:
            continue

        # Filtros de calidad mínimos
        if str(item.get("estado", "")).strip().lower() != "activa":
            continue
        if not to_bool(item.get("publicada_web")):
            continue

        # Normalizaciones base + compatibilidad futura (multi-fuente)
        item["codigo"] = codigo
        item["id"] = f"nexxos-{codigo}"
        item["source"] = "nexxos"
        item["source_id"] = codigo
        item["link"] = f"{BASE_URL}{codigo}"

        # Operación: En Venta = SI => venta, si no => arriendo
        item["operacion"] = "venta" if to_bool(item.get("operacion")) else "arriendo"

        # Flags
        item["exclusiva"] = to_bool(item.get("exclusiva"))
        item["destacada"] = to_bool(item.get("destacada"))

        # Amenities desde texto libre
        descripcion = item.get("descripcion", "")
        item["amenities"] = extract_amenities(descripcion)

        results.append(item)

    # Output
    output_path = Path("data/nexxos/properties.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ Exportadas {len(results)} propiedades a {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/xls_to_json.py archivo.xlsx")
        sys.exit(1)
    main(sys.argv[1])
