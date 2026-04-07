"""Tests for OperationsAgent tools and routing."""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timedelta
from app.agents.operations import OperationsAgent
from app.models.operations import Progetto, Task
from app.models.hr import Collaboratore


class TestOperationsTools:

    def test_crea_progetto(self, db_session):
        agent = OperationsAgent(db=db_session)
        result = json.loads(agent._crea_progetto(
            nome="Sito Web Acme", cliente="Acme Corp", budget=50000,
            data_inizio="2026-04-01", data_fine_prevista="2026-09-30",
        ))
        assert result["status"] == "ok"
        assert result["progetto_id"] > 0

    def test_aggiorna_progetto(self, db_session):
        agent = OperationsAgent(db=db_session)
        res = json.loads(agent._crea_progetto(nome="Test Project"))
        pid = res["progetto_id"]
        result = json.loads(agent._aggiorna_progetto(
            progetto_id=pid, stato="attivo", percentuale_avanzamento=25
        ))
        assert result["status"] == "ok"

    def test_aggiorna_progetto_not_found(self, db_session):
        agent = OperationsAgent(db=db_session)
        result = json.loads(agent._aggiorna_progetto(progetto_id=9999, stato="attivo"))
        assert result["status"] == "error"

    def test_crea_task(self, db_session):
        agent = OperationsAgent(db=db_session)
        res = json.loads(agent._crea_progetto(nome="Project Alpha"))
        pid = res["progetto_id"]
        result = json.loads(agent._crea_task(
            progetto_id=pid, titolo="Design UI", priorita="alta",
            data_scadenza="2026-05-01",
        ))
        assert result["status"] == "ok"
        assert result["task_id"] > 0

    def test_crea_task_project_not_found(self, db_session):
        agent = OperationsAgent(db=db_session)
        result = json.loads(agent._crea_task(progetto_id=9999, titolo="Test"))
        assert result["status"] == "error"

    def test_aggiorna_task_completato(self, db_session):
        agent = OperationsAgent(db=db_session)
        res = json.loads(agent._crea_progetto(nome="P"))
        pid = res["progetto_id"]
        tres = json.loads(agent._crea_task(progetto_id=pid, titolo="T"))
        tid = tres["task_id"]
        result = json.loads(agent._aggiorna_task(task_id=tid, stato="completato"))
        assert result["status"] == "ok"
        task = db_session.query(Task).filter(Task.id == tid).first()
        assert task.stato == "completato"
        assert task.completed_at is not None

    def test_registra_timesheet(self, db_session):
        agent = OperationsAgent(db=db_session)
        res = json.loads(agent._crea_progetto(nome="P"))
        pid = res["progetto_id"]
        # Create a collaboratore for timesheet
        collab = Collaboratore(nome="Test", cognome="Dev", tipo="consulente")
        db_session.add(collab)
        db_session.commit()
        db_session.refresh(collab)

        result = json.loads(agent._registra_timesheet(
            collaboratore_id=collab.id, progetto_id=pid,
            data="2026-04-06", ore=6, descrizione_attivita="Sviluppo backend"
        ))
        assert result["status"] == "ok"

    def test_stato_progetti_empty(self, db_session):
        agent = OperationsAgent(db=db_session)
        result = json.loads(agent._stato_progetti())
        assert "Nessun progetto" in result["message"]

    def test_stato_progetti_with_data(self, db_session):
        agent = OperationsAgent(db=db_session)
        agent._crea_progetto(nome="P1", data_fine_prevista="2026-12-31")
        result = json.loads(agent._stato_progetti())
        assert result["totale"] >= 1
        assert result["progetti"][0]["semaforo"] == "verde"

    def test_alert_ritardi_none(self, db_session):
        agent = OperationsAgent(db=db_session)
        result = json.loads(agent._alert_ritardi())
        assert "Nessun ritardo" in result["message"]

    def test_alert_ritardi_with_overdue(self, db_session):
        agent = OperationsAgent(db=db_session)
        past = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        res = json.loads(agent._crea_progetto(nome="Late Project", data_fine_prevista=past))
        pid = res["progetto_id"]
        agent._aggiorna_progetto(progetto_id=pid, stato="attivo")
        result = json.loads(agent._alert_ritardi())
        assert result["totale_progetti_ritardo"] >= 1


class TestOperationsRouting:

    def test_high_confidence(self, db_session):
        agent = OperationsAgent(db=db_session)
        score = agent.can_handle("crea un nuovo progetto e assegna i task")
        assert score.score > 0.1

    def test_low_confidence(self, db_session):
        agent = OperationsAgent(db=db_session)
        score = agent.can_handle("registra una fattura passiva")
        assert score.score < 0.1
