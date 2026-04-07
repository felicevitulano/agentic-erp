"""Tests for MarketingAgent tools and routing."""
from __future__ import annotations

import json
import pytest
from datetime import datetime
from app.agents.marketing import MarketingAgent
from app.models.marketing import Contenuto, ContattoEvento, StatoContenuto
from app.models.operations import Progetto
from app.models.sales import Opportunity


class TestMarketingTools:

    def test_crea_contenuto_minimal(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._crea_contenuto(titolo="Post AI", tipo="post_linkedin"))
        assert result["status"] == "ok"
        assert result["contenuto_id"] > 0

    def test_crea_contenuto_full(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._crea_contenuto(
            titolo="Case Study Acme",
            tipo="case_study",
            autore="Felice",
            data_pubblicazione="2026-05-01",
            contenuto_testo="Testo del case study",
            note="Da rivedere",
        ))
        assert result["status"] == "ok"
        c = db_session.query(Contenuto).filter(Contenuto.id == result["contenuto_id"]).first()
        assert c.autore == "Felice"
        assert c.data_pubblicazione == datetime(2026, 5, 1)

    def test_aggiorna_contenuto(self, db_session):
        agent = MarketingAgent(db=db_session)
        res = json.loads(agent._crea_contenuto(titolo="Draft", tipo="post_linkedin"))
        cid = res["contenuto_id"]
        result = json.loads(agent._aggiorna_contenuto(
            contenuto_id=cid, stato="in_revisione", note="Pronto per review"
        ))
        assert result["status"] == "ok"
        c = db_session.query(Contenuto).filter(Contenuto.id == cid).first()
        assert c.stato == "in_revisione"

    def test_aggiorna_contenuto_pubblicato_sets_date(self, db_session):
        agent = MarketingAgent(db=db_session)
        res = json.loads(agent._crea_contenuto(titolo="NoDate", tipo="articolo_blog"))
        cid = res["contenuto_id"]
        agent._aggiorna_contenuto(contenuto_id=cid, stato="pubblicato")
        c = db_session.query(Contenuto).filter(Contenuto.id == cid).first()
        assert c.data_pubblicazione is not None

    def test_aggiorna_contenuto_not_found(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._aggiorna_contenuto(contenuto_id=9999))
        assert result["status"] == "error"

    def test_calendario_editoriale_empty(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._calendario_editoriale())
        assert "Nessun contenuto" in result["message"]

    def test_calendario_editoriale_with_data(self, db_session):
        agent = MarketingAgent(db=db_session)
        agent._crea_contenuto(titolo="Post 1", tipo="post_linkedin")
        agent._crea_contenuto(titolo="Post 2", tipo="articolo_blog")
        result = json.loads(agent._calendario_editoriale())
        assert result["totale"] == 2

    def test_calendario_editoriale_filter_tipo(self, db_session):
        agent = MarketingAgent(db=db_session)
        agent._crea_contenuto(titolo="P1", tipo="post_linkedin")
        agent._crea_contenuto(titolo="P2", tipo="case_study")
        result = json.loads(agent._calendario_editoriale(tipo="case_study"))
        assert result["totale"] == 1

    def test_registra_contatto_evento(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._registra_contatto_evento(
            nome="Mario Rossi", evento="AI Summit 2026",
            email="mario@example.com", azienda="Acme",
            data_evento="2026-04-15", interesse="Automazione AI",
        ))
        assert result["status"] == "ok"
        assert result["contatto_evento_id"] > 0

    def test_suggerisci_contenuti_empty(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._suggerisci_contenuti())
        assert result["totale"] >= 1  # fallback suggestion always present

    def test_suggerisci_contenuti_from_projects(self, db_session):
        p = Progetto(nome="Progetto Completato", cliente="Acme", stato="completato")
        db_session.add(p)
        db_session.commit()
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._suggerisci_contenuti())
        types = [s["tipo"] for s in result["suggerimenti"]]
        assert "case_study" in types

    def test_suggerisci_contenuti_from_deals(self, db_session):
        from app.models.sales import Contact
        contact = Contact(nome="Test", cognome="C", azienda="X")
        db_session.add(contact)
        db_session.commit()
        opp = Opportunity(contact_id=contact.id, titolo="Deal Vinto", valore_stimato=10000, stato="vinto")
        db_session.add(opp)
        db_session.commit()
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._suggerisci_contenuti())
        types = [s["tipo"] for s in result["suggerimenti"]]
        assert "post_linkedin" in types

    def test_report_marketing(self, db_session):
        agent = MarketingAgent(db=db_session)
        result = json.loads(agent._report_marketing(mese=4, anno=2026))
        assert "mese" in result
        assert result["mese"] == "2026-04"


class TestMarketingRouting:

    def test_high_confidence(self, db_session):
        agent = MarketingAgent(db=db_session)
        score = agent.can_handle("crea un post linkedin sulla nostra nuova partnership")
        assert score.score > 0.1

    def test_low_confidence(self, db_session):
        agent = MarketingAgent(db=db_session)
        score = agent.can_handle("registra una fattura passiva da 5000 euro")
        assert score.score < 0.1
