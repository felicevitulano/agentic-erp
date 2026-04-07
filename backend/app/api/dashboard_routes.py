from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import User, get_db
from app.models.audit import AuditLog, Notification
from app.models.sales import Opportunity, Contract
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Pipeline value (active opportunities, excluding won/lost)
    active_opps = db.query(func.sum(Opportunity.valore_stimato)).filter(
        Opportunity.stato.notin_(["vinto", "perso"])
    ).scalar() or 0

    # Active contracts value
    active_contracts = db.query(func.count(Contract.id)).filter(
        Contract.stato == "attivo"
    ).scalar() or 0

    # Won this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fatturato_mese = db.query(func.sum(Opportunity.valore_stimato)).filter(
        Opportunity.stato == "vinto",
        Opportunity.updated_at >= month_start,
    ).scalar() or 0

    # Stale opportunities (same state for >14 days)
    stale_date = now - timedelta(days=14)
    stale_opps = db.query(func.count(Opportunity.id)).filter(
        Opportunity.stato.notin_(["vinto", "perso"]),
        Opportunity.updated_at < stale_date,
    ).scalar() or 0

    return {
        "pipeline_value": active_opps,
        "fatturato_mese": fatturato_mese,
        "progetti_attivi": active_contracts,
        "task_scaduti": stale_opps,
        "prossime_scadenze": [],
    }


@router.get("/notifications")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if notif:
        notif.read = 1
        db.commit()
    return {"ok": True}


@router.get("/audit-log")
def get_audit_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    agent: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
):
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if agent:
        query = query.filter(AuditLog.agent == agent)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.limit(limit).all()


@router.get("/agents/status")
def get_agents_status(current_user: User = Depends(get_current_user)):
    from app.agents import get_all_agents
    return [
        {
            "id": cls.AGENT_ID,
            "name": cls.AGENT_NAME,
            "description": cls.DESCRIPTION,
        }
        for cls in get_all_agents()
    ]
