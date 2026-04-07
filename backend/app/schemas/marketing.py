from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ContenutoCreate(BaseModel):
    titolo: str
    tipo: str = "post_linkedin"
    autore: Optional[str] = None
    data_pubblicazione: Optional[str] = None
    contenuto_testo: Optional[str] = None
    note: Optional[str] = None


class ContenutoUpdate(BaseModel):
    titolo: Optional[str] = None
    tipo: Optional[str] = None
    stato: Optional[str] = None
    data_pubblicazione: Optional[str] = None
    autore: Optional[str] = None
    contenuto_testo: Optional[str] = None
    metriche: Optional[dict] = None
    note: Optional[str] = None


class ContenutoResponse(BaseModel):
    id: int
    titolo: str
    tipo: str
    stato: str
    data_pubblicazione: Optional[datetime]
    autore: Optional[str]
    contenuto_testo: Optional[str]
    metriche: Optional[dict]
    note: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ContattoEventoCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    azienda: Optional[str] = None
    evento: str
    data_evento: Optional[str] = None
    interesse: Optional[str] = None
    note: Optional[str] = None


class ContattoEventoResponse(BaseModel):
    id: int
    nome: str
    email: Optional[str]
    azienda: Optional[str]
    evento: str
    data_evento: Optional[datetime]
    interesse: Optional[str]
    note: Optional[str]
    convertito_a_contatto_id: Optional[int]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
