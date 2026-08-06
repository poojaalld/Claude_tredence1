from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.payment_service.models import AccountStatus, AccountType, TransactionType


class CreateAccountRequest(BaseModel):
    account_type: AccountType


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    account_type: AccountType
    balance: Decimal
    status: AccountStatus
    created_at: datetime


class DepositRequest(BaseModel):
    account_number: str
    amount: Decimal = Field(gt=0)
    description: str | None = None


class WithdrawRequest(BaseModel):
    account_number: str
    amount: Decimal = Field(gt=0)
    description: str | None = None


class TransferRequest(BaseModel):
    source_account_number: str
    target_account_number: str
    amount: Decimal = Field(gt=0)
    description: str | None = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    related_account_id: int | None
    description: str | None
    created_at: datetime
