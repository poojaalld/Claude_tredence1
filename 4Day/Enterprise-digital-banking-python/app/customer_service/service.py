from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.core.security import create_access_token, hash_password, verify_password
from app.customer_service import repository
from app.customer_service.models import Customer
from app.customer_service.schemas import (
    AuthResponse,
    CustomerResponse,
    LoginRequest,
    RegisterRequest,
    UpdateCustomerRequest,
)


def register(db: Session, request: RegisterRequest) -> AuthResponse:
    if repository.get_by_email(db, request.email) is not None:
        raise BadRequestException(f"An account with email {request.email} already exists")

    customer = Customer(
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        hashed_password=hash_password(request.password),
    )
    customer = repository.create(db, customer)
    return _issue_auth_response(customer)


def login(db: Session, request: LoginRequest) -> AuthResponse:
    customer = repository.get_by_email(db, request.email)
    if customer is None or not verify_password(request.password, customer.hashed_password):
        raise BadRequestException("Invalid email or password")
    return _issue_auth_response(customer)


def get_profile(customer: Customer) -> CustomerResponse:
    return CustomerResponse.model_validate(customer)


def update_profile(db: Session, customer: Customer, request: UpdateCustomerRequest) -> CustomerResponse:
    if request.full_name is not None:
        customer.full_name = request.full_name
    if request.phone is not None:
        customer.phone = request.phone
    customer = repository.save(db, customer)
    return CustomerResponse.model_validate(customer)


def list_customers(db: Session) -> list[CustomerResponse]:
    return [CustomerResponse.model_validate(c) for c in repository.list_all(db)]


def get_customer_by_id(db: Session, customer_id: int) -> CustomerResponse:
    customer = repository.get_by_id(db, customer_id)
    if customer is None:
        raise ResourceNotFoundException(f"Customer {customer_id} not found")
    return CustomerResponse.model_validate(customer)


def _issue_auth_response(customer: Customer) -> AuthResponse:
    token = create_access_token(subject=customer.email, role=customer.role.value)
    return AuthResponse(access_token=token, customer=CustomerResponse.model_validate(customer))
