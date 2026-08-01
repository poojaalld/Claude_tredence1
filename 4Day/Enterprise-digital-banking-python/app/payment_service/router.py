from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_customer
from app.customer_service.models import Customer
from app.payment_service import service
from app.payment_service.schemas import (
    AccountResponse,
    CreateAccountRequest,
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)

account_router = APIRouter(prefix="/api/accounts", tags=["Payment Service - Accounts"])
payment_router = APIRouter(prefix="/api/payments", tags=["Payment Service - Payments"])


@account_router.post("", response_model=AccountResponse)
def create_account(
    request: CreateAccountRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.create_account(db, current_customer, request)


@account_router.get("", response_model=list[AccountResponse])
def list_my_accounts(db: Session = Depends(get_db), current_customer: Customer = Depends(get_current_customer)):
    return service.list_my_accounts(db, current_customer)


@account_router.get("/{account_number}", response_model=AccountResponse)
def get_account(
    account_number: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.get_account_response(db, current_customer, account_number)


@payment_router.post("/deposit", response_model=TransactionResponse)
def deposit(
    request: DepositRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.deposit(db, current_customer, request)


@payment_router.post("/withdraw", response_model=TransactionResponse)
def withdraw(
    request: WithdrawRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.withdraw(db, current_customer, request)


@payment_router.post("/transfer", response_model=TransactionResponse)
def transfer(
    request: TransferRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.transfer(db, current_customer, request)


@payment_router.get("/{account_number}/transactions", response_model=list[TransactionResponse])
def get_transaction_history(
    account_number: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.list_transactions(db, current_customer, account_number)
