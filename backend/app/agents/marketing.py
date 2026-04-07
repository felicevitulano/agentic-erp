from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.base_agent import BaseAgent, ConfidenceScore
from app.models.marketing import Contenuto, ContattoEvento, TipoContenuto, StatoContenuto
from app.models.operations import Progetto, StatoProgetto
from app.models.sales import Opportunity


class MarketingAgent(BaseAgent):
    AGENT_ID = "marketing"
    AGENT_NAME = "Agente Marketing"
    DESCRIPTION = "Gestisce calendario editoriale, contenuti e contatti da eventi"

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
        return """Sei l'Agente Marketing di Agentic ERP per Think Next S.r.l.
Gestisci il calendario editoriale per LinkedIn e blog, tracciamento contenuti e contatti da eventi.

Rispondi sempre in italiano. Sii conciso e professionale.
Suggerisci contenuti basati sulle attivita' aziendali (progetti completati, deal chiusi, case study).
NON pubblichi direttamente sui canali (fuori scope).

Tipi contenuto: post_linkedin, articolo_blog, case_study.
Stati contenuto: bozza, in_revisione, pubblicato."""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "crea_contenuto",
                "description": "Crea un nuovo contenuto nel calendario editoriale",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "titolo": {"type": "string"},
                        "tipo": {"type": "string", "enum": ["post_linkedin", "articolo_blog", "case_study"]},
                        "autore": {"type": "string"},
                        "data_pubblicazione": {"type": "string", "description": "YYYY-MM-DD"},
                        "contenuto_testo": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["titolo", "tipo"],
                },
            },
            {
                "name": "aggiorna_contenuto",
                "description": "Aggiorna stato o dettagli di un contenuto",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "contenuto_id": {"type": "integer"},
                        "stato": {"type": "string", "enum": ["bozza", "in_revisione", "pubblicato"]},
                        "contenuto_testo": {"type": "string"},
                        "metriche": {"type": "object"},
                        "note": {"type": "string"},
                    },
                    "required": ["contenuto_id"],
                },
            },
            {
                "name": "calendario_editoriale",
                "description": "Mostra il calendario editoriale con filtri",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "stato": {"type": "string", "enum": ["bozza", "in_revisione", "pubblicato", "tutti"]},
                        "tipo": {"type": "string", "enum": ["post_linkedin", "articolo_blog", "case_study", "tutti"]},
                    },
                },
            },
            {
                "name": "registra_contatto_evento",
                "description": "Registra un contatto acquisito a un evento/webinar",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "email": {"type": "string"},
                        "azienda": {"type": "string"},
                        "evento": {"type": "string"},
                        "data_evento": {"type": "string", "description": "YYYY-MM-DD"},
                        "interesse": {"type": "string"},
                        "note": {"type": "string"},
                    },
                    "required": ["nome", "evento"],
                },
            },
            {
                "name": "suggerisci_contenuti",
                "description": "Suggerisce idee per contenuti basate sulle attivita' aziendali",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "report_marketing",
                "description": "Report mensile dei contenuti pubblicati",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mese": {"type": "integer"},
                        "anno": {"type": "integer"},
                    },
                },
            },
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        handlers = {
            "crea_contenuto": self._crea_contenuto,
            "aggiorna_contenuto": self._aggiorna_contenuto,
            "calendario_editoriale": self._calendario_editoriale,
            "registra_contatto_evento": self._registra_contatto_evento,
            "suggerisci_contenuti": self._suggerisci_contenuti,
            "report_marketing": self._report_marketing,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return f"Tool '{tool_name}' non riconosciuto."
        return handler(**tool_input)

    def _get_keywords(self) -> list[str]:
        return [
            "contenuto", "contenuti", "content",
            "linkedin", "blog", "post", "articolo",
            "case study", "calendario editoriale",
            "pubblicare", "pubblicazione", "bozza",
            "marketing", "evento", "webinar",
            "social", "editoriale",
        ]

    def _crea_contenuto(self, titolo: str, tipo: str, **kwargs) -> str:
        contenuto = Contenuto(
            titolo=titolo, tipo=tipo,
            autore=kwargs.get("autore"),
            contenuto_testo=kwargs.get("contenuto_testo"),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_pubblicazione"):
            contenuto.data_pubblicazione = datetime.strptime(kwargs["data_pubblicazione"], "%Y-%m-%d")

        self.db.add(contenuto)
        self.db.commit()
        self.db.refresh(contenuto)
        return json.dumps({
            "status": "ok",
            "message": f"Contenuto '{titolo}' creato come {tipo} (bozza)",
            "contenuto_id": contenuto.id,
        })

    def _aggiorna_contenuto(self, contenuto_id: int, **kwargs) -> str:
        c = self.db.query(Contenuto).filter(Contenuto.id == contenuto_id).first()
        if not c:
            return json.dumps({"status": "error", "message": f"Contenuto {contenuto_id} non trovato"})

        if kwargs.get("stato"):
            c.stato = kwargs["stato"]
            if kwargs["stato"] == StatoContenuto.PUBBLICATO.value and not c.data_pubblicazione:
                c.data_pubblicazione = datetime.now(timezone.utc)
        if kwargs.get("contenuto_testo"):
            c.contenuto_testo = kwargs["contenuto_testo"]
        if kwargs.get("metriche"):
            c.metriche = kwargs["metriche"]
        if kwargs.get("note"):
            c.note = kwargs["note"]

        self.db.commit()
        return json.dumps({
            "status": "ok",
            "message": f"Contenuto '{c.titolo}' aggiornato",
            "contenuto_id": c.id,
        })

    def _calendario_editoriale(self, **kwargs) -> str:
        stato = kwargs.get("stato", "tutti")
        tipo = kwargs.get("tipo", "tutti")

        query = self.db.query(Contenuto)
        if stato != "tutti":
            query = query.filter(Contenuto.stato == stato)
        if tipo != "tutti":
            query = query.filter(Contenuto.tipo == tipo)

        contenuti = query.order_by(Contenuto.data_pubblicazione.desc().nullslast()).all()

        if not contenuti:
            return json.dumps({"message": "Nessun contenuto nel calendario."})

        items = [{
            "id": c.id,
            "titolo": c.titolo,
            "tipo": c.tipo,
            "stato": c.stato,
            "autore": c.autore,
            "data_pubblicazione": c.data_pubblicazione.strftime("%Y-%m-%d") if c.data_pubblicazione else None,
        } for c in contenuti]

        return json.dumps({"contenuti": items, "totale": len(items)})

    def _registra_contatto_evento(self, nome: str, evento: str, **kwargs) -> str:
        ce = ContattoEvento(
            nome=nome, evento=evento,
            email=kwargs.get("email"),
            azienda=kwargs.get("azienda"),
            interesse=kwargs.get("interesse"),
            note=kwargs.get("note"),
        )
        if kwargs.get("data_evento"):
            ce.data_evento = datetime.strptime(kwargs["data_evento"], "%Y-%m-%d")

        self.db.add(ce)
        self.db.commit()
        self.db.refresh(ce)
        return json.dumps({
            "status": "ok",
            "message": f"Contatto '{nome}' registrato dall'evento '{evento}'",
            "contatto_evento_id": ce.id,
        })

    def _suggerisci_contenuti(self) -> str:
        suggerimenti = []

        # Check completed projects -> case study
        progetti_completati = self.db.query(Progetto).filter(
            Progetto.stato == StatoProgetto.COMPLETATO.value
        ).limit(5).all()
        for p in progetti_completati:
            suggerimenti.append({
                "tipo": "case_study",
                "suggerimento": f"Case Study: {p.nome}" + (f" per {p.cliente}" if p.cliente else ""),
                "motivo": "Progetto completato con successo",
            })

        # Check won deals -> success story
        deal_vinti = self.db.query(Opportunity).filter(
            Opportunity.stato == "vinto"
        ).limit(5).all()
        for d in deal_vinti:
            suggerimenti.append({
                "tipo": "post_linkedin",
                "suggerimento": f"Post LinkedIn: Nuova collaborazione - {d.titolo}",
                "motivo": "Deal chiuso con successo",
            })

        if not suggerimenti:
            suggerimenti.append({
                "tipo": "post_linkedin",
                "suggerimento": "Post LinkedIn: Presentazione servizi Think Next e approccio AI-first",
                "motivo": "Contenuto di brand awareness sempre utile",
            })

        return json.dumps({"suggerimenti": suggerimenti, "totale": len(suggerimenti)})

    def _report_marketing(self, **kwargs) -> str:
        now = datetime.now(timezone.utc)
        mese = kwargs.get("mese", now.month)
        anno = kwargs.get("anno", now.year)

        contenuti = self.db.query(Contenuto).all()
        # Filter in Python for SQLite compatibility
        del_mese = [c for c in contenuti
                    if c.data_pubblicazione and c.data_pubblicazione.month == mese and c.data_pubblicazione.year == anno]

        pubblicati = [c for c in del_mese if c.stato == StatoContenuto.PUBBLICATO.value]
        bozze = [c for c in del_mese if c.stato == StatoContenuto.BOZZA.value]

        contatti_evento = self.db.query(ContattoEvento).all()
        ce_mese = [ce for ce in contatti_evento
                   if ce.data_evento and ce.data_evento.month == mese and ce.data_evento.year == anno]

        return json.dumps({
            "mese": f"{anno}-{mese:02d}",
            "contenuti_pubblicati": len(pubblicati),
            "bozze_in_lavorazione": len(bozze),
            "per_tipo": {
                "post_linkedin": sum(1 for c in pubblicati if c.tipo == TipoContenuto.POST_LINKEDIN.value),
                "articolo_blog": sum(1 for c in pubblicati if c.tipo == TipoContenuto.ARTICOLO_BLOG.value),
                "case_study": sum(1 for c in pubblicati if c.tipo == TipoContenuto.CASE_STUDY.value),
            },
            "contatti_da_eventi": len(ce_mese),
        })
