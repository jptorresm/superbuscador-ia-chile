from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router as assistant_router

print("🔥 APP STARTING — app.py cargado")

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (OBLIGATORIO)
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.t4global.cl",
        "https://t4global.cl",
        "http://localhost:3000",
        "http://localhost:8069",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================

app.include_router(assistant_router)

# =========================
# HEALTHCHECK
# =========================

@app.get("/")
def health():
    return {"status": "ok"}
