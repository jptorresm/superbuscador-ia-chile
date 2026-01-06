from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

from backend.assistant_router import router as assistant_router

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
# ROUTER REAL
# =========================
app.include_router(assistant_router)

# =========================
# PROXY (ODOO ONLINE)
# =========================
@app.post("/proxy")
async def proxy(request: Request):
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "http://localhost:8000/assistant",
                content=body,
                headers={"Content-Type": "application/json"},
            )

        return JSONResponse(
            status_code=200,
            content=resp.json(),
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
