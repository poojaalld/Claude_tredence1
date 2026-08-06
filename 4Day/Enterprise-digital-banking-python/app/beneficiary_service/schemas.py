from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.beneficiary_service.models import BeneficiaryStatus


class AddBeneficiaryRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=100)
    beneficiary_name: str = Field(min_length=1, max_length=120)
    account_number: str = Field(min_length=1, max_length=20)
    bank_name: str | None = Field(default=None, max_length=120)


class UpdateBeneficiaryRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=100)
    beneficiary_name: str | None = Field(default=None, min_length=1, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    status: BeneficiaryStatus | None = None


class BeneficiaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    nickname: str
    beneficiary_name: str
    account_number: str
    bank_name: str | None
    status: BeneficiaryStatus
    created_at: datetime
