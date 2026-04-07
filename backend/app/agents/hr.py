from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.base_agent import BaseAgent, ConfidenceScore
from app.models.hr import Collaboratore, Presenza, Assenza, TipoCollaboratore, StatoCollaboratore


class HRAgent(BaseAgent):
    AGENT_ID = "hr"
    AGENT_NAME = "Agente HR"
    DESCRIPTION = "Gestisce collaboratori, presenze, ferie e onboarding"

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
        return """Sei l'Agente HR di Agentic ERP per Think Next S.r.l.
Gestisci l'anagrafica collaboratori e consulenti, presenze, ferie e onboarding.

Rispondi sempre in italiano. Sii conciso e professionale.
Segnala proattivamente i contratti in scadenza nei prossimi 30 giorni.
NON gestisci l'assegnazione a progetti (dominio Operations).

Tipi collaboratore: dipendente, consulente.
Stati: attivo, inattivo.
Tipi assenza: ferie, permesso, malattia."""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "crea_collaboratore",
                "description": "Crea un nuovo collaboratore nel team",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "cognome": {"type": "string"},
                        "tipo": {"type": "string", "enum": ["dipendente", "consulente"]},
                        "email": {"type": "string"},
                        "telefono": {"type": "string"},
                        "tariffa_giornaliera": {"type": "number"},
                        "competenze": {"type": "array", "items": {"type": "string"}},
                        "data_inizio_contratto": {"type": "string", "description": "YYYY-MM-DD"},
                        "data_fine_contratto": {"type": "string", "description": "YYYY-MM-DD"},
                        "note": {"type": "string"},
                    },
                    "required": ["nome", "cognome", "tipo"],
                },
            },
            {
                "name": "cerca_collaboratori",
                "description": "Cerca collaboratori per nome o competenza",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            {
                "name": "registra_presenza",
                "description": "Registra la presenza giornaliera di un collaboratore",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "collaboratore_id": {"type": "integer"},
                        "data": {"type": "string", "description": "YYYY-MM-DD"},
                        "ore": {"type": "number", "default": 8},
                        "note": {"type": "string"},
                    },
                    "required": ["collaboratore_id", "data"],
                },
            },
            {
                "name": "gestisci_ferie",
                "description": "Crea o gestisci una richiesta di ferie/permesso",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "collaboratore_id": {"type": "integer"},
                        "tipo": {"type": "string", "enum": ["ferie", "permesso", "malattia"]},
                        "data_inizio": {"type": "string", "description": "YYYY-MM-DD"},
                        "data_fine": {"type": "string", "description": "YYYY-MM-DD"},
                        "note": {"type": "string"},
                    },
                    "required": ["collaboratore_id", "tipo", "data_inizio", "data_fine"],
                },
            },
            {
                "name": "contratti_in_scadenza",
                "description": "Mostra contratti di collaborazione in scadenza",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "giorni": {"type": "integer", "default": 30},
                    },
                },
            },
            {
                "name": "report_presenze",
                "description": "Report presenze per collaboratore e periodo",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "collaboratore_id": {"type": "integer"},
                        "mese": {"type": "integer"},
                        "anno": {"type": "integer"},
                    },
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handlers = {
            "crea_collaboratore": self._crea_collaboratore,
            "cerca_collaboratori": self._cerca_collaboratori,
            "registra_presenza": self._registra_presenza,
            "gestisci_ferie": self._gestisci_ferie,
            "contratti_in_scadenza": self._contratti_in_scadenza,
            "report_presenze": self._report_presenze,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' non riconosciuto."
        return handler(**tool_input)

    def _get_keywords(self) -> list[str]:
        return [
            "collaboratore", "collaboratori", "dipendente", "consulente",
            "presenza", "presenze", "assenza", "assenze",
            "ferie", "permesso", "malattia",
            "onboarding", "team", "risorse umane", "hr",
            "contratto collaborazione", "tariffa", "competenze",
        ]

    def _crea_collaboratore(self, nome: str, cognome: str, tipo: str, **kwargs) -> str:
        collab = Collaboratore(
            nome=nome, cognome=cognome, tipo=tipo,
            email=kwargs.get("email"),
            telefono=kwargs.get("telefono"),
            tariffa_giornaliera=kwargs.get("tariffa_giornaliera"),
            competenze=kwargs.get("competenze"),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_inizio_contratto"):
            collab.data_inizio_contratto = datetime.strptime(kwargs["data_inizio_contratto"], "%Y-%m-%d")
        if kwargs.get("data_fine_contratto"):
            collab.data_fine_contratto = datetime.strptime(kwargs["data_fine_contratto"], "%Y-%m-%d")

        self.db.add(collab)
        self.db.commit()
        self.db.refresh(collab)
        return json.dumps({
            "status": "ok",
            "message": f"Collaboratore creato: {nome} {cognome} ({tipo})",
            "collaboratore_id": collab.id,
        })

    def _cerca_collaboratori(self, query: str) -> str:
        q = f"%{query}%"
        results = (
            self.db.query(Collaboratore)
            .filter(
                (Collaboratore.nome.ilike(q))
                | (Collaboratore.cognome.ilike(q))
                | (Collaboratore.email.ilike(q))
            )
            .limit(20)
            .all()
        )
        items = [{
            "id": c.id,
            "nome": f"{c.nome} {c.cognome}",
            "tipo": c.tipo,
            "email": c.email,
            "stato": c.stato,
            "competenze": c.competenze,
        } for c in results]
        return json.dumps({"results": items, "count": len(items)})

    def _registra_presenza(self, collaboratore_id: int, data: str, **kwargs) -> str:
        collab = self.db.query(Collaboratore).filter(Collaboratore.id == collaboratore_id).first()
        if not collab:
            return json.dumps({"status": "error", "message": f"Collaboratore {collaboratore_id} non trovato"})

        presenza = Presenza(
            collaboratore_id=collaboratore_id,
            data=datetime.strptime(data, "%Y-%m-%d"),
            ore=kwargs.get("ore", 8.0),
            note=kwargs.get("note"),
        )
        self.db.add(presenza)
        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Presenza registrata per {collab.nome} {collab.cognome}: {data} - {kwargs.get('ore', 8.0)}h",
        })

    def _gestisci_ferie(self, collaboratore_id: int, tipo: str, data_inizio: str, data_fine: str, **kwargs) -> str:
        collab = self.db.query(Collaboratore).filter(Collaboratore.id == collaboratore_id).first()
        if not collab:
            return json.dumps({"status": "error", "message": f"Collaboratore {collaboratore_id} non trovato"})

        assenza = Assenza(
            collaboratore_id=collaboratore_id,
            tipo=tipo,
            data_inizio=datetime.strptime(data_inizio, "%Y-%m-%d"),
            data_fine=datetime.strptime(data_fine, "%Y-%m-%d"),
            note=kwargs.get("note"),
        )
        self.db.add(assenza)
        self.db.commit()
        self.db.refresh(assenza)
        return json.dumps({
            "status": "ok",
            "message": f"Richiesta {tipo} registrata per {collab.nome} {collab.cognome}: {data_inizio} -> {data_fine}",
            "assenza_id": assenza.id,
        })

    def _contratti_in_scadenza(self, **kwargs) -> str:
        giorni = kwargs.get("giorni", 30)
        now = datetime.now(timezone.utc)
        limit = now + timedelta(days=giorni)

        scadenti = (
            self.db.query(Collaboratore)
            .filter(
                Collaboratore.stato == StatoCollaboratore.ATTIVO.value,
                Collaboratore.data_fine_contratto != None,
                Collaboratore.data_fine_contratto <= limit,
            )
            .order_by(Collaboratore.data_fine_contratto)
            .all()
        )

        if not scadenti:
            return json.dumps({"message": f"Nessun contratto in scadenza nei prossimi {giorni} giorni."})

        items = [{
            "id": c.id,
            "nome": f"{c.nome} {c.cognome}",
            "tipo": c.tipo,
            "data_fine_contratto": c.data_fine_contratto.strftime("%Y-%m-%d") if c.data_fine_contratto else None,
            "giorni_rimanenti": (c.data_fine_contratto - now.replace(tzinfo=None)).days if c.data_fine_contratto else None,
        } for c in scadenti]

        return json.dumps({"contratti_in_scadenza": items, "totale": len(items)})

    def _report_presenze(self, **kwargs) -> str:
        now = datetime.now(timezone.utc)
        collab_id = kwargs.get("collaboratore_id")
        mese = kwargs.get("mese", now.month)
        anno = kwargs.get("anno", now.year)

        query = self.db.query(Presenza)
        if collab_id:
            query = query.filter(Presenza.collaboratore_id == collab_id)

        presenze = query.all()
        # Filter by month/year in Python (SQLite compatibility)
        filtered = [p for p in presenze if p.data and p.data.month == mese and p.data.year == anno]

        totale_ore = sum(p.ore for p in filtered)
        totale_giorni = len(filtered)

        return json.dumps({
            "mese": f"{anno}-{mese:02d}",
            "totale_giorni": totale_giorni,
            "totale_ore": totale_ore,
            "presenze": totale_giorni,
        })
