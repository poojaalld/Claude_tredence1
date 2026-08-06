from sqlalchemy.orm import Session

from app.beneficiary_service import repository
from app.beneficiary_service.models import Beneficiary
from app.beneficiary_service.schemas import AddBeneficiaryRequest, BeneficiaryResponse, UpdateBeneficiaryRequest
from app.core.exceptions import BadRequestException, ForbiddenException, ResourceNotFoundException
from app.customer_service.models import Customer, Role
from app.payment_service import repository as payment_repository


def add_beneficiary(db: Session, customer: Customer, request: AddBeneficiaryRequest) -> BeneficiaryResponse:
    account = payment_repository.get_account_by_number(db, request.account_number)
    if account is None:
        raise ResourceNotFoundException(f"Account {request.account_number} not found")
    if account.customer_id == customer.id:
        raise BadRequestException("You cannot add your own account as a beneficiary")
    if repository.get_by_customer_and_account(db, customer.id, request.account_number) is not None:
        raise BadRequestException(f"Beneficiary with account {request.account_number} already exists")

    beneficiary = Beneficiary(
        customer_id=customer.id,
        nickname=request.nickname,
        beneficiary_name=request.beneficiary_name,
        account_number=request.account_number,
        bank_name=request.bank_name,
    )
    beneficiary = repository.create(db, beneficiary)
    return BeneficiaryResponse.model_validate(beneficiary)


def get_owned_beneficiary(db: Session, customer: Customer, beneficiary_id: int) -> Beneficiary:
    beneficiary = repository.get_by_id(db, beneficiary_id)
    if beneficiary is None:
        raise ResourceNotFoundException(f"Beneficiary {beneficiary_id} not found")
    if beneficiary.customer_id != customer.id and customer.role != Role.ADMIN:
        raise ForbiddenException("You do not have access to this beneficiary")
    return beneficiary


def get_beneficiary(db: Session, customer: Customer, beneficiary_id: int) -> BeneficiaryResponse:
    return BeneficiaryResponse.model_validate(get_owned_beneficiary(db, customer, beneficiary_id))


def list_my_beneficiaries(db: Session, customer: Customer) -> list[BeneficiaryResponse]:
    return [BeneficiaryResponse.model_validate(b) for b in repository.list_by_customer(db, customer.id)]


def update_beneficiary(
    db: Session, customer: Customer, beneficiary_id: int, request: UpdateBeneficiaryRequest
) -> BeneficiaryResponse:
    beneficiary = get_owned_beneficiary(db, customer, beneficiary_id)
    if request.nickname is not None:
        beneficiary.nickname = request.nickname
    if request.beneficiary_name is not None:
        beneficiary.beneficiary_name = request.beneficiary_name
    if request.bank_name is not None:
        beneficiary.bank_name = request.bank_name
    if request.status is not None:
        beneficiary.status = request.status
    beneficiary = repository.save(db, beneficiary)
    return BeneficiaryResponse.model_validate(beneficiary)


def delete_beneficiary(db: Session, customer: Customer, beneficiary_id: int) -> None:
    beneficiary = get_owned_beneficiary(db, customer, beneficiary_id)
    repository.delete(db, beneficiary)
