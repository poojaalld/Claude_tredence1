from sqlalchemy import select
from sqlalchemy.orm import Session

from app.customer_service.models import Customer


def get_by_id(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def get_by_email(db: Session, email: str) -> Customer | None:
    return db.scalar(select(Customer).where(Customer.email == email))


def list_all(db: Session) -> list[Customer]:
    return list(db.scalars(select(Customer).order_by(Customer.id)))


def create(db: Session, customer: Customer) -> Customer:
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def save(db: Session, customer: Customer) -> Customer:
    db.commit()
    db.refresh(customer)
    return customer
