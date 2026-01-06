from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.assistant_router import assistant as assistant_handler
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
# ROUTER NORMAL
# =========================
app.include_router(assistant_router)

# =========================
# PROXY (SIN HTTP INTERNO)
# =========================
@app.post("/proxy")
async def proxy(request: Request):
    try:
        payload = await request.json()
        # llamamos DIRECTO al handler real
        response = await assistant_handler(payload)
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
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "ok"}
