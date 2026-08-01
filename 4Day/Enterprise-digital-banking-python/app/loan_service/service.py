"""Loan application, approval, and repayment.

Disbursement and repayment never touch Account.balance directly - they go
through payment_service.record_loan_disbursement/record_loan_repayment,
which themselves call payment_service.credit/debit, preserving the single
money-movement invariant defined in payment_service/service.py.

Simplification: EMI is computed with the standard reducing-balance formula,
but every installment is a flat EMI amount rather than a full
principal/interest amortization split - fine for this lab, not a substitute
for a real amortization table.
"""

from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestException, ForbiddenException, ResourceNotFoundException
from app.customer_service.models import Customer, Role
from app.loan_service import repository
from app.loan_service.models import InstallmentStatus, Loan, LoanInstallment, LoanStatus
from app.loan_service.schemas import InstallmentResponse, LoanApplicationRequest, LoanDetailResponse, LoanResponse
from app.notification_service import service as notification_service
from app.notification_service.models import NotificationType
from app.payment_service import repository as payment_repository
from app.payment_service import service as payment_service

TWO_PLACES = Decimal("0.01")


def calculate_emi(principal: Decimal, annual_rate: Decimal, tenure_months: int) -> Decimal:
    if annual_rate == 0:
        return (principal / tenure_months).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return emi.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def apply(db: Session, customer: Customer, request: LoanApplicationRequest) -> LoanResponse:
    min_amount = Decimal(str(settings.loan_min_amount))
    max_amount = Decimal(str(settings.loan_max_amount))
    if not (min_amount <= request.principal_amount <= max_amount):
        raise BadRequestException(f"Loan amount must be between {min_amount} and {max_amount}")
    if request.tenure_months > settings.loan_max_tenure_months:
        raise BadRequestException(f"Tenure cannot exceed {settings.loan_max_tenure_months} months")

    account = payment_service.get_owned_account(db, customer, request.account_number)

    interest_rate = Decimal(str(settings.loan_default_interest_rate))
    emi = calculate_emi(request.principal_amount, interest_rate, request.tenure_months)

    loan = Loan(
        customer_id=customer.id,
        account_id=account.id,
        principal_amount=request.principal_amount,
        interest_rate=interest_rate,
        tenure_months=request.tenure_months,
        emi_amount=emi,
        status=LoanStatus.PENDING,
    )
    loan = repository.create_loan(db, loan)
    _generate_installments(db, loan)

    notification_service.notify(
        db, customer.id, NotificationType.LOAN_APPLIED,
        f"Loan application #{loan.id} for {loan.principal_amount} submitted. "
        f"EMI: {loan.emi_amount}/month for {loan.tenure_months} months.",
    )
    return LoanResponse.model_validate(loan)


def _generate_installments(db: Session, loan: Loan) -> None:
    installments = [
        LoanInstallment(loan_id=loan.id, installment_number=i, due_amount=loan.emi_amount)
        for i in range(1, loan.tenure_months + 1)
    ]
    repository.add_installments(db, installments)


def list_for_customer(db: Session, customer: Customer) -> list[LoanResponse]:
    return [LoanResponse.model_validate(loan) for loan in repository.list_loans_by_customer(db, customer.id)]


def _get_loan_or_404(db: Session, loan_id: int) -> Loan:
    loan = repository.get_loan_by_id(db, loan_id)
    if loan is None:
        raise ResourceNotFoundException(f"Loan {loan_id} not found")
    return loan


def _assert_owner_or_admin(customer: Customer, loan: Loan) -> None:
    if loan.customer_id != customer.id and customer.role != Role.ADMIN:
        raise ForbiddenException("You do not have access to this loan")


def get_detail(db: Session, customer: Customer, loan_id: int) -> LoanDetailResponse:
    loan = _get_loan_or_404(db, loan_id)
    _assert_owner_or_admin(customer, loan)
    installments = repository.list_installments(db, loan.id)
    return LoanDetailResponse(
        **LoanResponse.model_validate(loan).model_dump(),
        installments=[InstallmentResponse.model_validate(i) for i in installments],
    )


def approve(db: Session, loan_id: int) -> LoanResponse:
    loan = _get_loan_or_404(db, loan_id)
    if loan.status != LoanStatus.PENDING:
        raise BadRequestException(f"Loan {loan_id} is not pending approval (status: {loan.status.value})")

    account = payment_repository.get_account_by_id(db, loan.account_id)
    if account is None:
        raise ResourceNotFoundException(f"Disbursement account for loan {loan_id} not found")

    payment_service.record_loan_disbursement(db, account, loan.principal_amount, loan.id)

    loan.status = LoanStatus.ACTIVE
    loan.decided_at = datetime.now(timezone.utc)
    loan = repository.save_loan(db, loan)

    notification_service.notify(
        db, loan.customer_id, NotificationType.LOAN_APPROVED,
        f"Loan #{loan.id} approved. {loan.principal_amount} disbursed to account {account.account_number}.",
    )
    return LoanResponse.model_validate(loan)


def reject(db: Session, loan_id: int) -> LoanResponse:
    loan = _get_loan_or_404(db, loan_id)
    if loan.status != LoanStatus.PENDING:
        raise BadRequestException(f"Loan {loan_id} is not pending approval (status: {loan.status.value})")

    loan.status = LoanStatus.REJECTED
    loan.decided_at = datetime.now(timezone.utc)
    loan = repository.save_loan(db, loan)

    notification_service.notify(db, loan.customer_id, NotificationType.LOAN_REJECTED, f"Loan #{loan.id} application was rejected.")
    return LoanResponse.model_validate(loan)


def repay_next_installment(db: Session, customer: Customer, loan_id: int) -> LoanDetailResponse:
    loan = _get_loan_or_404(db, loan_id)
    _assert_owner_or_admin(customer, loan)
    if loan.status != LoanStatus.ACTIVE:
        raise BadRequestException(f"Loan {loan_id} is not active (status: {loan.status.value})")

    installment = repository.get_next_pending_installment(db, loan.id)
    if installment is None:
        raise BadRequestException(f"Loan {loan_id} has no pending installments")

    account = payment_repository.get_account_by_id(db, loan.account_id)
    payment_service.record_loan_repayment(db, account, installment.due_amount, loan.id)

    installment.status = InstallmentStatus.PAID
    installment.paid_at = datetime.now(timezone.utc)
    repository.save_installment(db, installment)

    notification_service.notify(
        db, loan.customer_id, NotificationType.LOAN_REPAYMENT,
        f"Installment #{installment.installment_number} of {installment.due_amount} paid for loan #{loan.id}.",
    )

    if repository.count_pending_installments(db, loan.id) == 0:
        loan.status = LoanStatus.CLOSED
        repository.save_loan(db, loan)
        notification_service.notify(db, loan.customer_id, NotificationType.LOAN_CLOSED, f"Loan #{loan.id} fully repaid and closed.")

    return get_detail(db, customer, loan.id)
