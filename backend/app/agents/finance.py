from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.core.base_agent import BaseAgent, ConfidenceScore
from app.models.finance import Fattura, TipoFattura, StatoFattura


class FinanceAgent(BaseAgent):
    AGENT_ID = "finance"
    AGENT_NAME = "Agente Finanza"
    DESCRIPTION = "Gestisce fatture, scadenzario, cash flow e reportistica finanziaria"

    @property
    def agent_id(self) -> str:
        return self.AGENT_ID

    @property
    def agent_name(self) -> str:
        return self.AGENT_NAME

    @property
    def description(self) -> str:
        return self.DESCRIPTION

    def get_system_prompt(self) -> str:
        return """Sei l'Agente Finanza di Agentic ERP per Think Next S.r.l.
Gestisci fatture attive e passive, scadenzario, cash flow previsionale e reportistica mensile.

Rispondi sempre in italiano. Sii conciso e professionale.
Quando registri fatture, calcola automaticamente l'importo totale con IVA.
Segnala proattivamente le fatture scadute e le problematiche di cash flow.
Usa formattazione tabellare per report e scadenzari.

Tipi fattura: attiva (emessa ai clienti), passiva (ricevuta dai fornitori).
Stati fattura: emessa, pagata, scaduta.
Una fattura attiva scaduta da oltre 30 giorni genera un alert automatico."""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "registra_fattura",
                "description": "Registra una nuova fattura attiva o passiva",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tipo": {"type": "string", "enum": ["attiva", "passiva"], "description": "Tipo fattura"},
                        "numero": {"type": "string", "description": "Numero fattura (es. FT-2026-001)"},
                        "importo": {"type": "number", "description": "Importo netto in EUR"},
                        "iva": {"type": "number", "description": "Aliquota IVA (default 22)", "default": 22},
                        "data_scadenza": {"type": "string", "description": "Data scadenza YYYY-MM-DD"},
                        "fornitore_o_cliente": {"type": "string", "description": "Nome fornitore o cliente"},
                        "contract_id": {"type": "integer", "description": "ID contratto collegato (opzionale)"},
                        "data_emissione": {"type": "string", "description": "Data emissione YYYY-MM-DD (default oggi)"},
                        "note": {"type": "string", "description": "Note (opzionale)"},
                    },
                    "required": ["tipo", "numero", "importo", "data_scadenza", "fornitore_o_cliente"],
                },
            },
            {
                "name": "aggiorna_stato_fattura",
                "description": "Aggiorna lo stato di una fattura (es. segna come pagata)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "fattura_id": {"type": "integer", "description": "ID fattura"},
                        "nuovo_stato": {"type": "string", "enum": ["emessa", "pagata", "scaduta"], "description": "Nuovo stato"},
                        "data_pagamento": {"type": "string", "description": "Data pagamento YYYY-MM-DD (per stato pagata)"},
                        "note": {"type": "string", "description": "Note aggiuntive"},
                    },
                    "required": ["fattura_id", "nuovo_stato"],
                },
            },
            {
                "name": "scadenzario",
                "description": "Mostra lo scadenzario fatture con filtri per periodo e stato",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "giorni": {"type": "integer", "description": "Prossimi N giorni (default 30)", "default": 30},
                        "tipo": {"type": "string", "enum": ["attiva", "passiva", "tutte"], "description": "Filtra per tipo"},
                        "solo_non_pagate": {"type": "boolean", "description": "Mostra solo non pagate", "default": True},
                    },
                },
            },
            {
                "name": "cash_flow_previsionale",
                "description": "Calcola il cash flow previsionale per i prossimi mesi",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mesi": {"type": "integer", "description": "Numero mesi avanti (default 3)", "default": 3},
                    },
                },
            },
            {
                "name": "report_mensile",
                "description": "Report entrate/uscite mensile con confronto mese precedente",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mese": {"type": "integer", "description": "Mese (1-12, default mese corrente)"},
                        "anno": {"type": "integer", "description": "Anno (default anno corrente)"},
                    },
                },
            },
            {
                "name": "fatture_scadute",
                "description": "Elenco fatture attive scadute con alert per quelle oltre 30 giorni",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handlers = {
            "registra_fattura": self._registra_fattura,
            "aggiorna_stato_fattura": self._aggiorna_stato_fattura,
            "scadenzario": self._scadenzario,
            "cash_flow_previsionale": self._cash_flow_previsionale,
            "report_mensile": self._report_mensile,
            "fatture_scadute": self._fatture_scadute,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' non riconosciuto."
        return handler(**tool_input)

    def _get_keywords(self) -> list[str]:
        return [
            "fattura", "fatture", "invoice", "bolletta",
            "scadenza", "scadenze", "scadenzario", "pagamento", "pagamenti",
            "cash flow", "flusso di cassa", "liquidita", "liquidità",
            "entrate", "uscite", "incasso", "incassi",
            "iva", "imponibile", "netto", "lordo",
            "fornitore", "fornitori", "costo", "costi",
            "report mensile", "bilancio", "finanza", "finanziario",
        ]

    # --- Tool implementations ---

    def _registra_fattura(self, tipo: str, numero: str, importo: float,
                          data_scadenza: str, fornitore_o_cliente: str, **kwargs) -> str:
        existing = self.db.query(Fattura).filter(Fattura.numero == numero).first()
        if existing:
            return json.dumps({"status": "error", "message": f"Fattura con numero '{numero}' gia' esistente"})

        iva = kwargs.get("iva", 22.0)
        importo_totale = importo * (1 + iva / 100)

        fattura = Fattura(
            tipo=tipo,
            numero=numero,
            importo=importo,
            iva=iva,
            importo_totale=importo_totale,
            data_scadenza=datetime.strptime(data_scadenza, "%Y-%m-%d").replace(tzinfo=timezone.utc),
            fornitore_o_cliente=fornitore_o_cliente,
            contract_id=kwargs.get("contract_id"),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_emissione"):
            fattura.data_emissione = datetime.strptime(kwargs["data_emissione"], "%Y-%m-%d").replace(tzinfo=timezone.utc)

        self.db.add(fattura)
        self.db.commit()
        self.db.refresh(fattura)

        return json.dumps({
            "status": "ok",
            "message": f"Fattura {numero} registrata: {importo:,.2f} EUR + IVA {iva}% = {importo_totale:,.2f} EUR - {fornitore_o_cliente}",
            "fattura_id": fattura.id,
        })

    def _aggiorna_stato_fattura(self, fattura_id: int, nuovo_stato: str, **kwargs) -> str:
        fattura = self.db.query(Fattura).filter(Fattura.id == fattura_id).first()
        if not fattura:
            return json.dumps({"status": "error", "message": f"Fattura {fattura_id} non trovata"})

        fattura.stato = nuovo_stato
        if nuovo_stato == "pagata":
            dp = kwargs.get("data_pagamento")
            fattura.data_pagamento = (
                datetime.strptime(dp, "%Y-%m-%d").replace(tzinfo=timezone.utc) if dp
                else datetime.now(timezone.utc)
            )
        if kwargs.get("note"):
            fattura.note = kwargs["note"]

        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Fattura {fattura.numero} aggiornata a '{nuovo_stato}'",
            "fattura_id": fattura.id,
        })

    def _scadenzario(self, **kwargs) -> str:
        giorni = kwargs.get("giorni", 30)
        tipo = kwargs.get("tipo", "tutte")
        solo_non_pagate = kwargs.get("solo_non_pagate", True)

        now = datetime.now(timezone.utc)
        limit = now + timedelta(days=giorni)

        query = self.db.query(Fattura).filter(Fattura.data_scadenza <= limit)
        if tipo != "tutte":
            query = query.filter(Fattura.tipo == tipo)
        if solo_non_pagate:
            query = query.filter(Fattura.stato != StatoFattura.PAGATA.value)

        fatture = query.order_by(Fattura.data_scadenza).all()

        if not fatture:
            return json.dumps({"message": f"Nessuna scadenza nei prossimi {giorni} giorni."})

        items = []
        for f in fatture:
            days_to = (f.data_scadenza.replace(tzinfo=timezone.utc) - now).days if f.data_scadenza else 0
            items.append({
                "id": f.id,
                "numero": f.numero,
                "tipo": f.tipo,
                "importo_totale": f.importo_totale,
                "fornitore_o_cliente": f.fornitore_o_cliente,
                "data_scadenza": f.data_scadenza.strftime("%Y-%m-%d") if f.data_scadenza else None,
                "stato": f.stato,
                "giorni_alla_scadenza": days_to,
                "alert": days_to < 0 and f.tipo == "attiva",
            })

        return json.dumps({"scadenze": items, "totale": len(items)})

    def _cash_flow_previsionale(self, **kwargs) -> str:
        mesi = kwargs.get("mesi", 3)
        now = datetime.now(timezone.utc)
        result = []

        for i in range(mesi):
            target = now + relativedelta(months=i)
            month_start = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + relativedelta(months=1))

            entrate_q = (
                self.db.query(Fattura)
                .filter(
                    Fattura.tipo == TipoFattura.ATTIVA.value,
                    Fattura.data_scadenza >= month_start,
                    Fattura.data_scadenza < month_end,
                    Fattura.stato != StatoFattura.PAGATA.value,
                )
                .all()
            )
            uscite_q = (
                self.db.query(Fattura)
                .filter(
                    Fattura.tipo == TipoFattura.PASSIVA.value,
                    Fattura.data_scadenza >= month_start,
                    Fattura.data_scadenza < month_end,
                    Fattura.stato != StatoFattura.PAGATA.value,
                )
                .all()
            )

            entrate = sum(f.importo_totale for f in entrate_q)
            uscite = sum(f.importo_totale for f in uscite_q)

            result.append({
                "mese": target.strftime("%Y-%m"),
                "entrate_previste": round(entrate, 2),
                "uscite_previste": round(uscite, 2),
                "saldo_previsto": round(entrate - uscite, 2),
            })

        return json.dumps({"cash_flow": result, "mesi_analizzati": mesi})

    def _report_mensile(self, **kwargs) -> str:
        now = datetime.now(timezone.utc)
        mese = kwargs.get("mese", now.month)
        anno = kwargs.get("anno", now.year)

        month_start = datetime(anno, mese, 1, tzinfo=timezone.utc)
        month_end = month_start + relativedelta(months=1)
        prev_start = month_start - relativedelta(months=1)

        def _stats(start, end):
            fatture = self.db.query(Fattura).filter(
                Fattura.data_emissione >= start,
                Fattura.data_emissione < end,
            ).all()
            entrate = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.ATTIVA.value)
            uscite = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.PASSIVA.value)
            pagate = sum(1 for f in fatture if f.stato == StatoFattura.PAGATA.value)
            scadute = sum(1 for f in fatture if f.stato == StatoFattura.SCADUTA.value)
            return entrate, uscite, len(fatture), pagate, scadute

        entrate, uscite, emesse, pagate, scadute = _stats(month_start, month_end)
        prev_entrate, prev_uscite, _, _, _ = _stats(prev_start, month_start)

        var_entrate = ((entrate - prev_entrate) / prev_entrate * 100) if prev_entrate > 0 else None
        var_uscite = ((uscite - prev_uscite) / prev_uscite * 100) if prev_uscite > 0 else None

        return json.dumps({
            "mese": f"{anno}-{mese:02d}",
            "entrate": round(entrate, 2),
            "uscite": round(uscite, 2),
            "saldo": round(entrate - uscite, 2),
            "fatture_emesse": emesse,
            "fatture_pagate": pagate,
            "fatture_scadute": scadute,
            "variazione_entrate": f"{var_entrate:+.1f}%" if var_entrate is not None else "N/A",
            "variazione_uscite": f"{var_uscite:+.1f}%" if var_uscite is not None else "N/A",
        })

    def _fatture_scadute(self) -> str:
        now = datetime.now(timezone.utc)
        scadute = (
            self.db.query(Fattura)
            .filter(
                Fattura.tipo == TipoFattura.ATTIVA.value,
                Fattura.stato != StatoFattura.PAGATA.value,
                Fattura.data_scadenza < now,
            )
            .order_by(Fattura.data_scadenza)
            .all()
        )

        if not scadute:
            return json.dumps({"message": "Nessuna fattura attiva scaduta. Ottimo!"})

        items = []
        alert_count = 0
        for f in scadute:
            days_overdue = (now - f.data_scadenza.replace(tzinfo=timezone.utc)).days
            is_alert = days_overdue > 30
            if is_alert:
                alert_count += 1
            items.append({
                "id": f.id,
                "numero": f.numero,
                "importo_totale": f.importo_totale,
                "fornitore_o_cliente": f.fornitore_o_cliente,
                "data_scadenza": f.data_scadenza.strftime("%Y-%m-%d"),
                "giorni_scaduta": days_overdue,
                "alert_30gg": is_alert,
            })

        return json.dumps({
            "fatture_scadute": items,
            "totale": len(items),
            "alert_oltre_30gg": alert_count,
            "valore_totale_scaduto": round(sum(f.importo_totale for f in scadute), 2),
        })
