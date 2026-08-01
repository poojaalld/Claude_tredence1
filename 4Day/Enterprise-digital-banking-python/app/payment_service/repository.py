from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payment_service.models import Account, Transaction


def create_account(db: Session, account: Account) -> Account:
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def get_account_by_number(db: Session, account_number: str) -> Account | None:
    return db.scalar(select(Account).where(Account.account_number == account_number))


def get_account_by_id(db: Session, account_id: int) -> Account | None:
    return db.get(Account, account_id)


def list_accounts_by_customer(db: Session, customer_id: int) -> list[Account]:
    stmt = select(Account).where(Account.customer_id == customer_id).order_by(Account.id)
    return list(db.scalars(stmt))


def account_number_exists(db: Session, account_number: str) -> bool:
    return get_account_by_number(db, account_number) is not None


def save_account(db: Session, account: Account) -> Account:
    db.commit()
    db.refresh(account)
    return account


def create_transaction(db: Session, transaction: Transaction) -> Transaction:
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def list_transactions_by_account(db: Session, account_id: int) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.account_id == account_id).order_by(Transaction.created_at.desc())
    return list(db.scalars(stmt))
