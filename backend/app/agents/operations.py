from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.base_agent import BaseAgent, ConfidenceScore
from app.models.operations import Progetto, Task, Timesheet, StatoProgetto, StatoTask, PrioritaTask


class OperationsAgent(BaseAgent):
    AGENT_ID = "operations"
    AGENT_NAME = "Agente Operations"
    DESCRIPTION = "Gestisce progetti, task, timesheet e monitoraggio delivery"

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
        return """Sei l'Agente Operations di Agentic ERP per Think Next S.r.l.
Gestisci progetti, task, milestone, timesheet e monitoraggio delivery.

Rispondi sempre in italiano. Sii conciso e professionale.
Segnala proattivamente progetti in ritardo e task scaduti.
Usa indicatori semaforo (verde/giallo/rosso) per lo stato dei progetti.
NON gestisci i dati contrattuali dei collaboratori (dominio HR).

Stati progetto: pianificato, attivo, completato, sospeso.
Priorita' task: alta, media, bassa.
Stati task: da_fare, in_corso, completato, bloccato."""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "crea_progetto",
                "description": "Crea un nuovo progetto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "cliente": {"type": "string"},
                        "data_inizio": {"type": "string", "description": "YYYY-MM-DD"},
                        "data_fine_prevista": {"type": "string", "description": "YYYY-MM-DD"},
                        "budget": {"type": "number"},
                        "contract_id": {"type": "integer"},
                        "note": {"type": "string"},
                    },
                    "required": ["nome"],
                },
            },
            {
                "name": "aggiorna_progetto",
                "description": "Aggiorna stato o avanzamento di un progetto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "progetto_id": {"type": "integer"},
                        "stato": {"type": "string", "enum": ["pianificato", "attivo", "completato", "sospeso"]},
                        "percentuale_avanzamento": {"type": "number"},
                        "note": {"type": "string"},
                    },
                    "required": ["progetto_id"],
                },
            },
            {
                "name": "crea_task",
                "description": "Crea un nuovo task per un progetto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "progetto_id": {"type": "integer"},
                        "titolo": {"type": "string"},
                        "descrizione": {"type": "string"},
                        "priorita": {"type": "string", "enum": ["alta", "media", "bassa"]},
                        "collaboratore_id": {"type": "integer"},
                        "data_scadenza": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                    "required": ["progetto_id", "titolo"],
                },
            },
            {
                "name": "aggiorna_task",
                "description": "Aggiorna lo stato di un task",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer"},
                        "stato": {"type": "string", "enum": ["da_fare", "in_corso", "completato", "bloccato"]},
                        "collaboratore_id": {"type": "integer"},
                        "note": {"type": "string"},
                    },
                    "required": ["task_id"],
                },
            },
            {
                "name": "registra_timesheet",
                "description": "Registra ore lavorate su un progetto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "collaboratore_id": {"type": "integer"},
                        "progetto_id": {"type": "integer"},
                        "data": {"type": "string", "description": "YYYY-MM-DD"},
                        "ore": {"type": "number"},
                        "descrizione_attivita": {"type": "string"},
                    },
                    "required": ["collaboratore_id", "progetto_id", "data", "ore"],
                },
            },
            {
                "name": "stato_progetti",
                "description": "Panoramica di tutti i progetti con indicatori semaforo",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "alert_ritardi",
                "description": "Mostra progetti e task in ritardo",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handlers = {
            "crea_progetto": self._crea_progetto,
            "aggiorna_progetto": self._aggiorna_progetto,
            "crea_task": self._crea_task,
            "aggiorna_task": self._aggiorna_task,
            "registra_timesheet": self._registra_timesheet,
            "stato_progetti": self._stato_progetti,
            "alert_ritardi": self._alert_ritardi,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' non riconosciuto."
        return handler(**tool_input)

    def _get_keywords(self) -> list[str]:
        return [
            "progetto", "progetti", "project",
            "task", "attivita", "attività", "compito",
            "timesheet", "ore", "ore lavorate",
            "milestone", "delivery", "scadenza progetto",
            "ritardo", "bloccato", "in corso",
            "assegnare", "assegnazione", "allocazione",
            "budget progetto", "avanzamento",
        ]

    def _crea_progetto(self, nome: str, **kwargs) -> str:
        progetto = Progetto(
            nome=nome,
            cliente=kwargs.get("cliente"),
            budget=kwargs.get("budget"),
            contract_id=kwargs.get("contract_id"),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_inizio"):
            progetto.data_inizio = datetime.strptime(kwargs["data_inizio"], "%Y-%m-%d")
        if kwargs.get("data_fine_prevista"):
            progetto.data_fine_prevista = datetime.strptime(kwargs["data_fine_prevista"], "%Y-%m-%d")

        self.db.add(progetto)
        self.db.commit()
        self.db.refresh(progetto)
        return json.dumps({
            "status": "ok",
            "message": f"Progetto '{nome}' creato" + (f" - Budget: {kwargs.get('budget'):,.0f} EUR" if kwargs.get('budget') else ""),
            "progetto_id": progetto.id,
        })

    def _aggiorna_progetto(self, progetto_id: int, **kwargs) -> str:
        progetto = self.db.query(Progetto).filter(Progetto.id == progetto_id).first()
        if not progetto:
            return json.dumps({"status": "error", "message": f"Progetto {progetto_id} non trovato"})

        if kwargs.get("stato"):
            progetto.stato = kwargs["stato"]
        if kwargs.get("percentuale_avanzamento") is not None:
            progetto.percentuale_avanzamento = kwargs["percentuale_avanzamento"]
        if kwargs.get("note"):
            progetto.note = kwargs["note"]

        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Progetto '{progetto.nome}' aggiornato",
            "progetto_id": progetto.id,
        })

    def _crea_task(self, progetto_id: int, titolo: str, **kwargs) -> str:
        progetto = self.db.query(Progetto).filter(Progetto.id == progetto_id).first()
        if not progetto:
            return json.dumps({"status": "error", "message": f"Progetto {progetto_id} non trovato"})

        task = Task(
            progetto_id=progetto_id,
            titolo=titolo,
            descrizione=kwargs.get("descrizione"),
            priorita=kwargs.get("priorita", PrioritaTask.MEDIA.value),
            collaboratore_id=kwargs.get("collaboratore_id"),
        )
        if kwargs.get("data_scadenza"):
            task.data_scadenza = datetime.strptime(kwargs["data_scadenza"], "%Y-%m-%d")

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return json.dumps({
            "status": "ok",
            "message": f"Task '{titolo}' creato nel progetto '{progetto.nome}'",
            "task_id": task.id,
        })

    def _aggiorna_task(self, task_id: int, **kwargs) -> str:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return json.dumps({"status": "error", "message": f"Task {task_id} non trovato"})

        if kwargs.get("stato"):
            task.stato = kwargs["stato"]
            if kwargs["stato"] == StatoTask.COMPLETATO.value:
                task.completed_at = datetime.now(timezone.utc)
        if kwargs.get("collaboratore_id"):
            task.collaboratore_id = kwargs["collaboratore_id"]

        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Task '{task.titolo}' aggiornato",
            "task_id": task.id,
        })

    def _registra_timesheet(self, collaboratore_id: int, progetto_id: int, data: str, ore: float, **kwargs) -> str:
        progetto = self.db.query(Progetto).filter(Progetto.id == progetto_id).first()
        if not progetto:
            return json.dumps({"status": "error", "message": f"Progetto {progetto_id} non trovato"})

        entry = Timesheet(
            collaboratore_id=collaboratore_id,
            progetto_id=progetto_id,
            data=datetime.strptime(data, "%Y-%m-%d"),
            ore=ore,
            descrizione_attivita=kwargs.get("descrizione_attivita"),
        )
        self.db.add(entry)
        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Timesheet registrato: {ore}h su '{progetto.nome}' il {data}",
        })

    def _stato_progetti(self) -> str:
        progetti = self.db.query(Progetto).filter(
            Progetto.stato.in_([StatoProgetto.ATTIVO.value, StatoProgetto.PIANIFICATO.value])
        ).all()

        if not progetti:
            return json.dumps({"message": "Nessun progetto attivo."})

        now = datetime.now(timezone.utc)
        items = []
        for p in progetti:
            # Semaforo: verde (on track), giallo (attenzione), rosso (ritardo)
            semaforo = "verde"
            if p.data_fine_prevista:
                dfp = p.data_fine_prevista.replace(tzinfo=timezone.utc) if p.data_fine_prevista.tzinfo is None else p.data_fine_prevista
                days_left = (dfp - now).days
                if days_left < 0:
                    semaforo = "rosso"
                elif days_left < 14 and p.percentuale_avanzamento < 80:
                    semaforo = "giallo"

            # Budget check
            total_hours = sum(t.ore for t in p.timesheet_entries)
            costo_stimato = total_hours * 400  # tariffa media

            items.append({
                "id": p.id,
                "nome": p.nome,
                "cliente": p.cliente,
                "stato": p.stato,
                "avanzamento": p.percentuale_avanzamento,
                "semaforo": semaforo,
                "budget": p.budget,
                "costo_attuale": costo_stimato,
                "ore_registrate": total_hours,
                "task_totali": len(p.tasks),
                "task_completati": sum(1 for t in p.tasks if t.stato == StatoTask.COMPLETATO.value),
            })

        return json.dumps({"progetti": items, "totale": len(items)})

    def _alert_ritardi(self) -> str:
        now = datetime.now(timezone.utc)

        # Progetti in ritardo
        progetti_ritardo = self.db.query(Progetto).filter(
            Progetto.stato == StatoProgetto.ATTIVO.value,
            Progetto.data_fine_prevista != None,
            Progetto.data_fine_prevista < now,
        ).all()

        # Task scaduti
        task_scaduti = self.db.query(Task).filter(
            Task.stato.in_([StatoTask.DA_FARE.value, StatoTask.IN_CORSO.value]),
            Task.data_scadenza != None,
            Task.data_scadenza < now,
        ).all()

        if not progetti_ritardo and not task_scaduti:
            return json.dumps({"message": "Nessun ritardo rilevato. Tutto nei tempi!"})

        return json.dumps({
            "progetti_in_ritardo": [{
                "id": p.id,
                "nome": p.nome,
                "data_fine_prevista": p.data_fine_prevista.strftime("%Y-%m-%d") if p.data_fine_prevista else None,
                "giorni_ritardo": (now - p.data_fine_prevista.replace(tzinfo=timezone.utc)).days if p.data_fine_prevista else 0,
                "avanzamento": p.percentuale_avanzamento,
            } for p in progetti_ritardo],
            "task_scaduti": [{
                "id": t.id,
                "titolo": t.titolo,
                "stato": t.stato,
                "data_scadenza": t.data_scadenza.strftime("%Y-%m-%d") if t.data_scadenza else None,
                "giorni_ritardo": (now - t.data_scadenza.replace(tzinfo=timezone.utc)).days if t.data_scadenza else 0,
            } for t in task_scaduti],
            "totale_progetti_ritardo": len(progetti_ritardo),
            "totale_task_scaduti": len(task_scaduti),
        })
