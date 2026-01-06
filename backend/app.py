from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests

from backend.assistant_router import router as assistant_router

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (simple, seguro)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# =========================
# ROUTER REAL
# =========================
app.include_router(assistant_router)

# =========================
# PROXY (CLAVE PARA ODOO ONLINE)
# =========================
@app.post("/proxy")
async def proxy(request: Request):
    body = await request.body()

    try:
        # llamada interna al assistant REAL
        r = requests.post(
            "http://localhost:8000/assistant",
            data=body,
            headers={"Content-Type": "application/json"},
            timeout=20,
        )

        return JSONResponse(
            status_code=200,
            content=r.json(),
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "type": "error",
                "message": "Error en proxy",
                "detail": str(e),
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "ok"}
