# backend/assistant_router.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from backend.search_engine import search_properties
from backend.utils import clean_for_json

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/assistant")
def assistant(req: AssistantRequest):
    # hardcode inicial para validar pipeline
    results = search_properties(
        operacion="arriendo",
        comuna="Providencia"
    )

    return clean_for_json({
        "type": "results",
        "filters": {
            "operacion": "arriendo",
            "comuna": "Providencia"
        },
        "results": results[:10]
    })
