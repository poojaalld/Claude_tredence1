import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
from app.beneficiary_service.router import router as beneficiary_router
from app.core.database import create_all_tables
from app.core.exceptions import register_exception_handlers
from app.customer_service.router import auth_router, customer_router
from app.loan_service.router import router as loan_router
from app.notification_service.router import router as notification_router
from app.payment_service.router import account_router, payment_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_all_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(account_router)
app.include_router(payment_router)
app.include_router(loan_router)
app.include_router(notification_router)
app.include_router(beneficiary_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "UP", "service": settings.app_name, "version": settings.app_version}
