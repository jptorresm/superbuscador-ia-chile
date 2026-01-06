from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router as assistant_router

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS — MODO COMPATIBLE ODOO
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 IMPORTANTE
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================
app.include_router(assistant_router)

@app.get("/")
def root():
    return {"status": "ok"}
