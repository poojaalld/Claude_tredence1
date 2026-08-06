from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.beneficiary_service import service
from app.beneficiary_service.schemas import AddBeneficiaryRequest, BeneficiaryResponse, UpdateBeneficiaryRequest
from app.core.database import get_db
from app.core.deps import get_current_customer
from app.customer_service.models import Customer

router = APIRouter(prefix="/api/beneficiaries", tags=["Beneficiary Service"])


@router.post("", response_model=BeneficiaryResponse)
def add_beneficiary(
    request: AddBeneficiaryRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.add_beneficiary(db, current_customer, request)


@router.get("", response_model=list[BeneficiaryResponse])
def list_my_beneficiaries(db: Session = Depends(get_db), current_customer: Customer = Depends(get_current_customer)):
    return service.list_my_beneficiaries(db, current_customer)


@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(
    beneficiary_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.get_beneficiary(db, current_customer, beneficiary_id)


@router.put("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    request: UpdateBeneficiaryRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return service.update_beneficiary(db, current_customer, beneficiary_id, request)


@router.delete("/{beneficiary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_beneficiary(
    beneficiary_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    service.delete_beneficiary(db, current_customer, beneficiary_id)
