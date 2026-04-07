from typing import Dict, List, Optional

from pydantic import BaseModel
from datetime import datetime


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: int
    agent_id: str
    actions: List[Dict] = []
    needs_human_review: bool = False


class ConversationResponse(BaseModel):
    id: int
    title: str
    main_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    agent_id: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
