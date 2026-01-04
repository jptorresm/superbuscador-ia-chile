from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# =========================
# APP
# =========================
app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (SIEMPRE ANTES DE ROUTERS)
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
