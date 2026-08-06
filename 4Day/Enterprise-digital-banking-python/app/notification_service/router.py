from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_customer
from app.customer_service.models import Customer
from app.notification_service import service
from app.notification_service.schemas import NotificationResponse

router = APIRouter(prefix="/api/notifications", tags=["Notification Service"])


@router.get("", response_model=list[NotificationResponse])
def list_my_notifications(db: Session = Depends(get_db), current_customer: Customer = Depends(get_current_customer)):
    return service.list_for_customer(db, current_customer.id)
