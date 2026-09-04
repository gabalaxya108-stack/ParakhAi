from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from backend.app.services.ai.grok_assistant import NirikshaAssistantService

router = APIRouter(prefix="/assistant")

class AssistantChatRequest(BaseModel):
    message: str = Field(..., description="Inspector natural language query")
    inspection_id: Optional[str] = Field(None, description="Optional active inspection context")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Previous multi-turn conversation messages")

class AssistantChatResponse(BaseModel):
    assistant_name: str
    model: str
    reply: str
    evidence_used: Dict[str, Any]
    status: str

@router.post("/chat", response_model=AssistantChatResponse)
def chat_with_niriksha(payload: AssistantChatRequest = Body(...)):
    """
    POST /api/v1/assistant/chat
    Communicates with NIRIKSHA, the PARAKH AI Conversational Regulatory Assistant.
    Powered by Groq Ultra-Fast AI with statutory database grounding.
    """
    service = NirikshaAssistantService()
    res = service.chat(
        user_query=payload.message,
        context_inspection_id=payload.inspection_id,
        history=payload.history
    )
    return AssistantChatResponse(**res)
