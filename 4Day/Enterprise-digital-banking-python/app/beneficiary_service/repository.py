from sqlalchemy import select
from sqlalchemy.orm import Session

from app.beneficiary_service.models import Beneficiary


def create(db: Session, beneficiary: Beneficiary) -> Beneficiary:
    db.add(beneficiary)
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def get_by_id(db: Session, beneficiary_id: int) -> Beneficiary | None:
    return db.get(Beneficiary, beneficiary_id)


def get_by_customer_and_account(db: Session, customer_id: int, account_number: str) -> Beneficiary | None:
    stmt = select(Beneficiary).where(
        Beneficiary.customer_id == customer_id,
        Beneficiary.account_number == account_number,
    )
    return db.scalar(stmt)


def list_by_customer(db: Session, customer_id: int) -> list[Beneficiary]:
    stmt = select(Beneficiary).where(Beneficiary.customer_id == customer_id).order_by(Beneficiary.id)
    return list(db.scalars(stmt))


def save(db: Session, beneficiary: Beneficiary) -> Beneficiary:
    db.commit()
    db.refresh(beneficiary)
    return beneficiary


def delete(db: Session, beneficiary: Beneficiary) -> None:
    db.delete(beneficiary)
    db.commit()
