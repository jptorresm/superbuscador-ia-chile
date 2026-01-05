import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_DATA_PATH = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"

# =========================
# LOAD DATA (ONCE)
# =========================
def load_properties() -> List[Dict[str, Any]]:
    print("ENRICHED_DATA_PATH:", ENRICHED_DATA_PATH)
    print("EXISTS:", ENRICHED_DATA_PATH.exists())

    if not ENRICHED_DATA_PATH.exists():
        return []

    try:
        with open(ENRICHED_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                print("TOTAL ENRICHED PROPERTIES:", len(data))
                return data
    except Exception as e:
        print("❌ ERROR loading enriched data:", e)

    return []


ALL_PROPERTIES = load_properties()

# =========================
# UTILS
# =========================
def normalize_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return (
        str(value)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )


# =========================
# MAIN SEARCH
#
