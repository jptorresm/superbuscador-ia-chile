from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router as assistant_router

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS — DEFINITIVO
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.t4global.cl",
        "https://t4global.cl",
        "http://localhost:8069",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================

app.include_router(assistant_router)

# =========================
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {"status": "ok"}
