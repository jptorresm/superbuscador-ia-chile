from pathlib import Path
import json
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "enriched"

def load_sources() -> List[dict]:
    properties: List[dict] = []

    for file in DATA_DIR.glob("*_enriched.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                p["source"] = file.stem
                properties.append(p)

    return properties
