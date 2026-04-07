from __future__ import annotations

import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.core.base_agent import BaseAgent, AgentResponse
from app.models import Conversation, Message
from app.utils.audit import log_action

logger = logging.getLogger("agentic_erp")

CONFIDENCE_THRESHOLD = 0.3


@dataclass
class OrchestratorResponse:
    response: str
    conversation_id: int
    agents_involved: list[str]
    actions: list[dict]
    needs_human_review: bool = False


class Orchestrator:
    """Coordina gli agenti AI e gestisce il routing dei messaggi."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.agents: list[BaseAgent] = []

    def register_agent(self, agent: BaseAgent):
        self.agents.append(agent)

    def route_message(
        self, message: str, conversation_id: int | None = None
    ) -> OrchestratorResponse:
        # Get or create conversation
        if conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conversation:
                conversation = self._create_conversation(message)
        else:
            conversation = self._create_conversation(message)

        # Save user message
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)
        self.db.commit()

        # Load conversation context
        context = self._build_context(conversation.id)

        # Route to best agent(s)
        scores = []
        for agent in self.agents:
            score = agent.can_handle(message)
            scores.append((agent, score))
            logger.info(f"[orchestrator] {agent.agent_id}: {score.score:.2f} ({score.reason})")

        scores.sort(key=lambda x: x[1].score, reverse=True)

        if not scores or scores[0][1].score < CONFIDENCE_THRESHOLD:
            # No agent is confident enough — use fallback
            response_text = self._fallback_response(message)
            agents_involved = ["orchestrator"]
            actions = []
        else:
            best_agent = scores[0][0]
            logger.info(f"[orchestrator] Routing a: {best_agent.agent_id}")

            # Check if multiple agents should be involved
            secondary_agents = [
                agent for agent, score in scores[1:]
                if score.score >= CONFIDENCE_THRESHOLD and score.score >= scores[0][1].score * 0.7
            ]

            if secondary_agents:
                # Multi-agent response
                result = self._multi_agent_response(
                    best_agent, secondary_agents, message, context
                )
            else:
                result = best_agent.process_message(message, context)

            response_text = result.text
            agents_involved = [result.agent_id]
            actions = result.actions

            # Update conversation main agent
            conversation.main_agent = result.agent_id
            self.db.commit()

        # Save assistant message
        assistant_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            agent_id=agents_involved[0] if agents_involved else None,
        )
        self.db.add(assistant_msg)
        self.db.commit()

        log_action(
            self.db,
            agent="orchestrator",
            action="route_message",
            user_id=self.user_id,
            details={
                "message_preview": message[:100],
                "agents_involved": agents_involved,
                "conversation_id": conversation.id,
            },
        )

        return OrchestratorResponse(
            response=response_text,
            conversation_id=conversation.id,
            agents_involved=agents_involved,
            actions=actions,
        )

    def _create_conversation(self, first_message: str) -> Conversation:
        title = first_message[:50] + ("..." if len(first_message) > 50 else "")
        conversation = Conversation(user_id=self.user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def _build_context(self, conversation_id: int) -> list[dict]:
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(20)
            .all()
        )
        messages.reverse()
        context = []
        for msg in messages:
            if msg.role in ("user", "assistant"):
                context.append({"role": msg.role, "content": msg.content})
        return context

    def _multi_agent_response(
        self,
        primary: BaseAgent,
        secondary: list[BaseAgent],
        message: str,
        context: list[dict],
    ) -> AgentResponse:
        """Compone una risposta da più agenti."""
        primary_result = primary.process_message(message, context)

        secondary_info = []
        for agent in secondary:
            try:
                result = agent.process_message(message, context)
                secondary_info.append(f"[{agent.agent_name}]: {result.text}")
            except Exception as e:
                logger.error(f"Errore agente secondario {agent.agent_id}: {e}")

        if secondary_info:
            combined = (
                f"{primary_result.text}\n\n"
                f"--- Informazioni aggiuntive ---\n"
                + "\n\n".join(secondary_info)
            )
            primary_result.text = combined

        return primary_result

    def _fallback_response(self, message: str) -> str:
        return (
            "Non sono sicuro di quale area aziendale riguardi la tua richiesta. "
            "Puoi specificare se si tratta di:\n"
            "- **Vendite** (contatti, pipeline, contratti)\n"
            "- **Finanza** (fatture, scadenzario, cash flow)\n"
            "- **Risorse Umane** (collaboratori, presenze, ferie)\n"
            "- **Operations** (progetti, task, timesheet)\n"
            "- **Marketing** (contenuti, calendario editoriale, eventi)"
        )

    def get_agents_status(self) -> list[dict]:
        return [
            {
                "id": agent.agent_id,
                "name": agent.agent_name,
                "description": agent.description,
            }
            for agent in self.agents
        ]
