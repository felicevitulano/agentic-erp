from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.hr import Collaboratore, Presenza, Assenza, StatoCollaboratore
from app.schemas.hr import (
    CollaboratoreCreate, CollaboratoreUpdate, CollaboratoreResponse,
    PresenzaCreate, AssenzaCreate, AssenzaResponse,
)
from app.auth.jwt import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["hr"])


# --- Collaboratori ---

@router.get("/collaboratori", response_model=List[CollaboratoreResponse])
def list_collaboratori(
    stato: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Collaboratore)
    if stato:
        query = query.filter(Collaboratore.stato == stato)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Collaboratore.nome.ilike(like))
            | (Collaboratore.cognome.ilike(like))
            | (Collaboratore.email.ilike(like))
        )
    return query.order_by(Collaboratore.cognome).all()


@router.get("/collaboratori/{cid}", response_model=CollaboratoreResponse)
def get_collaboratore(cid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Collaboratore).filter(Collaboratore.id == cid).first()
    if not c:
        raise HTTPException(404, "Collaboratore non trovato")
    return c


@router.post("/collaboratori", response_model=CollaboratoreResponse, status_code=201)
def create_collaboratore(data: CollaboratoreCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = Collaboratore(
        nome=data.nome, cognome=data.cognome, tipo=data.tipo,
        email=data.email, telefono=data.telefono,
        tariffa_giornaliera=data.tariffa_giornaliera,
        competenze=data.competenze, note=data.note,
    )
    if data.data_inizio_contratto:
        c.data_inizio_contratto = datetime.strptime(data.data_inizio_contratto, "%Y-%m-%d")
    if data.data_fine_contratto:
        c.data_fine_contratto = datetime.strptime(data.data_fine_contratto, "%Y-%m-%d")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/collaboratori/{cid}", response_model=CollaboratoreResponse)
def update_collaboratore(cid: int, data: CollaboratoreUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = db.query(Collaboratore).filter(Collaboratore.id == cid).first()
    if not c:
        raise HTTPException(404, "Collaboratore non trovato")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "data_fine_contratto" and value:
            setattr(c, field, datetime.strptime(value, "%Y-%m-%d"))
        else:
            setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return c


# --- Presenze ---

@router.post("/presenze", status_code=201)
def create_presenza(data: PresenzaCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = Presenza(
        collaboratore_id=data.collaboratore_id,
        data=datetime.strptime(data.data, "%Y-%m-%d"),
        ore=data.ore, note=data.note,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "status": "ok"}


@router.get("/presenze")
def list_presenze(
    collaboratore_id: Optional[int] = None,
    mese: Optional[int] = None,
    anno: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Presenza)
    if collaboratore_id:
        query = query.filter(Presenza.collaboratore_id == collaboratore_id)
    presenze = query.order_by(Presenza.data.desc()).all()

    if mese and anno:
        presenze = [p for p in presenze if p.data and p.data.month == mese and p.data.year == anno]

    return [{
        "id": p.id,
        "collaboratore_id": p.collaboratore_id,
        "data": p.data.isoformat() if p.data else None,
        "ore": p.ore,
        "note": p.note,
    } for p in presenze]


# --- Assenze ---

@router.post("/assenze", response_model=AssenzaResponse, status_code=201)
def create_assenza(data: AssenzaCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = Assenza(
        collaboratore_id=data.collaboratore_id,
        tipo=data.tipo,
        data_inizio=datetime.strptime(data.data_inizio, "%Y-%m-%d"),
        data_fine=datetime.strptime(data.data_fine, "%Y-%m-%d"),
        note=data.note,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("/assenze")
def list_assenze(
    collaboratore_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Assenza)
    if collaboratore_id:
        query = query.filter(Assenza.collaboratore_id == collaboratore_id)
    return query.order_by(Assenza.data_inizio.desc()).all()


@router.put("/assenze/{aid}/approva")
def approva_assenza(aid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.query(Assenza).filter(Assenza.id == aid).first()
    if not a:
        raise HTTPException(404, "Assenza non trovata")
    a.stato = "approvata"
    db.commit()
    return {"status": "ok", "message": "Assenza approvata"}


# --- Contratti in scadenza ---

@router.get("/collaboratori-scadenza")
def contratti_in_scadenza(
    giorni: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    limit = now + timedelta(days=giorni)
    scadenti = (
        db.query(Collaboratore)
        .filter(
            Collaboratore.stato == StatoCollaboratore.ATTIVO.value,
            Collaboratore.data_fine_contratto != None,
            Collaboratore.data_fine_contratto <= limit,
        )
        .order_by(Collaboratore.data_fine_contratto)
        .all()
    )
    return [{
        "id": c.id,
        "nome": f"{c.nome} {c.cognome}",
        "tipo": c.tipo,
        "data_fine_contratto": c.data_fine_contratto.isoformat() if c.data_fine_contratto else None,
    } for c in scadenti]
