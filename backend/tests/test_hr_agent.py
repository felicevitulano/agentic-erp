"""Tests for HRAgent tools and routing."""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timedelta
from app.agents.hr import HRAgent
from app.models.hr import Collaboratore


class TestHRTools:

    def test_crea_collaboratore(self, db_session):
        agent = HRAgent(db=db_session)
        result = json.loads(agent._crea_collaboratore(
            nome="Mario", cognome="Rossi", tipo="consulente",
            email="mario@test.it", tariffa_giornaliera=400,
            competenze=["Python", "React"],
        ))
        assert result["status"] == "ok"
        assert result["collaboratore_id"] > 0

    def test_cerca_collaboratori(self, db_session):
        agent = HRAgent(db=db_session)
        agent._crea_collaboratore(nome="Luca", cognome="Bianchi", tipo="dipendente")
        result = json.loads(agent._cerca_collaboratori(query="Luca"))
        assert result["count"] == 1
        assert "Luca" in result["results"][0]["nome"]

    def test_registra_presenza(self, db_session):
        agent = HRAgent(db=db_session)
        res = json.loads(agent._crea_collaboratore(nome="Anna", cognome="Verdi", tipo="consulente"))
        cid = res["collaboratore_id"]
        result = json.loads(agent._registra_presenza(collaboratore_id=cid, data="2026-04-06", ore=6))
        assert result["status"] == "ok"

    def test_registra_presenza_not_found(self, db_session):
        agent = HRAgent(db=db_session)
        result = json.loads(agent._registra_presenza(collaboratore_id=9999, data="2026-04-06"))
        assert result["status"] == "error"

    def test_gestisci_ferie(self, db_session):
        agent = HRAgent(db=db_session)
        res = json.loads(agent._crea_collaboratore(nome="Paolo", cognome="Neri", tipo="dipendente"))
        cid = res["collaboratore_id"]
        result = json.loads(agent._gestisci_ferie(
            collaboratore_id=cid, tipo="ferie",
            data_inizio="2026-08-01", data_fine="2026-08-15"
        ))
        assert result["status"] == "ok"
        assert result["assenza_id"] > 0

    def test_contratti_in_scadenza_none(self, db_session):
        agent = HRAgent(db=db_session)
        result = json.loads(agent._contratti_in_scadenza())
        assert "Nessun contratto" in result["message"]

    def test_contratti_in_scadenza_found(self, db_session):
        agent = HRAgent(db=db_session)
        scadenza = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        agent._crea_collaboratore(
            nome="Marco", cognome="Gialli", tipo="consulente",
            data_inizio_contratto="2026-01-01", data_fine_contratto=scadenza,
        )
        result = json.loads(agent._contratti_in_scadenza(giorni=30))
        assert result["totale"] >= 1

    def test_report_presenze_empty(self, db_session):
        agent = HRAgent(db=db_session)
        result = json.loads(agent._report_presenze())
        assert result["totale_giorni"] == 0


class TestHRAgentRouting:

    def test_high_confidence(self, db_session):
        agent = HRAgent(db=db_session)
        score = agent.can_handle("registra le presenze del collaboratore")
        assert score.score > 0.1

    def test_low_confidence(self, db_session):
        agent = HRAgent(db=db_session)
        score = agent.can_handle("crea una fattura per il fornitore")
        assert score.score < 0.1
