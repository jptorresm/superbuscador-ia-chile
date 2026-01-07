# backend/data_loader.py
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_FILE = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"

def load_enriched():
    print("📦 data_loader.load_enriched() called")
    print("📍 ENRICHED_FILE =", ENRICHED_FILE)
    print("📍 exists =", ENRICHED_FILE.exists())

    if not ENRICHED_FILE.exists():
        raise RuntimeError(f"Missing enriched file: {ENRICHED_FILE}")

    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"✅ enriched loaded: {len(data)} records")
    return data
