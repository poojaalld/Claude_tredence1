from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.notification_service.models import NotificationChannel, NotificationStatus, NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: NotificationType
    channel: NotificationChannel
    message: str
    status: NotificationStatus
    sent_at: datetime
