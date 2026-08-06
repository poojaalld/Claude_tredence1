from sqlalchemy import select
from sqlalchemy.orm import Session

from app.loan_service.models import InstallmentStatus, Loan, LoanInstallment


def create_loan(db: Session, loan: Loan) -> Loan:
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan


def save_loan(db: Session, loan: Loan) -> Loan:
    db.commit()
    db.refresh(loan)
    return loan


def get_loan_by_id(db: Session, loan_id: int) -> Loan | None:
    return db.get(Loan, loan_id)


def list_loans_by_customer(db: Session, customer_id: int) -> list[Loan]:
    stmt = select(Loan).where(Loan.customer_id == customer_id).order_by(Loan.applied_at.desc())
    return list(db.scalars(stmt))


def add_installments(db: Session, installments: list[LoanInstallment]) -> None:
    db.add_all(installments)
    db.commit()


def list_installments(db: Session, loan_id: int) -> list[LoanInstallment]:
    stmt = (
        select(LoanInstallment)
        .where(LoanInstallment.loan_id == loan_id)
        .order_by(LoanInstallment.installment_number)
    )
    return list(db.scalars(stmt))


def get_next_pending_installment(db: Session, loan_id: int) -> LoanInstallment | None:
    stmt = (
        select(LoanInstallment)
        .where(LoanInstallment.loan_id == loan_id, LoanInstallment.status == InstallmentStatus.PENDING)
        .order_by(LoanInstallment.installment_number)
        .limit(1)
    )
    return db.scalar(stmt)


def save_installment(db: Session, installment: LoanInstallment) -> LoanInstallment:
    db.commit()
    db.refresh(installment)
    return installment


def count_pending_installments(db: Session, loan_id: int) -> int:
    stmt = select(LoanInstallment).where(
        LoanInstallment.loan_id == loan_id, LoanInstallment.status == InstallmentStatus.PENDING
    )
    return len(list(db.scalars(stmt)))
