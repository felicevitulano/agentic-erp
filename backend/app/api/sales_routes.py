from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.models import User, get_db
from app.models.sales import Contact, Opportunity, Contract, SAL, PipelineState, VALID_TRANSITIONS
from app.schemas.sales import (
    ContactCreate, ContactUpdate, ContactResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    ContractResponse, SALCreate, SALResponse, PipelineStats,
)
from app.auth.jwt import get_current_user
from app.utils.audit import log_action

router = APIRouter(prefix="/api", tags=["sales"])


# ============ CONTACTS ============

@router.get("/contacts", response_model=List[ContactResponse])
def list_contacts(
    q: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Contact)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Contact.nome.ilike(like))
            | (Contact.cognome.ilike(like))
            | (Contact.azienda.ilike(like))
            | (Contact.email.ilike(like))
        )
    return query.order_by(Contact.updated_at.desc()).offset(offset).limit(limit).all()


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    return contact


@router.post("/contacts", response_model=ContactResponse, status_code=201)
def create_contact(
    data: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = Contact(**data.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    log_action(db, agent="api", action="create_contact", user_id=current_user.id,
               entity_type="contact", entity_id=contact.id)
    return contact


@router.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    log_action(db, agent="api", action="update_contact", user_id=current_user.id,
               entity_type="contact", entity_id=contact.id)
    return contact


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    db.delete(contact)
    db.commit()
    log_action(db, agent="api", action="delete_contact", user_id=current_user.id,
               entity_type="contact", entity_id=contact_id)
    return {"ok": True}


# ============ OPPORTUNITIES ============

@router.get("/opportunities", response_model=List[OpportunityResponse])
def list_opportunities(
    stato: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).options(joinedload(Opportunity.contact))
    if stato:
        query = query.filter(Opportunity.stato == stato)
    return query.order_by(Opportunity.updated_at.desc()).all()


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
def get_opportunity(
    opp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = db.query(Opportunity).options(joinedload(Opportunity.contact)).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunita non trovata")
    return opp


@router.post("/opportunities", response_model=OpportunityResponse, status_code=201)
def create_opportunity(
    data: OpportunityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contact = db.query(Contact).filter(Contact.id == data.contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contatto non trovato")

    opp = Opportunity(
        contact_id=data.contact_id,
        titolo=data.titolo,
        valore_stimato=data.valore_stimato,
        probabilita_chiusura=data.probabilita_chiusura,
        note=data.note,
    )
    if data.data_chiusura_prevista:
        opp.data_chiusura_prevista = datetime.strptime(data.data_chiusura_prevista, "%Y-%m-%d")
    db.add(opp)
    db.commit()
    db.refresh(opp)
    log_action(db, agent="api", action="create_opportunity", user_id=current_user.id,
               entity_type="opportunity", entity_id=opp.id)
    return opp


@router.put("/opportunities/{opp_id}", response_model=OpportunityResponse)
def update_opportunity(
    opp_id: int,
    data: OpportunityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunita non trovata")

    update_data = data.model_dump(exclude_unset=True)

    # Validate state transition
    if "stato" in update_data:
        current = PipelineState(opp.stato)
        new = PipelineState(update_data["stato"])
        if new not in VALID_TRANSITIONS.get(current, []):
            raise HTTPException(
                status_code=400,
                detail=f"Transizione non valida: {current.value} -> {new.value}"
            )
        if new == PipelineState.PERSO and not update_data.get("motivo_perdita"):
            raise HTTPException(status_code=400, detail="Motivo perdita obbligatorio")

        # Auto-create contract on win
        if new == PipelineState.VINTO:
            contract = Contract(
                opportunity_id=opp.id,
                contact_id=opp.contact_id,
                titolo=opp.titolo,
                valore_totale=opp.valore_stimato,
                data_inizio=datetime.now(timezone.utc),
            )
            db.add(contract)

    for field, value in update_data.items():
        if field == "data_chiusura_prevista" and value:
            value = datetime.strptime(value, "%Y-%m-%d")
        setattr(opp, field, value)

    db.commit()
    db.refresh(opp)
    log_action(db, agent="api", action="update_opportunity", user_id=current_user.id,
               entity_type="opportunity", entity_id=opp.id,
               details={"changes": update_data})
    return opp


# ============ CONTRACTS ============

@router.get("/contracts", response_model=List[ContractResponse])
def list_contracts(
    stato: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Contract)
    if stato:
        query = query.filter(Contract.stato == stato)
    return query.order_by(Contract.created_at.desc()).all()


@router.get("/contracts/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contratto non trovato")
    return contract


# ============ SAL ============

@router.get("/contracts/{contract_id}/sal", response_model=List[SALResponse])
def list_sal(
    contract_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(SAL).filter(SAL.contract_id == contract_id).order_by(SAL.numero_sal).all()


@router.post("/sal", response_model=SALResponse, status_code=201)
def create_sal(
    data: SALCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contratto non trovato")

    last_sal = (
        db.query(SAL)
        .filter(SAL.contract_id == data.contract_id)
        .order_by(SAL.numero_sal.desc())
        .first()
    )
    numero = (last_sal.numero_sal + 1) if last_sal else 1

    sal = SAL(
        contract_id=data.contract_id,
        numero_sal=numero,
        percentuale_avanzamento=data.percentuale_avanzamento,
        importo_maturato=data.importo_maturato,
        descrizione=data.descrizione,
        note=data.note,
    )
    db.add(sal)
    db.commit()
    db.refresh(sal)
    log_action(db, agent="api", action="create_sal", user_id=current_user.id,
               entity_type="sal", entity_id=sal.id)
    return sal


# ============ PIPELINE STATS ============

@router.get("/pipeline/stats", response_model=PipelineStats)
def pipeline_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opps = db.query(Opportunity).all()
    per_stato = {}
    vinte = 0
    perse = 0
    valore_totale = 0.0

    for o in opps:
        if o.stato not in per_stato:
            per_stato[o.stato] = {"count": 0, "value": 0.0}
        per_stato[o.stato]["count"] += 1
        per_stato[o.stato]["value"] += o.valore_stimato
        valore_totale += o.valore_stimato
        if o.stato == "vinto":
            vinte += 1
        elif o.stato == "perso":
            perse += 1

    closed = vinte + perse
    win_rate = (vinte / closed * 100) if closed > 0 else 0

    return PipelineStats(
        totale_opportunita=len(opps),
        valore_totale=valore_totale,
        per_stato=per_stato,
        win_rate=round(win_rate, 1),
        vinte=vinte,
        perse=perse,
    )
