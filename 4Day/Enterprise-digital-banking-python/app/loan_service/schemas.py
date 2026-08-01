from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.loan_service.models import InstallmentStatus, LoanStatus


class LoanApplicationRequest(BaseModel):
    account_number: str
    principal_amount: Decimal = Field(gt=0)
    tenure_months: int = Field(gt=0)


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    installment_number: int
    due_amount: Decimal
    status: InstallmentStatus
    paid_at: datetime | None


class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    principal_amount: Decimal
    interest_rate: Decimal
    tenure_months: int
    emi_amount: Decimal
    status: LoanStatus
    applied_at: datetime
    decided_at: datetime | None


class LoanDetailResponse(LoanResponse):
    installments: list[InstallmentResponse]
