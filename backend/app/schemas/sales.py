from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# --- Contact ---
class ContactCreate(BaseModel):
    nome: str
    cognome: str
    azienda: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    ruolo: Optional[str] = None
    fonte: Optional[str] = None
    note: Optional[str] = None


class ContactUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    azienda: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    ruolo: Optional[str] = None
    fonte: Optional[str] = None
    note: Optional[str] = None


class ContactResponse(BaseModel):
    id: int
    nome: str
    cognome: str
    azienda: str
    email: Optional[str]
    telefono: Optional[str]
    ruolo: Optional[str]
    fonte: Optional[str]
    note: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- Opportunity ---
class OpportunityCreate(BaseModel):
    contact_id: int
    titolo: str
    valore_stimato: float
    probabilita_chiusura: int = 10
    data_chiusura_prevista: Optional[str] = None
    note: Optional[str] = None


class OpportunityUpdate(BaseModel):
    titolo: Optional[str] = None
    valore_stimato: Optional[float] = None
    stato: Optional[str] = None
    probabilita_chiusura: Optional[int] = None
    data_chiusura_prevista: Optional[str] = None
    motivo_perdita: Optional[str] = None
    note: Optional[str] = None


class OpportunityResponse(BaseModel):
    id: int
    contact_id: int
    titolo: str
    valore_stimato: float
    stato: str
    probabilita_chiusura: int
    data_chiusura_prevista: Optional[datetime]
    motivo_perdita: Optional[str]
    note: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    contact: Optional[ContactResponse] = None

    model_config = {"from_attributes": True}


# --- Contract ---
class ContractResponse(BaseModel):
    id: int
    opportunity_id: int
    contact_id: int
    titolo: str
    valore_totale: float
    data_inizio: Optional[datetime]
    data_fine: Optional[datetime]
    stato: str
    note: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


# --- SAL ---
class SALCreate(BaseModel):
    contract_id: int
    percentuale_avanzamento: float
    importo_maturato: float
    descrizione: Optional[str] = None
    note: Optional[str] = None


class SALResponse(BaseModel):
    id: int
    contract_id: int
    numero_sal: int
    descrizione: Optional[str]
    percentuale_avanzamento: float
    importo_maturato: float
    data_sal: Optional[datetime]
    note: Optional[str]

    model_config = {"from_attributes": True}


# --- Pipeline Stats ---
class PipelineStats(BaseModel):
    totale_opportunita: int
    valore_totale: float
    per_stato: dict
    win_rate: float
    vinte: int
    perse: int
