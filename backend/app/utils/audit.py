from __future__ import annotations

from sqlalchemy.orm import Session
from app.models.audit import AuditLog, Notification


def log_action(
    db: Session,
    agent: str,
    action: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
):
    entry = AuditLog(
        user_id=user_id,
        agent=agent,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    db.commit()
    return entry


def create_notification(
    db: Session,
    user_id: int,
    agent: str,
    type: str,
    title: str,
    message: str,
):
    notif = Notification(
        user_id=user_id,
        agent=agent,
        type=type,
        title=title,
        message=message,
    )
    db.add(notif)
    db.commit()
    return notif
