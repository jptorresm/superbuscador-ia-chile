from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (simple)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# =========================
# ROUTER
# =========================
app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok"}
