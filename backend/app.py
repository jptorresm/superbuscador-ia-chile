from backend.data_bootstrap import run_enrichment

run_enrichment()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =========================
# APP
# =========================
app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (ANTES DE TODO)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.t4global.cl",
        "https://t4global.cl",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================
from backend.assistant_router import router as assistant_router
app.include_router(assistant_router)

# =========================
# ROOT (TEST)
# =========================
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "SuperBuscador IA Chile"
    }
@app.post("/cors-test")
def cors_test():
    return {"ok": True}
