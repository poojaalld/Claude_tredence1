import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db

# Import every model module so its table is registered on Base.metadata.
from app.customer_service import models as _customer_models  # noqa: F401
from app.loan_service import models as _loan_models  # noqa: F401
from app.notification_service import models as _notification_models  # noqa: F401
from app.payment_service import models as _payment_models  # noqa: F401
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def register_customer(client, email="alice@example.com", password="secret123", full_name="Alice Anderson"):
    response = client.post(
        "/api/auth/register",
        json={"full_name": full_name, "email": email, "phone": "1234567890", "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_admin(email: str) -> None:
    from app.customer_service.models import Role

    db = TestingSessionLocal()
    try:
        customer = db.query(_customer_models.Customer).filter_by(email=email).one()
        customer.role = Role.ADMIN
        db.commit()
    finally:
        db.close()
