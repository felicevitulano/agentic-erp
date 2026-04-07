from __future__ import annotations

import json
import logging
from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from app.models import User, get_db, Conversation, Message
from app.auth.jwt import get_current_user, decode_token
from app.schemas.chat import ChatMessage, ChatResponse, ConversationResponse, MessageResponse
from app.core.orchestrator import Orchestrator
from app.agents import get_all_agents

logger = logging.getLogger("agentic_erp")

router = APIRouter(prefix="/api", tags=["chat"])


def _create_orchestrator(db: Session, user_id: int) -> Orchestrator:
    orchestrator = Orchestrator(db=db, user_id=user_id)
    for agent_cls in get_all_agents():
        agent = agent_cls(db=db, user_id=user_id)
        orchestrator.register_agent(agent)
    return orchestrator


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orchestrator = _create_orchestrator(db, current_user.id)
    result = orchestrator.route_message(request.message, request.conversation_id)
    return ChatResponse(
        response=result.response,
        conversation_id=result.conversation_id,
        agent_id=result.agents_involved[0] if result.agents_involved else "orchestrator",
        actions=result.actions,
        needs_human_review=result.needs_human_review,
    )


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # Validate token
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    orchestrator = _create_orchestrator(db, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            result = orchestrator.route_message(
                message_data.get("message", ""),
                message_data.get("conversation_id"),
            )

            await websocket.send_json({
                "type": "response",
                "response": result.response,
                "conversation_id": result.conversation_id,
                "agent_id": result.agents_involved[0] if result.agents_involved else "orchestrator",
                "actions": result.actions,
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnesso per utente {user_id}")
    except Exception as e:
        logger.error(f"Errore WebSocket: {e}")
        await websocket.close(code=4000)


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
        .all()
    )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        return []
    return conversation.messages
