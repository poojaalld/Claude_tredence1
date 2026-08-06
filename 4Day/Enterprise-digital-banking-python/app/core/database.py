from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, echo=settings.database_echo, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    # Import every model module so its table is registered on Base.metadata
    # before create_all runs.
    from app.beneficiary_service import models as _beneficiary_models  # noqa: F401
    from app.customer_service import models as _customer_models  # noqa: F401
    from app.loan_service import models as _loan_models  # noqa: F401
    from app.notification_service import models as _notification_models  # noqa: F401
    from app.payment_service import models as _payment_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
