# backend/assistant_router.py

print("🧠 assistant_router starting")

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.search_engine import search_properties

router = APIRouter()

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/assistant")
def assistant(req: AssistantRequest):
    results = search_properties(operacion="arriendo")

    return {
        "type": "results",
        "filters": {"operacion": "arriendo"},
        "results": results[:5],
    }
