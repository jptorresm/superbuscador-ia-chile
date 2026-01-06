from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.assistant_router import router as assistant_router

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS — MODO SEGURO
# =========================
# (para desarrollo / integración externa)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ⚠️ importante para aislar el problema
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# =========================
# ROUTERS
# =========================

app.include_router(assistant_router)

# =========================
# CATCH GLOBAL DE ERRORES
# =========================
# ⚠️ ESTO ES CLAVE

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,   # 👈 evita 500
        content={
            "type": "error",
            "message": "Error interno controlado",
            "detail": str(exc),
        },
    )

# =========================
# HEALTHCHECK
# =========================

@app.get("/")
def root():
    return {"status": "ok"}
