from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.operations import Progetto, Task, Timesheet, StatoProgetto, StatoTask
from app.schemas.operations import (
    ProgettoCreate, ProgettoUpdate, ProgettoResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    TimesheetCreate, TimesheetResponse,
)
from app.auth.jwt import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["operations"])


# --- Progetti ---

@router.get("/progetti", response_model=List[ProgettoResponse])
def list_progetti(
    stato: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Progetto)
    if stato:
        query = query.filter(Progetto.stato == stato)
    return query.order_by(Progetto.created_at.desc()).all()


@router.get("/progetti/{pid}", response_model=ProgettoResponse)
def get_progetto(pid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Progetto).filter(Progetto.id == pid).first()
    if not p:
        raise HTTPException(404, "Progetto non trovato")
    return p


@router.post("/progetti", response_model=ProgettoResponse, status_code=201)
def create_progetto(data: ProgettoCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = Progetto(
        nome=data.nome, cliente=data.cliente,
        budget=data.budget, contract_id=data.contract_id, note=data.note,
    )
    if data.data_inizio:
        p.data_inizio = datetime.strptime(data.data_inizio, "%Y-%m-%d")
    if data.data_fine_prevista:
        p.data_fine_prevista = datetime.strptime(data.data_fine_prevista, "%Y-%m-%d")
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/progetti/{pid}", response_model=ProgettoResponse)
def update_progetto(pid: int, data: ProgettoUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Progetto).filter(Progetto.id == pid).first()
    if not p:
        raise HTTPException(404, "Progetto non trovato")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "data_fine_prevista" and value:
            setattr(p, field, datetime.strptime(value, "%Y-%m-%d"))
        else:
            setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


# --- Progetti overview con semaforo ---

@router.get("/progetti-overview")
def progetti_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    progetti = db.query(Progetto).filter(
        Progetto.stato.in_([StatoProgetto.ATTIVO.value, StatoProgetto.PIANIFICATO.value])
    ).all()

    now = datetime.now(timezone.utc)
    items = []
    for p in progetti:
        semaforo = "verde"
        if p.data_fine_prevista:
            dfp = p.data_fine_prevista.replace(tzinfo=timezone.utc) if p.data_fine_prevista.tzinfo is None else p.data_fine_prevista
            days_left = (dfp - now).days
            if days_left < 0:
                semaforo = "rosso"
            elif days_left < 14 and p.percentuale_avanzamento < 80:
                semaforo = "giallo"

        total_hours = sum(t.ore for t in p.timesheet_entries)
        items.append({
            "id": p.id,
            "nome": p.nome,
            "cliente": p.cliente,
            "stato": p.stato,
            "avanzamento": p.percentuale_avanzamento,
            "semaforo": semaforo,
            "budget": p.budget,
            "ore_registrate": total_hours,
            "task_totali": len(p.tasks),
            "task_completati": sum(1 for t in p.tasks if t.stato == StatoTask.COMPLETATO.value),
            "data_fine_prevista": p.data_fine_prevista.isoformat() if p.data_fine_prevista else None,
        })

    return {"progetti": items, "totale": len(items)}


# --- Tasks ---

@router.get("/tasks", response_model=List[TaskResponse])
def list_tasks(
    progetto_id: Optional[int] = None,
    stato: Optional[str] = None,
    collaboratore_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Task)
    if progetto_id:
        query = query.filter(Task.progetto_id == progetto_id)
    if stato:
        query = query.filter(Task.stato == stato)
    if collaboratore_id:
        query = query.filter(Task.collaboratore_id == collaboratore_id)
    return query.order_by(Task.created_at.desc()).all()


@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Progetto).filter(Progetto.id == data.progetto_id).first()
    if not p:
        raise HTTPException(404, "Progetto non trovato")
    t = Task(
        progetto_id=data.progetto_id, titolo=data.titolo,
        descrizione=data.descrizione, priorita=data.priorita,
        collaboratore_id=data.collaboratore_id,
    )
    if data.data_scadenza:
        t.data_scadenza = datetime.strptime(data.data_scadenza, "%Y-%m-%d")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/tasks/{tid}", response_model=TaskResponse)
def update_task(tid: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(Task).filter(Task.id == tid).first()
    if not t:
        raise HTTPException(404, "Task non trovato")
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "data_scadenza" and value:
            setattr(t, field, datetime.strptime(value, "%Y-%m-%d"))
        elif field == "stato" and value == StatoTask.COMPLETATO.value:
            t.stato = value
            t.completed_at = datetime.now(timezone.utc)
        else:
            setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return t


# --- Timesheet ---

@router.get("/timesheet", response_model=List[TimesheetResponse])
def list_timesheet(
    progetto_id: Optional[int] = None,
    collaboratore_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Timesheet)
    if progetto_id:
        query = query.filter(Timesheet.progetto_id == progetto_id)
    if collaboratore_id:
        query = query.filter(Timesheet.collaboratore_id == collaboratore_id)
    return query.order_by(Timesheet.data.desc()).all()


@router.post("/timesheet", response_model=TimesheetResponse, status_code=201)
def create_timesheet(data: TimesheetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.query(Progetto).filter(Progetto.id == data.progetto_id).first()
    if not p:
        raise HTTPException(404, "Progetto non trovato")
    t = Timesheet(
        collaboratore_id=data.collaboratore_id,
        progetto_id=data.progetto_id,
        data=datetime.strptime(data.data, "%Y-%m-%d"),
        ore=data.ore,
        descrizione_attivita=data.descrizione_attivita,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
