from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_customer, require_admin
from app.customer_service.models import Customer
from app.loan_service import service
from app.loan_service.schemas import LoanApplicationRequest, LoanDetailResponse, LoanResponse

router = APIRouter(prefix="/api/loans", tags=["Loan Service"])


@router.post("/apply", response_model=LoanResponse)
def apply_for_loan(
    request: LoanApplicationRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.apply(db, current_customer, request)


@router.get("", response_model=list[LoanResponse])
def list_my_loans(db: Session = Depends(get_db), current_customer: Customer = Depends(get_current_customer)):
    return service.list_for_customer(db, current_customer)


@router.get("/{loan_id}", response_model=LoanDetailResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db), current_customer: Customer = Depends(get_current_customer)):
    return service.get_detail(db, current_customer, loan_id)


@router.post("/{loan_id}/approve", response_model=LoanResponse)
def approve_loan(loan_id: int, db: Session = Depends(get_db), _admin: Customer = Depends(require_admin)):
    return service.approve(db, loan_id)


@router.post("/{loan_id}/reject", response_model=LoanResponse)
def reject_loan(loan_id: int, db: Session = Depends(get_db), _admin: Customer = Depends(require_admin)):
    return service.reject(db, loan_id)


@router.post("/{loan_id}/repay", response_model=LoanDetailResponse)
def repay_installment(
    loan_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.repay_next_installment(db, current_customer, loan_id)
