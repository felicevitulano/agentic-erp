from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CollaboratoreCreate(BaseModel):
    nome: str
    cognome: str
    tipo: str = "consulente"
    email: Optional[str] = None
    telefono: Optional[str] = None
    tariffa_giornaliera: Optional[float] = None
    competenze: Optional[List[str]] = None
    data_inizio_contratto: Optional[str] = None
    data_fine_contratto: Optional[str] = None
    note: Optional[str] = None


class CollaboratoreUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    tipo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    tariffa_giornaliera: Optional[float] = None
    competenze: Optional[List[str]] = None
    data_fine_contratto: Optional[str] = None
    stato: Optional[str] = None
    note: Optional[str] = None


class CollaboratoreResponse(BaseModel):
    id: int
    nome: str
    cognome: str
    tipo: str
    email: Optional[str]
    telefono: Optional[str]
    tariffa_giornaliera: Optional[float]
    competenze: Optional[list]
    data_inizio_contratto: Optional[datetime]
    data_fine_contratto: Optional[datetime]
    stato: str
    note: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PresenzaCreate(BaseModel):
    collaboratore_id: int
    data: str
    ore: float = 8.0
    note: Optional[str] = None


class AssenzaCreate(BaseModel):
    collaboratore_id: int
    tipo: str = "ferie"
    data_inizio: str
    data_fine: str
    note: Optional[str] = None


class AssenzaResponse(BaseModel):
    id: int
    collaboratore_id: int
    tipo: str
    data_inizio: Optional[datetime]
    data_fine: Optional[datetime]
    stato: str
    note: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
