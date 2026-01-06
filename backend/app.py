from backend.assistant_router import run_assistant_logic

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
        # Este bloque YA NO debería activarse nunca
        return JSONResponse(
            status_code=200,
            content={
                "type": "error",
                "message": "Error en proxy",
                "detail": str(e),
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )
