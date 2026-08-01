from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_customer, require_admin
from app.customer_service import service
from app.customer_service.models import Customer
from app.customer_service.schemas import (
    AuthResponse,
    CustomerResponse,
    LoginRequest,
    RegisterRequest,
    UpdateCustomerRequest,
)

auth_router = APIRouter(prefix="/api/auth", tags=["Customer Service - Auth"])
customer_router = APIRouter(prefix="/api/customers", tags=["Customer Service"])


@auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return service.register(db, request)


@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return service.login(db, request)


@customer_router.get("/me", response_model=CustomerResponse)
def get_my_profile(current_customer: Customer = Depends(get_current_customer)):
    return service.get_profile(current_customer)


@customer_router.put("/me", response_model=CustomerResponse)
def update_my_profile(
    request: UpdateCustomerRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.update_profile(db, current_customer, request)


@customer_router.get("", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db), _admin: Customer = Depends(require_admin)):
    return service.list_customers(db)


@customer_router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), _admin: Customer = Depends(require_admin)):
    return service.get_customer_by_id(db, customer_id)
