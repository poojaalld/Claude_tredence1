from sqlalchemy import select
from sqlalchemy.orm import Session

from app.notification_service.models import Notification


def create(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_by_id(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def list_by_customer(db: Session, customer_id: int) -> list[Notification]:
    stmt = select(Notification).where(Notification.customer_id == customer_id).order_by(Notification.sent_at.desc())
    return list(db.scalars(stmt))
