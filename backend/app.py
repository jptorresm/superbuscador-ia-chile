print("🚀 app.py starting")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router as assistant_router

app = FastAPI(title="SuperBuscador IA Chile")

# CORS (Render + Worker, pero no molesta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router del asistente
app.include_router(assistant_router)

@app.get("/")
def health():
    return {"status": "ok"}

