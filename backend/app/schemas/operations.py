from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ProgettoCreate(BaseModel):
    nome: str
    cliente: Optional[str] = None
    data_inizio: Optional[str] = None
    data_fine_prevista: Optional[str] = None
    budget: Optional[float] = None
    contract_id: Optional[int] = None
    note: Optional[str] = None


class ProgettoUpdate(BaseModel):
    nome: Optional[str] = None
    stato: Optional[str] = None
    percentuale_avanzamento: Optional[float] = None
    data_fine_prevista: Optional[str] = None
    note: Optional[str] = None


class ProgettoResponse(BaseModel):
    id: int
    contract_id: Optional[int]
    nome: str
    cliente: Optional[str]
    data_inizio: Optional[datetime]
    data_fine_prevista: Optional[datetime]
    budget: Optional[float]
    stato: str
    percentuale_avanzamento: float
    note: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    progetto_id: int
    titolo: str
    descrizione: Optional[str] = None
    priorita: str = "media"
    collaboratore_id: Optional[int] = None
    data_scadenza: Optional[str] = None


class TaskUpdate(BaseModel):
    titolo: Optional[str] = None
    stato: Optional[str] = None
    priorita: Optional[str] = None
    collaboratore_id: Optional[int] = None
    data_scadenza: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    progetto_id: int
    collaboratore_id: Optional[int]
    titolo: str
    descrizione: Optional[str]
    priorita: str
    stato: str
    data_scadenza: Optional[datetime]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TimesheetCreate(BaseModel):
    collaboratore_id: int
    progetto_id: int
    data: str
    ore: float
    descrizione_attivita: Optional[str] = None


class TimesheetResponse(BaseModel):
    id: int
    collaboratore_id: int
    progetto_id: int
    data: Optional[datetime]
    ore: float
    descrizione_attivita: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
