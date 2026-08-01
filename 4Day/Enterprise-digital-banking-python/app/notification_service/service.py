"""Notification dispatch.

`notify()` is called by other services (payment_service, loan_service,
customer_service) whenever a customer-facing event happens. In this lab the
CONSOLE channel just logs the message - swap in a real email/SMS provider
call here for production without touching any calling service.
"""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.notification_service import repository
from app.notification_service.models import Notification, NotificationChannel, NotificationStatus, NotificationType
from app.notification_service.schemas import NotificationResponse

logger = logging.getLogger("notification_service")


def notify(db: Session, customer_id: int, type_: NotificationType, message: str) -> Notification:
    channel = NotificationChannel(settings.notification_channel)

    logger.info("[NOTIFY:%s] customer=%s type=%s message=%s", channel.value, customer_id, type_.value, message)

    notification = Notification(
        customer_id=customer_id,
        type=type_,
        channel=channel,
        message=message,
        status=NotificationStatus.SENT,
    )
    return repository.create(db, notification)


def list_for_customer(db: Session, customer_id: int) -> list[NotificationResponse]:
    return [NotificationResponse.model_validate(n) for n in repository.list_by_customer(db, customer_id)]
