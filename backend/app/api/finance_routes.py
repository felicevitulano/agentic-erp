from __future__ import annotations

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.finance import Fattura, TipoFattura, StatoFattura
from app.schemas.finance import FatturaCreate, FatturaUpdate, FatturaResponse, CashFlowItem, ReportMensile
from app.auth.jwt import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["finance"])


# --- Fatture CRUD ---

@router.get("/fatture", response_model=List[FatturaResponse])
def list_fatture(
    tipo: Optional[str] = None,
    stato: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Fattura)
    if tipo:
        query = query.filter(Fattura.tipo == tipo)
    if stato:
        query = query.filter(Fattura.stato == stato)
    return query.order_by(Fattura.data_scadenza.desc()).all()


@router.get("/fatture/{fattura_id}", response_model=FatturaResponse)
def get_fattura(fattura_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
    if not fattura:
        raise HTTPException(404, "Fattura non trovata")
    return fattura


@router.post("/fatture", response_model=FatturaResponse, status_code=201)
def create_fattura(data: FatturaCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(Fattura).filter(Fattura.numero == data.numero).first()
    if existing:
        raise HTTPException(400, f"Fattura con numero '{data.numero}' gia' esistente")

    importo_totale = data.importo * (1 + data.iva / 100)

    fattura = Fattura(
        contract_id=data.contract_id,
        tipo=data.tipo,
        numero=data.numero,
        importo=data.importo,
        iva=data.iva,
        importo_totale=importo_totale,
        data_scadenza=datetime.strptime(data.data_scadenza, "%Y-%m-%d").replace(tzinfo=timezone.utc),
        fornitore_o_cliente=data.fornitore_o_cliente,
        note=data.note,
    )
    if data.data_emissione:
        fattura.data_emissione = datetime.strptime(data.data_emissione, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    db.add(fattura)
    db.commit()
    db.refresh(fattura)
    return fattura


@router.put("/fatture/{fattura_id}", response_model=FatturaResponse)
def update_fattura(fattura_id: int, data: FatturaUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fattura = db.query(Fattura).filter(Fattura.id == fattura_id).first()
    if not fattura:
        raise HTTPException(404, "Fattura non trovata")

    if data.stato is not None:
        fattura.stato = data.stato
    if data.data_pagamento is not None:
        fattura.data_pagamento = datetime.strptime(data.data_pagamento, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if data.note is not None:
        fattura.note = data.note

    db.commit()
    db.refresh(fattura)
    return fattura


# --- Scadenzario ---

@router.get("/scadenzario")
def scadenzario(
    giorni: int = 30,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    limit = now + timedelta(days=giorni)

    query = db.query(Fattura).filter(
        Fattura.data_scadenza <= limit,
        Fattura.stato != StatoFattura.PAGATA.value,
    )
    if tipo:
        query = query.filter(Fattura.tipo == tipo)

    fatture = query.order_by(Fattura.data_scadenza).all()

    items = []
    for f in fatture:
        ds = f.data_scadenza.replace(tzinfo=timezone.utc) if f.data_scadenza.tzinfo is None else f.data_scadenza
        days_to = (ds - now).days
        items.append({
            "id": f.id,
            "numero": f.numero,
            "tipo": f.tipo,
            "importo_totale": f.importo_totale,
            "fornitore_o_cliente": f.fornitore_o_cliente,
            "data_scadenza": f.data_scadenza.isoformat(),
            "stato": f.stato,
            "giorni_alla_scadenza": days_to,
        })

    return {"scadenze": items, "totale": len(items)}


# --- Cash Flow ---

@router.get("/cash-flow")
def cash_flow(
    mesi: int = 6,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    result = []

    for i in range(-2, mesi):  # 2 mesi passati + N futuri
        target = now + relativedelta(months=i)
        month_start = target.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + relativedelta(months=1)

        fatture = db.query(Fattura).filter(
            Fattura.data_scadenza >= month_start,
            Fattura.data_scadenza < month_end,
        ).all()

        entrate = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.ATTIVA.value)
        uscite = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.PASSIVA.value)

        result.append({
            "mese": target.strftime("%Y-%m"),
            "label": target.strftime("%b %Y"),
            "entrate": round(entrate, 2),
            "uscite": round(uscite, 2),
            "saldo": round(entrate - uscite, 2),
            "is_past": i < 0,
        })

    return {"cash_flow": result}


# --- Report Mensile ---

@router.get("/finance/report-mensile")
def report_mensile(
    mese: Optional[int] = None,
    anno: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    m = mese or now.month
    y = anno or now.year

    month_start = datetime(y, m, 1, tzinfo=timezone.utc)
    month_end = month_start + relativedelta(months=1)
    prev_start = month_start - relativedelta(months=1)

    def _stats(start, end):
        fatture = db.query(Fattura).filter(
            Fattura.data_emissione >= start,
            Fattura.data_emissione < end,
        ).all()
        ent = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.ATTIVA.value)
        usc = sum(f.importo_totale for f in fatture if f.tipo == TipoFattura.PASSIVA.value)
        pag = sum(1 for f in fatture if f.stato == StatoFattura.PAGATA.value)
        sca = sum(1 for f in fatture if f.stato == StatoFattura.SCADUTA.value)
        return ent, usc, len(fatture), pag, sca

    entrate, uscite, emesse, pagate, scadute = _stats(month_start, month_end)
    prev_e, prev_u, _, _, _ = _stats(prev_start, month_start)

    return {
        "mese": f"{y}-{m:02d}",
        "entrate": round(entrate, 2),
        "uscite": round(uscite, 2),
        "saldo": round(entrate - uscite, 2),
        "fatture_emesse": emesse,
        "fatture_pagate": pagate,
        "fatture_scadute": scadute,
        "variazione_entrate": round((entrate - prev_e) / prev_e * 100, 1) if prev_e > 0 else None,
        "variazione_uscite": round((uscite - prev_u) / prev_u * 100, 1) if prev_u > 0 else None,
    }


# --- Fatture Scadute ---

@router.get("/fatture-scadute")
def fatture_scadute(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    scadute = (
        db.query(Fattura)
        .filter(
            Fattura.tipo == TipoFattura.ATTIVA.value,
            Fattura.stato != StatoFattura.PAGATA.value,
            Fattura.data_scadenza < now,
        )
        .order_by(Fattura.data_scadenza)
        .all()
    )

    items = []
    for f in scadute:
        ds = f.data_scadenza.replace(tzinfo=timezone.utc) if f.data_scadenza.tzinfo is None else f.data_scadenza
        days_overdue = (now - ds).days
        items.append({
            "id": f.id,
            "numero": f.numero,
            "importo_totale": f.importo_totale,
            "fornitore_o_cliente": f.fornitore_o_cliente,
            "data_scadenza": f.data_scadenza.isoformat(),
            "giorni_scaduta": days_overdue,
            "alert_30gg": days_overdue > 30,
        })

    return {
        "fatture_scadute": items,
        "totale": len(items),
        "valore_totale_scaduto": round(sum(i["importo_totale"] for i in items), 2),
    }
