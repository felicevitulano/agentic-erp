from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.base_agent import BaseAgent, ConfidenceScore
from app.models.sales import Contact, Opportunity, Contract, SAL, PipelineState, VALID_TRANSITIONS, LossReason


class SalesAgent(BaseAgent):
    AGENT_ID = "sales"
    AGENT_NAME = "Agente Vendite"
    DESCRIPTION = "Gestisce contatti, pipeline commerciale, contratti e SAL"

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
        return """Sei l'Agente Vendite di Agentic ERP per Think Next S.r.l.
Gestisci il ciclo commerciale completo: contatti, pipeline opportunita', contratti e stati di avanzamento lavori (SAL).

Rispondi sempre in italiano. Sii conciso e professionale.
Quando crei o aggiorni dati, conferma l'azione con un riepilogo chiaro.
Quando generi report, usa formattazione tabellare per chiarezza.

Pipeline: Lead -> Qualificato -> Proposta Inviata -> Negoziazione -> Chiuso Vinto / Chiuso Perso.
Quando un'opportunita' viene chiusa come "Perso", chiedi SEMPRE il motivo della perdita.
Quando un'opportunita' viene chiusa come "Vinto", crea automaticamente un contratto."""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "crea_contatto",
                "description": "Crea un nuovo contatto commerciale nel database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "description": "Nome del contatto"},
                        "cognome": {"type": "string", "description": "Cognome del contatto"},
                        "azienda": {"type": "string", "description": "Azienda del contatto"},
                        "email": {"type": "string", "description": "Email (opzionale)"},
                        "telefono": {"type": "string", "description": "Telefono (opzionale)"},
                        "ruolo": {"type": "string", "description": "Ruolo in azienda (opzionale)"},
                        "fonte": {"type": "string", "description": "Fonte del lead (opzionale)"},
                        "note": {"type": "string", "description": "Note aggiuntive (opzionale)"},
                    },
                    "required": ["nome", "cognome", "azienda"],
                },
            },
            {
                "name": "cerca_contatti",
                "description": "Cerca contatti per nome, azienda o email",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Testo di ricerca"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "crea_opportunita",
                "description": "Crea una nuova opportunita' commerciale collegata a un contatto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID del contatto"},
                        "titolo": {"type": "string", "description": "Titolo dell'opportunita'"},
                        "valore_stimato": {"type": "number", "description": "Valore stimato in EUR"},
                        "probabilita_chiusura": {"type": "integer", "description": "Probabilita' 0-100"},
                        "data_chiusura_prevista": {"type": "string", "description": "Data prevista YYYY-MM-DD"},
                        "note": {"type": "string", "description": "Note (opzionale)"},
                    },
                    "required": ["contact_id", "titolo", "valore_stimato"],
                },
            },
            {
                "name": "aggiorna_pipeline",
                "description": "Aggiorna lo stato di un'opportunita' nella pipeline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "opportunity_id": {"type": "integer", "description": "ID opportunita'"},
                        "nuovo_stato": {
                            "type": "string",
                            "enum": ["lead", "qualificato", "proposta", "negoziazione", "vinto", "perso"],
                            "description": "Nuovo stato pipeline",
                        },
                        "motivo_perdita": {
                            "type": "string",
                            "enum": ["competitor", "prezzo", "timing", "budget", "altro"],
                            "description": "Obbligatorio se stato=perso",
                        },
                        "note": {"type": "string", "description": "Note aggiuntive"},
                    },
                    "required": ["opportunity_id", "nuovo_stato"],
                },
            },
            {
                "name": "registra_sal",
                "description": "Registra un nuovo stato di avanzamento lavori per un contratto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contract_id": {"type": "integer", "description": "ID contratto"},
                        "percentuale_avanzamento": {"type": "number", "description": "Percentuale 0-100"},
                        "importo_maturato": {"type": "number", "description": "Importo maturato in EUR"},
                        "descrizione": {"type": "string", "description": "Descrizione milestone"},
                        "note": {"type": "string", "description": "Note (opzionale)"},
                    },
                    "required": ["contract_id", "percentuale_avanzamento", "importo_maturato"],
                },
            },
            {
                "name": "report_pipeline",
                "description": "Genera un report della pipeline con metriche",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "report_perdite",
                "description": "Analisi dei motivi di perdita delle opportunita'",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handlers = {
            "crea_contatto": self._crea_contatto,
            "cerca_contatti": self._cerca_contatti,
            "crea_opportunita": self._crea_opportunita,
            "aggiorna_pipeline": self._aggiorna_pipeline,
            "registra_sal": self._registra_sal,
            "report_pipeline": self._report_pipeline,
            "report_perdite": self._report_perdite,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' non riconosciuto."
        return handler(**tool_input)

    def _get_keywords(self) -> list[str]:
        return [
            "contatto", "contatti", "lead", "cliente", "prospect",
            "opportunita", "opportunità", "pipeline", "trattativa", "trattative",
            "vendita", "vendite", "commerciale", "deal",
            "contratto", "contratti", "sal", "avanzamento",
            "proposta", "offerta", "preventivo", "win rate",
            "chiuso", "vinto", "perso", "perdita",
        ]

    # --- Tool implementations ---

    def _crea_contatto(self, nome: str, cognome: str, azienda: str, **kwargs) -> str:
        contact = Contact(
            nome=nome, cognome=cognome, azienda=azienda,
            email=kwargs.get("email"),
            telefono=kwargs.get("telefono"),
            ruolo=kwargs.get("ruolo"),
            fonte=kwargs.get("fonte"),
            note=kwargs.get("note"),
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return json.dumps({
            "status": "ok",
            "message": f"Contatto creato: {nome} {cognome} ({azienda})",
            "contact_id": contact.id,
        })

    def _cerca_contatti(self, query: str) -> str:
        q = f"%{query}%"
        results = (
            self.db.query(Contact)
            .filter(
                (Contact.nome.ilike(q))
                | (Contact.cognome.ilike(q))
                | (Contact.azienda.ilike(q))
                | (Contact.email.ilike(q))
            )
            .limit(20)
            .all()
        )
        contacts = [
            {
                "id": c.id,
                "nome": f"{c.nome} {c.cognome}",
                "azienda": c.azienda,
                "email": c.email,
                "ruolo": c.ruolo,
            }
            for c in results
        ]
        return json.dumps({"results": contacts, "count": len(contacts)})

    def _crea_opportunita(self, contact_id: int, titolo: str, valore_stimato: float, **kwargs) -> str:
        contact = self.db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return json.dumps({"status": "error", "message": f"Contatto {contact_id} non trovato"})

        opp = Opportunity(
            contact_id=contact_id,
            titolo=titolo,
            valore_stimato=valore_stimato,
            probabilita_chiusura=kwargs.get("probabilita_chiusura", 10),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_chiusura_prevista"):
            opp.data_chiusura_prevista = datetime.strptime(
                kwargs["data_chiusura_prevista"], "%Y-%m-%d"
            )
        self.db.add(opp)
        self.db.commit()
        self.db.refresh(opp)
        return json.dumps({
            "status": "ok",
            "message": f"Opportunita' '{titolo}' creata per {contact.nome} {contact.cognome} - Valore: {valore_stimato:,.0f} EUR",
            "opportunity_id": opp.id,
        })

    def _aggiorna_pipeline(self, opportunity_id: int, nuovo_stato: str, **kwargs) -> str:
        opp = self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opp:
            return json.dumps({"status": "error", "message": f"Opportunita' {opportunity_id} non trovata"})

        current = PipelineState(opp.stato)
        new = PipelineState(nuovo_stato)

        if new not in VALID_TRANSITIONS.get(current, []):
            return json.dumps({
                "status": "error",
                "message": f"Transizione non valida: {current.value} -> {new.value}. "
                           f"Transizioni valide: {[t.value for t in VALID_TRANSITIONS[current]]}",
            })

        if new == PipelineState.PERSO:
            motivo = kwargs.get("motivo_perdita")
            if not motivo:
                return json.dumps({
                    "status": "error",
                    "message": "Il motivo della perdita e' obbligatorio quando lo stato e' 'perso'.",
                })
            opp.motivo_perdita = motivo

        opp.stato = nuovo_stato
        if kwargs.get("note"):
            opp.note = kwargs["note"]
        self.db.commit()

        result = {
            "status": "ok",
            "message": f"Opportunita' aggiornata: {current.value} -> {nuovo_stato}",
            "opportunity_id": opp.id,
        }

        # Auto-create contract on win
        if new == PipelineState.VINTO:
            contract = Contract(
                opportunity_id=opp.id,
                contact_id=opp.contact_id,
                titolo=opp.titolo,
                valore_totale=opp.valore_stimato,
                data_inizio=datetime.now(timezone.utc),
            )
            self.db.add(contract)
            self.db.commit()
            self.db.refresh(contract)
            result["contract_id"] = contract.id
            result["message"] += f". Contratto #{contract.id} creato automaticamente."

        return json.dumps(result)

    def _registra_sal(self, contract_id: int, percentuale_avanzamento: float, importo_maturato: float, **kwargs) -> str:
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return json.dumps({"status": "error", "message": f"Contratto {contract_id} non trovato"})

        last_sal = (
            self.db.query(SAL)
            .filter(SAL.contract_id == contract_id)
            .order_by(SAL.numero_sal.desc())
            .first()
        )
        numero = (last_sal.numero_sal + 1) if last_sal else 1

        sal = SAL(
            contract_id=contract_id,
            numero_sal=numero,
            percentuale_avanzamento=percentuale_avanzamento,
            importo_maturato=importo_maturato,
            descrizione=kwargs.get("descrizione"),
            note=kwargs.get("note"),
        )
        self.db.add(sal)
        self.db.commit()

        return json.dumps({
            "status": "ok",
            "message": f"SAL #{numero} registrato: {percentuale_avanzamento}% - {importo_maturato:,.0f} EUR",
            "sal_id": sal.id,
        })

    def _report_pipeline(self) -> str:
        opps = self.db.query(Opportunity).all()
        if not opps:
            return json.dumps({"message": "Nessuna opportunita' in pipeline."})

        by_state = {}
        total_won = 0
        total_lost = 0
        for o in opps:
            state = o.stato
            if state not in by_state:
                by_state[state] = {"count": 0, "value": 0.0}
            by_state[state]["count"] += 1
            by_state[state]["value"] += o.valore_stimato
            if state == "vinto":
                total_won += 1
            elif state == "perso":
                total_lost += 1

        closed = total_won + total_lost
        win_rate = (total_won / closed * 100) if closed > 0 else 0

        return json.dumps({
            "pipeline": by_state,
            "totale_opportunita": len(opps),
            "win_rate": f"{win_rate:.1f}%",
            "vinte": total_won,
            "perse": total_lost,
        })

    def _report_perdite(self) -> str:
        lost = self.db.query(Opportunity).filter(Opportunity.stato == "perso").all()
        if not lost:
            return json.dumps({"message": "Nessuna opportunita' persa registrata."})

        reasons = {}
        for o in lost:
            r = o.motivo_perdita or "non_specificato"
            if r not in reasons:
                reasons[r] = {"count": 0, "value": 0.0}
            reasons[r]["count"] += 1
            reasons[r]["value"] += o.valore_stimato

        total = len(lost)
        for r in reasons:
            reasons[r]["percentuale"] = f"{reasons[r]['count'] / total * 100:.1f}%"

        return json.dumps({
            "totale_perse": total,
            "motivi": reasons,
            "valore_totale_perso": sum(o.valore_stimato for o in lost),
        })
