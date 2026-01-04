from fastapi import APIRouter
from pydantic import BaseModel
from backend.ai_interpreter import interpret_message

router = APIRouter(prefix="", tags=["assistant"])

class AssistantRequest(BaseModel):
    message: str

@router.post("/assistant")
def assistant(req: AssistantRequest):
    """
    Endpoint conversacional:
    - interpreta
    - decide ask vs search
    - NO ejecuta búsqueda
    """
    decision = interpret_message(req.message)
    return decision
