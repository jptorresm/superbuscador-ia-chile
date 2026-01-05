import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def run_enrichment():
    script = BASE_DIR / "scripts" / "enrich_nexxos.py"
    if script.exists():
        subprocess.run(["python", str(script)], check=True)
