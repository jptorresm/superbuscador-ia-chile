from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
ENRICHED_FILE = BASE_DIR / "data" / "enriched" / "nexxos_enriched.json"

def load_sources():
    if not ENRICHED_FILE.exists():
        raise RuntimeError(f"Missing enriched file: {ENRICHED_FILE}")

    with open(ENRICHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
