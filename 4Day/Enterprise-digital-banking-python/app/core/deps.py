import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.customer_service import repository as customer_repository
from app.customer_service.models import Customer, Role

bearer_scheme = HTTPBearer()


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError:
        raise UnauthorizedException("Invalid or expired authentication token")

    customer = customer_repository.get_by_email(db, payload.get("sub", ""))
    if customer is None:
        raise UnauthorizedException("Invalid or expired authentication token")
    return customer


def require_admin(current_customer: Customer = Depends(get_current_customer)) -> Customer:
    if current_customer.role != Role.ADMIN:
        raise ForbiddenException("Admin privileges required")
    return current_customer
