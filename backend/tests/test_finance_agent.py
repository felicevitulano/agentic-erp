"""Tests for FinanceAgent tools and routing."""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone, timedelta
from app.agents.finance import FinanceAgent
from app.models.finance import Fattura


class TestFinanceTools:
    """Test Finance agent tool implementations."""

    def test_registra_fattura_attiva(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._registra_fattura(
            tipo="attiva",
            numero="FT-2026-001",
            importo=10000,
            data_scadenza="2026-05-15",
            fornitore_o_cliente="Acme Corp",
        ))
        assert result["status"] == "ok"
        assert result["fattura_id"] > 0

        fattura = db_session.query(Fattura).filter(Fattura.id == result["fattura_id"]).first()
        assert fattura.importo == 10000
        assert fattura.iva == 22.0
        assert fattura.importo_totale == 12200.0
        assert fattura.tipo == "attiva"

    def test_registra_fattura_passiva(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._registra_fattura(
            tipo="passiva",
            numero="FP-2026-001",
            importo=5000,
            iva=10,
            data_scadenza="2026-04-30",
            fornitore_o_cliente="Fornitore XYZ",
        ))
        assert result["status"] == "ok"
        fattura = db_session.query(Fattura).filter(Fattura.id == result["fattura_id"]).first()
        assert fattura.importo_totale == 5500.0
        assert fattura.tipo == "passiva"

    def test_registra_fattura_duplicata(self, db_session):
        agent = FinanceAgent(db=db_session)
        agent._registra_fattura(
            tipo="attiva", numero="FT-DUP", importo=1000,
            data_scadenza="2026-05-01", fornitore_o_cliente="Test"
        )
        result = json.loads(agent._registra_fattura(
            tipo="attiva", numero="FT-DUP", importo=2000,
            data_scadenza="2026-05-01", fornitore_o_cliente="Test2"
        ))
        assert result["status"] == "error"
        assert "gia'" in result["message"]

    def test_aggiorna_stato_pagata(self, db_session):
        agent = FinanceAgent(db=db_session)
        res = json.loads(agent._registra_fattura(
            tipo="attiva", numero="FT-PAG", importo=3000,
            data_scadenza="2026-05-01", fornitore_o_cliente="Cliente A"
        ))
        fid = res["fattura_id"]

        result = json.loads(agent._aggiorna_stato_fattura(
            fattura_id=fid, nuovo_stato="pagata", data_pagamento="2026-04-20"
        ))
        assert result["status"] == "ok"

        fattura = db_session.query(Fattura).filter(Fattura.id == fid).first()
        assert fattura.stato == "pagata"
        assert fattura.data_pagamento is not None

    def test_aggiorna_stato_not_found(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._aggiorna_stato_fattura(fattura_id=9999, nuovo_stato="pagata"))
        assert result["status"] == "error"

    def test_scadenzario_empty(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._scadenzario())
        assert "Nessuna scadenza" in result["message"]

    def test_scadenzario_with_data(self, db_session):
        agent = FinanceAgent(db=db_session)
        # Create a fattura due in 10 days
        future = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        agent._registra_fattura(
            tipo="attiva", numero="FT-SCAD", importo=5000,
            data_scadenza=future, fornitore_o_cliente="Cliente Scad"
        )
        result = json.loads(agent._scadenzario(giorni=30))
        assert result["totale"] >= 1
        assert result["scadenze"][0]["numero"] == "FT-SCAD"

    def test_cash_flow_previsionale(self, db_session):
        agent = FinanceAgent(db=db_session)
        # Create entrate and uscite for this month
        now = datetime.now(timezone.utc)
        scadenza = (now + timedelta(days=5)).strftime("%Y-%m-%d")

        agent._registra_fattura(
            tipo="attiva", numero="FT-CF-E", importo=10000,
            data_scadenza=scadenza, fornitore_o_cliente="Entrata"
        )
        agent._registra_fattura(
            tipo="passiva", numero="FT-CF-U", importo=3000,
            data_scadenza=scadenza, fornitore_o_cliente="Uscita"
        )
        result = json.loads(agent._cash_flow_previsionale(mesi=1))
        assert result["mesi_analizzati"] == 1
        assert len(result["cash_flow"]) == 1
        cf = result["cash_flow"][0]
        assert cf["entrate_previste"] == 12200.0  # 10000 + 22% IVA
        assert cf["uscite_previste"] == 3660.0
        assert cf["saldo_previsto"] == 8540.0

    def test_report_mensile_empty(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._report_mensile())
        assert result["entrate"] == 0
        assert result["uscite"] == 0

    def test_fatture_scadute_none(self, db_session):
        agent = FinanceAgent(db=db_session)
        result = json.loads(agent._fatture_scadute())
        assert "Nessuna fattura attiva scaduta" in result["message"]

    def test_fatture_scadute_with_alert(self, db_session):
        agent = FinanceAgent(db=db_session)
        # Create overdue invoice (40 days ago)
        past = (datetime.now(timezone.utc) - timedelta(days=40)).strftime("%Y-%m-%d")
        agent._registra_fattura(
            tipo="attiva", numero="FT-OVER", importo=8000,
            data_scadenza=past, fornitore_o_cliente="Cliente Scaduto"
        )
        result = json.loads(agent._fatture_scadute())
        assert result["totale"] == 1
        assert result["alert_oltre_30gg"] == 1
        assert result["fatture_scadute"][0]["alert_30gg"] is True


class TestFinanceAgentRouting:
    """Test Finance agent keyword routing."""

    def test_high_confidence_finance_message(self, db_session):
        agent = FinanceAgent(db=db_session)
        score = agent.can_handle("registra una fattura attiva per Acme")
        assert score.score > 0.1  # "fattura" keyword matches

    def test_low_confidence_non_finance_message(self, db_session):
        agent = FinanceAgent(db=db_session)
        score = agent.can_handle("crea un progetto per il sito web")
        assert score.score < 0.1

    def test_medium_confidence_ambiguous(self, db_session):
        agent = FinanceAgent(db=db_session)
        score = agent.can_handle("mostrami il report mensile del cash flow e le fatture scadute")
        assert score.score > 0.1
