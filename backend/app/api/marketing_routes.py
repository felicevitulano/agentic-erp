from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.marketing import Contenuto, ContattoEvento
from app.schemas.marketing import (
    ContenutoCreate, ContenutoUpdate, ContenutoResponse,
    ContattoEventoCreate, ContattoEventoResponse,
)
from app.auth.jwt import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["marketing"])


# --- Contenuti ---

@router.get("/contenuti", response_model=List[ContenutoResponse])
def list_contenuti(
    tipo: Optional[str] = None,
    stato: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Contenuto)
    if tipo:
        query = query.filter(Contenuto.tipo == tipo)
    if stato:
        query = query.filter(Contenuto.stato == stato)
    return query.order_by(Contenuto.data_pubblicazione.desc().nullslast()).all()


@router.post("/contenuti", response_model=ContenutoResponse, status_code=201)
def create_contenuto(data: ContenutoCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = Contenuto(
        titolo=data.titolo, tipo=data.tipo,
        autore=data.autore, contenuto_testo=data.contenuto_testo, note=data.note,
    )
    if data.data_pubblicazione:
        c.data_pubblicazione = datetime.strptime(data.data_pubblicazione, "%Y-%m-%d")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/contenuti/{cid}", response_model=ContenutoResponse)
def update_contenuto(cid: int, data: ContenutoUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Contenuto).filter(Contenuto.id == cid).first()
    if not c:
        raise HTTPException(404, "Contenuto non trovato")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "data_pubblicazione" and value:
            setattr(c, field, datetime.strptime(value, "%Y-%m-%d"))
        else:
            setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return c


# --- Contatti Evento ---

@router.get("/contatti-evento", response_model=List[ContattoEventoResponse])
def list_contatti_evento(
    evento: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(ContattoEvento)
    if evento:
        query = query.filter(ContattoEvento.evento.ilike(f"%{evento}%"))
    return query.order_by(ContattoEvento.created_at.desc()).all()


@router.post("/contatti-evento", response_model=ContattoEventoResponse, status_code=201)
def create_contatto_evento(data: ContattoEventoCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ce = ContattoEvento(
        nome=data.nome, email=data.email, azienda=data.azienda,
        evento=data.evento, interesse=data.interesse, note=data.note,
    )
    if data.data_evento:
        ce.data_evento = datetime.strptime(data.data_evento, "%Y-%m-%d")
    db.add(ce)
    db.commit()
    db.refresh(ce)
    return ce
