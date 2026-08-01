"""Account + transaction orchestration.

Money-movement invariant: `credit()` and `debit()` are the ONLY functions
that mutate `Account.balance`, anywhere in the codebase - including from
loan_service (see record_loan_disbursement/record_loan_repayment below).
Every balance mutation is written together with its audit `Transaction`
row inside the same DB session/commit.
"""

import secrets
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ForbiddenException, ResourceNotFoundException
from app.customer_service.models import Customer, Role
from app.notification_service import service as notification_service
from app.notification_service.models import NotificationType
from app.payment_service import repository
from app.payment_service.models import Account, AccountType, Transaction, TransactionType
from app.payment_service.schemas import (
    AccountResponse,
    CreateAccountRequest,
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawRequest,
)


def _generate_account_number(db: Session) -> str:
    while True:
        candidate = "ACCT" + "".join(secrets.choice("0123456789") for _ in range(10))
        if not repository.account_number_exists(db, candidate):
            return candidate


def create_account(db: Session, customer: Customer, request: CreateAccountRequest) -> AccountResponse:
    account = Account(
        account_number=_generate_account_number(db),
        customer_id=customer.id,
        account_type=request.account_type,
        balance=Decimal("0.00"),
    )
    account = repository.create_account(db, account)
    notification_service.notify(
        db, customer.id, NotificationType.ACCOUNT_CREATED,
        f"Account {account.account_number} ({account.account_type.value}) has been opened.",
    )
    return AccountResponse.model_validate(account)


def list_my_accounts(db: Session, customer: Customer) -> list[AccountResponse]:
    return [AccountResponse.model_validate(a) for a in repository.list_accounts_by_customer(db, customer.id)]


def get_owned_account(db: Session, customer: Customer, account_number: str) -> Account:
    account = repository.get_account_by_number(db, account_number)
    if account is None:
        raise ResourceNotFoundException(f"Account {account_number} not found")
    if account.customer_id != customer.id and customer.role != Role.ADMIN:
        raise ForbiddenException("You do not have access to this account")
    return account


def get_account_response(db: Session, customer: Customer, account_number: str) -> AccountResponse:
    return AccountResponse.model_validate(get_owned_account(db, customer, account_number))


def credit(db: Session, account: Account, amount: Decimal) -> None:
    account.balance = account.balance + amount
    repository.save_account(db, account)


def debit(db: Session, account: Account, amount: Decimal) -> None:
    if account.balance < amount:
        raise BadRequestException(f"Insufficient funds in account {account.account_number}")
    account.balance = account.balance - amount
    repository.save_account(db, account)


def _record_transaction(
    db: Session,
    account: Account,
    type_: TransactionType,
    amount: Decimal,
    related_account_id: int | None = None,
    description: str | None = None,
) -> Transaction:
    transaction = Transaction(
        account_id=account.id,
        type=type_,
        amount=amount,
        balance_after=account.balance,
        related_account_id=related_account_id,
        description=description,
    )
    return repository.create_transaction(db, transaction)


def deposit(db: Session, customer: Customer, request: DepositRequest) -> TransactionResponse:
    account = get_owned_account(db, customer, request.account_number)
    credit(db, account, request.amount)
    transaction = _record_transaction(db, account, TransactionType.DEPOSIT, request.amount, description=request.description)
    notification_service.notify(
        db, customer.id, NotificationType.DEPOSIT,
        f"{request.amount} deposited into {account.account_number}. New balance: {account.balance}.",
    )
    return TransactionResponse.model_validate(transaction)


def withdraw(db: Session, customer: Customer, request: WithdrawRequest) -> TransactionResponse:
    account = get_owned_account(db, customer, request.account_number)
    debit(db, account, request.amount)
    transaction = _record_transaction(db, account, TransactionType.WITHDRAWAL, request.amount, description=request.description)
    notification_service.notify(
        db, customer.id, NotificationType.WITHDRAWAL,
        f"{request.amount} withdrawn from {account.account_number}. New balance: {account.balance}.",
    )
    return TransactionResponse.model_validate(transaction)


def transfer(db: Session, customer: Customer, request: TransferRequest) -> TransactionResponse:
    if request.source_account_number == request.target_account_number:
        raise BadRequestException("Source and target accounts must be different")

    source = get_owned_account(db, customer, request.source_account_number)
    target = repository.get_account_by_number(db, request.target_account_number)
    if target is None:
        raise ResourceNotFoundException(f"Account {request.target_account_number} not found")

    debit(db, source, request.amount)
    credit(db, target, request.amount)

    debit_txn = _record_transaction(
        db, source, TransactionType.TRANSFER, request.amount, related_account_id=target.id, description=request.description
    )
    _record_transaction(
        db, target, TransactionType.TRANSFER, request.amount, related_account_id=source.id, description=request.description
    )

    notification_service.notify(
        db, customer.id, NotificationType.TRANSFER,
        f"{request.amount} sent from {source.account_number} to {target.account_number}.",
    )
    if target.customer_id != customer.id:
        notification_service.notify(
            db, target.customer_id, NotificationType.TRANSFER,
            f"{request.amount} received into {target.account_number} from {source.account_number}.",
        )

    return TransactionResponse.model_validate(debit_txn)


def list_transactions(db: Session, customer: Customer, account_number: str) -> list[TransactionResponse]:
    account = get_owned_account(db, customer, account_number)
    return [TransactionResponse.model_validate(t) for t in repository.list_transactions_by_account(db, account.id)]


# --- Used by loan_service. Both go through credit()/debit() so the money-movement
# invariant above holds even for loan disbursement/repayment. ---


def record_loan_disbursement(db: Session, account: Account, amount: Decimal, loan_id: int) -> Transaction:
    credit(db, account, amount)
    return _record_transaction(
        db, account, TransactionType.LOAN_DISBURSEMENT, amount, description=f"Disbursement for loan #{loan_id}"
    )


def record_loan_repayment(db: Session, account: Account, amount: Decimal, loan_id: int) -> Transaction:
    debit(db, account, amount)
    return _record_transaction(
        db, account, TransactionType.LOAN_REPAYMENT, amount, description=f"Repayment for loan #{loan_id}"
    )
