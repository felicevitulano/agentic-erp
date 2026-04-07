from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from anthropic import Anthropic, APIError, RateLimitError
from sqlalchemy.orm import Session
from app.config import get_settings
from app.utils.audit import log_action

logger = logging.getLogger("agentic_erp")

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


@dataclass
class AgentResponse:
    text: str
    actions: list[dict] = field(default_factory=list)
    needs_human_review: bool = False
    structured_data: dict | None = None
    agent_id: str = ""


@dataclass
class ConfidenceScore:
    score: float  # 0.0 - 1.0
    reason: str


class BaseAgent(ABC):
    """Classe base per tutti gli agenti AI di Agentic ERP."""

    def __init__(self, db: Session, user_id: int | None = None):
        self.db = db
        self.user_id = user_id
        self.settings = get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Identificativo univoco dell'agente (es. 'sales', 'finance')."""

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Nome visualizzabile dell'agente."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrizione delle competenze dell'agente per il routing."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Prompt di sistema specifico per il dominio dell'agente."""

    @abstractmethod
    def get_tools(self) -> list[dict]:
        """Definizione dei tool esposti alla Claude API."""

    @abstractmethod
    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Esegue un tool e restituisce il risultato come stringa."""

    def can_handle(self, message: str) -> ConfidenceScore:
        """Valuta se l'agente e' competente per il messaggio (0.0 - 1.0)."""
        keywords = self._get_keywords()
        message_lower = message.lower()
        matches = sum(1 for kw in keywords if kw in message_lower)
        if not keywords:
            return ConfidenceScore(score=0.0, reason="Nessuna keyword definita")
        score = min(matches / max(len(keywords) * 0.1, 1), 1.0)
        return ConfidenceScore(
            score=score,
            reason=f"Trovate {matches}/{len(keywords)} keyword di dominio",
        )

    @abstractmethod
    def _get_keywords(self) -> list[str]:
        """Lista di keyword per il matching rapido del dominio."""

    def process_message(
        self, message: str, context: list[dict] | None = None
    ) -> AgentResponse:
        """Processa un messaggio utente con Claude API + tool use."""
        messages = list(context) if context else []
        messages.append({"role": "user", "content": message})

        tools = self.get_tools()
        all_actions = []

        for _ in range(10):  # max tool use iterations
            response = self._call_claude(messages, tools)

            if response.stop_reason == "end_turn":
                text = self._extract_text(response)
                return AgentResponse(
                    text=text,
                    actions=all_actions,
                    agent_id=self.agent_id,
                )

            if response.stop_reason == "tool_use":
                assistant_content = response.content
                messages.append({"role": "assistant", "content": assistant_content})

                tool_results = []
                for block in assistant_content:
                    if block.type == "tool_use":
                        logger.info(f"[{self.agent_id}] Tool call: {block.name}({block.input})")
                        try:
                            result = self.execute_tool(block.name, block.input)
                            all_actions.append({
                                "tool": block.name,
                                "input": block.input,
                                "result": result,
                            })
                            log_action(
                                self.db,
                                agent=self.agent_id,
                                action=block.name,
                                user_id=self.user_id,
                                details={"input": block.input, "result": result},
                            )
                        except Exception as e:
                            result = f"Errore nell'esecuzione del tool: {str(e)}"
                            logger.error(f"[{self.agent_id}] Tool error: {e}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                text = self._extract_text(response)
                return AgentResponse(text=text, agent_id=self.agent_id)

        return AgentResponse(
            text="Ho raggiunto il limite massimo di operazioni. Riprova con una richiesta piu' specifica.",
            agent_id=self.agent_id,
        )

    def _call_claude(self, messages: list[dict], tools: list[dict]):
        """Chiama Claude API con retry e backoff esponenziale."""
        for attempt in range(MAX_RETRIES):
            try:
                kwargs = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": self.get_system_prompt(),
                    "messages": messages,
                }
                if tools:
                    kwargs["tools"] = tools
                return self.client.messages.create(**kwargs)
            except RateLimitError:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"[{self.agent_id}] Rate limit, retry in {delay}s...")
                    time.sleep(delay)
                else:
                    raise
            except APIError as e:
                if attempt < MAX_RETRIES - 1 and e.status_code and e.status_code >= 500:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(f"[{self.agent_id}] API error {e.status_code}, retry in {delay}s...")
                    time.sleep(delay)
                else:
                    raise

    def _extract_text(self, response) -> str:
        """Estrae il testo dalla risposta Claude."""
        texts = []
        for block in response.content:
            if hasattr(block, "text"):
                texts.append(block.text)
        return "\n".join(texts) if texts else "Non ho una risposta per questa richiesta."
