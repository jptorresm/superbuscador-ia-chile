from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import router as assistant_router
from backend.assistant_router import run_assistant_logic

# =========================
# APP
# =========================

app = FastAPI(title="SuperBuscador IA Chile")

# =========================
# CORS (simple y estable)
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# =========================
# ROUTERS
# =========================

app.include_router(assistant_router)

# =========================
# PROXY (ODOO ONLINE)
# =========================

@app.post("/proxy")
async def proxy(request: Request):
    try:
        payload = await request.json()
        response = await run_assistant_logic(payload)
        return JSONResponse(
            status_code=200,
            content=response,
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
# ROOT / HEALTH
# =========================

@app.get("/")
def root():
    return {"status": "ok"}
