import pytest
from unittest.mock import MagicMock, patch
from app.core.orchestrator import Orchestrator
from app.core.base_agent import AgentResponse, ConfidenceScore


class MockAgent:
    def __init__(self, agent_id, confidence=0.8):
        self.agent_id = agent_id
        self.agent_name = f"Mock {agent_id}"
        self.description = f"Mock agent {agent_id}"
        self._confidence = confidence

    def can_handle(self, message):
        return ConfidenceScore(score=self._confidence, reason="mock")

    def process_message(self, message, context=None):
        return AgentResponse(
            text=f"Risposta da {self.agent_id}",
            agent_id=self.agent_id,
        )


class TestOrchestrator:

    @pytest.fixture
    def orchestrator(self, db_session, test_user):
        return Orchestrator(db=db_session, user_id=test_user.id)

    def test_routes_to_best_agent(self, orchestrator):
        agent_high = MockAgent("sales", confidence=0.9)
        agent_low = MockAgent("hr", confidence=0.2)
        orchestrator.register_agent(agent_high)
        orchestrator.register_agent(agent_low)

        result = orchestrator.route_message("Mostrami la pipeline vendite")
        assert "sales" in result.agents_involved
        assert "Risposta da sales" in result.response

    def test_fallback_when_no_agent_confident(self, orchestrator):
        agent = MockAgent("sales", confidence=0.1)
        orchestrator.register_agent(agent)

        result = orchestrator.route_message("Qual e' il senso della vita?")
        assert "orchestrator" in result.agents_involved
        assert "Non sono sicuro" in result.response

    def test_creates_conversation(self, orchestrator, db_session):
        agent = MockAgent("sales", confidence=0.8)
        orchestrator.register_agent(agent)

        result = orchestrator.route_message("Test messaggio")
        assert result.conversation_id > 0

    def test_continues_conversation(self, orchestrator, db_session):
        agent = MockAgent("sales", confidence=0.8)
        orchestrator.register_agent(agent)

        result1 = orchestrator.route_message("Primo messaggio")
        result2 = orchestrator.route_message("Secondo messaggio", result1.conversation_id)
        assert result1.conversation_id == result2.conversation_id

    def test_get_agents_status(self, orchestrator):
        orchestrator.register_agent(MockAgent("sales"))
        orchestrator.register_agent(MockAgent("finance"))
        status = orchestrator.get_agents_status()
        assert len(status) == 2
        assert status[0]["id"] == "sales"
