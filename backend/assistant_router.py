# backend/assistant_router.py

print("🧠 assistant_router starting")

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

print("✅ APIRouter created")

class AssistantRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

print("✅ Pydantic model loaded")

@router.post("/assistant")
def assistant(req: AssistantRequest):
    return {
        "type": "results",
        "filters": {"debug": True},
        "results": [],
    }

print("✅ /assistant route registered")
