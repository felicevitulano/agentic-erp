import json
import pytest
from app.agents.sales import SalesAgent
from app.models.sales import Contact, Opportunity, Contract, SAL, PipelineState


class TestSalesTools:
    """Testa i tool del Sales Agent in isolamento (senza Claude API)."""

    @pytest.fixture
    def agent(self, db_session, test_user):
        return SalesAgent(db=db_session, user_id=test_user.id)

    @pytest.fixture
    def sample_contact(self, db_session):
        contact = Contact(nome="Mario", cognome="Rossi", azienda="Acme Srl", email="mario@acme.it")
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)
        return contact

    @pytest.fixture
    def sample_opportunity(self, db_session, sample_contact):
        opp = Opportunity(
            contact_id=sample_contact.id,
            titolo="Progetto AI",
            valore_stimato=50000,
            stato=PipelineState.LEAD.value,
        )
        db_session.add(opp)
        db_session.commit()
        db_session.refresh(opp)
        return opp

    def test_crea_contatto(self, agent):
        result = json.loads(agent.execute_tool("crea_contatto", {
            "nome": "Luca",
            "cognome": "Bianchi",
            "azienda": "Tech Srl",
            "email": "luca@tech.it",
        }))
        assert result["status"] == "ok"
        assert result["contact_id"] > 0

    def test_cerca_contatti(self, agent, sample_contact):
        result = json.loads(agent.execute_tool("cerca_contatti", {"query": "Rossi"}))
        assert result["count"] == 1
        assert result["results"][0]["azienda"] == "Acme Srl"

    def test_cerca_contatti_no_results(self, agent):
        result = json.loads(agent.execute_tool("cerca_contatti", {"query": "ZZZ"}))
        assert result["count"] == 0

    def test_crea_opportunita(self, agent, sample_contact):
        result = json.loads(agent.execute_tool("crea_opportunita", {
            "contact_id": sample_contact.id,
            "titolo": "Nuovo Progetto",
            "valore_stimato": 30000,
        }))
        assert result["status"] == "ok"
        assert result["opportunity_id"] > 0

    def test_crea_opportunita_contact_not_found(self, agent):
        result = json.loads(agent.execute_tool("crea_opportunita", {
            "contact_id": 9999,
            "titolo": "Test",
            "valore_stimato": 1000,
        }))
        assert result["status"] == "error"

    def test_aggiorna_pipeline_valid(self, agent, sample_opportunity):
        result = json.loads(agent.execute_tool("aggiorna_pipeline", {
            "opportunity_id": sample_opportunity.id,
            "nuovo_stato": "qualificato",
        }))
        assert result["status"] == "ok"

    def test_aggiorna_pipeline_invalid_transition(self, agent, sample_opportunity):
        result = json.loads(agent.execute_tool("aggiorna_pipeline", {
            "opportunity_id": sample_opportunity.id,
            "nuovo_stato": "vinto",
        }))
        assert result["status"] == "error"
        assert "non valida" in result["message"]

    def test_aggiorna_pipeline_perso_without_reason(self, agent, sample_opportunity):
        result = json.loads(agent.execute_tool("aggiorna_pipeline", {
            "opportunity_id": sample_opportunity.id,
            "nuovo_stato": "perso",
        }))
        assert result["status"] == "error"
        assert "obbligatorio" in result["message"]

    def test_aggiorna_pipeline_perso_with_reason(self, agent, sample_opportunity):
        result = json.loads(agent.execute_tool("aggiorna_pipeline", {
            "opportunity_id": sample_opportunity.id,
            "nuovo_stato": "perso",
            "motivo_perdita": "prezzo",
        }))
        assert result["status"] == "ok"

    def test_aggiorna_pipeline_vinto_creates_contract(self, agent, db_session, sample_contact):
        # Create opportunity in negoziazione state
        opp = Opportunity(
            contact_id=sample_contact.id,
            titolo="Deal vinto",
            valore_stimato=100000,
            stato=PipelineState.NEGOZIAZIONE.value,
        )
        db_session.add(opp)
        db_session.commit()
        db_session.refresh(opp)

        result = json.loads(agent.execute_tool("aggiorna_pipeline", {
            "opportunity_id": opp.id,
            "nuovo_stato": "vinto",
        }))
        assert result["status"] == "ok"
        assert "contract_id" in result

        contract = db_session.query(Contract).filter(Contract.opportunity_id == opp.id).first()
        assert contract is not None
        assert contract.valore_totale == 100000

    def test_registra_sal(self, agent, db_session, sample_contact):
        contract = Contract(
            opportunity_id=1, contact_id=sample_contact.id,
            titolo="Test", valore_totale=50000,
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)

        result = json.loads(agent.execute_tool("registra_sal", {
            "contract_id": contract.id,
            "percentuale_avanzamento": 30,
            "importo_maturato": 15000,
            "descrizione": "Prima milestone",
        }))
        assert result["status"] == "ok"

    def test_report_pipeline_empty(self, agent):
        result = json.loads(agent.execute_tool("report_pipeline", {}))
        assert "Nessuna" in result["message"]

    def test_report_pipeline_with_data(self, agent, sample_opportunity):
        result = json.loads(agent.execute_tool("report_pipeline", {}))
        assert result["totale_opportunita"] == 1

    def test_report_perdite_empty(self, agent):
        result = json.loads(agent.execute_tool("report_perdite", {}))
        assert "Nessuna" in result["message"]


class TestSalesAgentRouting:
    """Testa il confidence scoring per il routing."""

    @pytest.fixture
    def agent(self, db_session, test_user):
        return SalesAgent(db=db_session, user_id=test_user.id)

    def test_high_confidence_sales_message(self, agent):
        score = agent.can_handle("Mostrami le trattative della pipeline vendite con i contatti lead")
        assert score.score > 0.3

    def test_low_confidence_non_sales_message(self, agent):
        score = agent.can_handle("Qual e' il meteo oggi?")
        assert score.score < 0.3

    def test_medium_confidence_ambiguous(self, agent):
        score = agent.can_handle("Mostrami i contatti del progetto")
        assert score.score > 0
