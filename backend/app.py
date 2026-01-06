from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from backend.assistant_router import router as assistant_router
from backend.assistant_router import run_assistant_logic

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

# Mantén tu endpoint /assistant como está
app.include_router(assistant_router)

# =========================
# PROXY (ODOO ONLINE) — TOLERANTE
# =========================
@app.post("/proxy")
async def proxy(request: Request):
    # 1) Leer body crudo (sirve para JSON o texto)
    body_bytes = await request.body()
    body_text = (body_bytes or b"").decode("utf-8", errors="ignore").strip()

    # 2) Intentar parsear JSON; si falla, degradar a mensaje texto
    payload = None
    if body_text:
        try:
            payload = json.loads(body_text)
        except Exception:
            payload = {"message": body_text}
    else:
        payload = {"message": ""}

    # 3) Asegurar forma mínima esperada
    if not isinstance(payload, dict):
        payload = {"message": str(payload)}

    payload.setdefault("message", "")
    payload.setdefault("context", None)

    # 4) Ejecutar lógica real (sin HTTP interno)
    try:
        response = await run_assistant_logic(payload)
        return JSONResponse(
            status_code=200,
            content=response,
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except Exception as e:
        # Este bloque idealmente nunca debería ejecutarse si run_assistant_logic está blindado
        return JSONResponse(
            status_code=200,
            content={
                "type": "error",
                "message": "Error en proxy",
                "detail": str(e),
                "debug_payload": payload,
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )

@app.get("/")
def root():
    return {"status": "ok"}
