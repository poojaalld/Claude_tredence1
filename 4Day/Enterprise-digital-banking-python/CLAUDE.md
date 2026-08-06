# Enterprise Digital Banking Platform

A modular Python/FastAPI implementation of a comprehensive digital banking system that supports customer authentication, account management, payments, loan processing, and notifications.

## Project Overview

**Architecture Type:** Modular Monolith (Package-per-Domain)  
**Framework:** FastAPI with SQLAlchemy ORM  
**Language:** Python 3.9+  
**Database:** SQLite (default) / PostgreSQL (production)  
**API Style:** REST with JWT Authentication

This project mirrors the Java/Spring Boot implementation but extends it with two additional domains:
- **Loan Service** - Complete loan lifecycle management
- **Notification Service** - Event-driven customer notifications

## Core Architecture

The application is organized as a modular monolith with four independent domain packages under `app/`:

```
app/
├── main.py                      # FastAPI app entry point, routers, exception handlers
├── core/
│   ├── config.py               # Environment & YAML config loading
│   ├── database.py             # SQLAlchemy setup, session factory, Base models
│   ├── security.py             # Password hashing (bcrypt), JWT operations
│   ├── deps.py                 # FastAPI dependency injection (auth guards)
│   └── exceptions.py           # Custom exceptions & HTTP response mappers
├── customer_service/           # Authentication & profile management
│   ├── models.py               # Customer, Role entities
│   ├── schemas.py              # Request/response DTOs
│   ├── repository.py           # Database access (queries/inserts)
│   ├── service.py              # Business logic (registration, login, profile)
│   └── router.py               # HTTP endpoints
├── payment_service/            # Accounts & money movement
│   ├── models.py               # Account, Transaction entities
│   ├── schemas.py              # DTOs
│   ├── repository.py           # Query/insert/update operations
│   ├── service.py              # Credit/debit with invariants, transfers
│   └── router.py               # Endpoints for accounts & payments
├── loan_service/               # Loan application, approval, repayment
│   ├── models.py               # Loan, LoanInstallment entities
│   ├── schemas.py              # DTOs
│   ├── repository.py           # Database operations
│   ├── service.py              # Apply, approve, repay logic
│   └── router.py               # Loan endpoints
└── notification_service/       # Event notifications
    ├── models.py               # Notification entity
    ├── schemas.py              # DTOs
    ├── repository.py           # Persistence
    ├── service.py              # notify() - called by other services
    └── router.py               # Query endpoints
```

## Domain Modules

### Customer Service
Handles registration, authentication, and profile management.

**Key Features:**
- User registration with email validation
- JWT-based login (token issued on successful authentication)
- Password hashing with bcrypt
- Role-based access control (CUSTOMER / ADMIN)
- Profile updates (name, phone)

**Key Endpoints:**
- `POST /api/auth/register` - Register new customer
- `POST /api/auth/login` - Authenticate & receive JWT
- `GET /api/customers/me` - Current user profile
- `PUT /api/customers/me` - Update profile
- `GET /api/customers` (admin) - List all customers
- `GET /api/customers/{id}` (admin) - Get customer details

**Important:** Admin role cannot be self-assigned. Promote a user via direct database update:
```python
from app.core.database import SessionLocal
from app.customer_service.models import Customer, Role

db = SessionLocal()
customer = db.query(Customer).filter_by(email="user@example.com").one()
customer.role = Role.ADMIN
db.commit()
```

---

### Payment Service
Manages bank accounts and all money movement (deposits, withdrawals, transfers).

**Key Features:**
- Account creation per customer
- Deposit/withdrawal with balance validation
- Inter-account transfers
- Full transaction audit trail
- Optimistic locking via SQLAlchemy `version_id_col` (prevents concurrent balance corruption)
- Cross-customer transfer validation

**Key Invariants:**
- `payment_service.service.credit()` and `debit()` are the **only** functions that mutate `Account.balance`
- Every balance mutation is recorded with an audit `Transaction` in the same database commit
- `Account.version` prevents concurrent writes from silently overwriting each other (raises `StaleDataError` instead)

**Key Endpoints:**
- `POST /api/accounts` - Open a new account
- `GET /api/accounts` - List my accounts
- `GET /api/accounts/{account_number}` - Account details
- `POST /api/payments/deposit` - Deposit funds
- `POST /api/payments/withdraw` - Withdraw funds
- `POST /api/payments/transfer` - Transfer to another account
- `GET /api/payments/{account_number}/transactions` - Transaction history

**Constraints:**
- Insufficient funds blocks withdrawals/transfers
- Customers cannot transfer to or access accounts owned by others (unless admin)

---

### Loan Service
Manages the complete loan lifecycle: application, approval, disbursement, and repayment with EMI schedule.

**Workflow:**
1. **Apply** - Customer requests loan against one of their accounts
   - Validates amount (min/max from config)
   - Validates tenure (max from config)
   - Computes EMI using reducing-balance formula
   - Generates `LoanInstallment` rows (one per month, status=PENDING)
   - Loan status: PENDING_APPROVAL

2. **Approve (Admin)** - Administrator reviews and approves
   - Calls `payment_service.record_loan_disbursement()` to credit principal
   - Sets loan status: ACTIVE
   - Customer can now repay installments

3. **Reject (Admin)** - Reject a pending loan
   - Sets status: REJECTED
   - No funds disbursed

4. **Repay (Customer/Admin)** - Pay next due installment
   - Debits EMI amount via `payment_service.record_loan_repayment()`
   - Marks installment: PAID
   - Once all installments PAID → Loan status: CLOSED

**EMI Calculation:**
Uses reducing-balance formula. Note: EMI is a flat monthly amount that **includes interest**, so customers must deposit additional funds beyond the principal to fully repay (see test examples for worked scenarios).

**Key Endpoints:**
- `POST /api/loans/apply` - Apply for loan
- `GET /api/loans` - List my loans
- `GET /api/loans/{id}` - Loan details + installment schedule
- `POST /api/loans/{id}/approve` (admin) - Approve & disburse
- `POST /api/loans/{id}/reject` (admin) - Reject loan
- `POST /api/loans/{id}/repay` - Pay next installment

**Important:** Loan disbursement and repayment go through Payment Service, never directly mutating account balance.

---

### Notification Service
Publishes customer-facing events from other services.

**Triggered By:**
- Customer Service: registration, profile update
- Payment Service: deposit, withdrawal, transfer
- Loan Service: application, approval, rejection, repayment, closure

**Current Implementation:**
- All notifications persisted to database
- "Dispatched" via console logging (stdout)
- Easy to swap for real email/SMS providers (modify `notify()` in `notification_service/service.py`)

**Key Endpoints:**
- `GET /api/notifications` - Retrieve my notification history

---

## Request Flow & Error Handling

**Standard Layer Pattern:**
```
Router (HTTP layer)
  ↓ (Pydantic validation, auth via Depends())
Service (Business rules, transactions)
  ↓
Repository (SQLAlchemy queries/mutations)
  ↓
Database
```

**Error Handling:**
- Services raise custom exceptions: `ResourceNotFoundException`, `BadRequestException`, `ForbiddenException`
- Routers do NOT build HTTP responses; they propagate exceptions
- `core/exceptions.py::register_exception_handlers` is the single source of truth that maps exceptions to JSON responses
- Request validation errors automatically return 400 with Pydantic error details

**Example:**
```python
# service.py
def get_account(self, account_number: str) -> Account:
    account = self.repository.get_by_number(account_number)
    if not account:
        raise ResourceNotFoundException(f"Account {account_number} not found")
    return account

# router.py
@router.get("/{account_number}")
async def get_account(
    account_number: str,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> AccountSchema:
    service = AccountService(db)
    return service.get_account(account_number)  # Exception propagates → handler converts to 400
```

---

## Configuration (`application.yml`)

Config uses Spring Boot-style variable interpolation (`${VAR:default}`):

```yaml
server:
  port: ${SERVER_PORT:8000}

database:
  url: ${DB_URL:sqlite:///./digital_banking.db}

jwt:
  secret: ${JWT_SECRET:change-this-to-a-long-random-secret-in-every-environment}
  expiration-minutes: ${JWT_EXPIRATION_MINUTES:1440}

loan:
  default-interest-rate: ${LOAN_DEFAULT_INTEREST_RATE:10.5}
  max-tenure-months: ${LOAN_MAX_TENURE_MONTHS:360}
  min-amount: ${LOAN_MIN_AMOUNT:10000}
  max-amount: ${LOAN_MAX_AMOUNT:5000000}

notification:
  channel: ${NOTIFICATION_CHANNEL:CONSOLE}
```

**Loaded by:** `app/core/config.py`  
**Override via `.env`:** Copy `.env.example` to `.env`, OpenCode will use those values in place of yaml/defaults

---

## Setup & Execution

### Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate          # Windows
# venv/bin/activate            # macOS/Linux
pip install -r requirements.txt
```

### Run the Application
```bash
python run.py
# or: python -m uvicorn app.main:app --reload
```

Tables are created automatically on startup.  
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Health Check:** `GET /health`

### Run Tests
```bash
python -m pytest -q
```

20 tests covering:
- Registration, login, profile management
- Admin access control
- Account creation, deposit, withdraw, transfer (with edge cases)
- Insufficient funds handling
- Cross-customer access denial
- EMI formula verification
- Full loan lifecycle (apply → approve → disburse → repay → closure)

**Test Database:** Isolated in-memory SQLite (configured in `tests/conftest.py`)

---

## Database & Storage

**Default:** SQLite file (`digital_banking.db`) - no external dependencies for local development.  
**Production:** Set `DB_URL` to a PostgreSQL connection string (e.g., `postgresql://user:pass@localhost/banking_db`)

SQLAlchemy abstracts the database layer - no code changes needed when switching databases.

---

## Key Design Decisions

1. **Modular Monolith** - Package-per-domain with clear boundaries (no circular imports). Can be split into independently deployed microservices later by replacing direct Python calls with HTTP/message queue calls.

2. **Service Layer as Transaction Boundary** - Business logic lives in `service.py`; repositories are thin data-access wrappers.

3. **Constructor Injection** - Dependencies passed explicitly (no magic service locators).

4. **DTO Pattern** - Pydantic `schemas.py` separates request/response format from internal models.

5. **Optimistic Locking** - Account version column prevents concurrent balance mutations from silently overwriting each other.

6. **Event-Driven Notifications** - Services call `notification_service.notify()` instead of handling notifications themselves (decoupling, easy to replace with real email/SMS).

7. **Centralized Exception Handling** - Single exception handler registry maps domain exceptions to HTTP responses.

---

## API Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | - | Register customer |
| POST | `/api/auth/login` | - | Log in, get JWT |
| GET | `/api/customers/me` | customer | Current profile |
| PUT | `/api/customers/me` | customer | Update name/phone |
| GET | `/api/customers` | admin | List all customers |
| GET | `/api/customers/{id}` | admin | Get customer by id |
| POST | `/api/accounts` | customer | Open account |
| GET | `/api/accounts` | customer | List my accounts |
| GET | `/api/accounts/{account_number}` | owner/admin | Account details |
| POST | `/api/payments/deposit` | customer | Deposit to own account |
| POST | `/api/payments/withdraw` | customer | Withdraw from own account |
| POST | `/api/payments/transfer` | customer | Transfer to any account |
| GET | `/api/payments/{account_number}/transactions` | owner/admin | Transaction history |
| POST | `/api/loans/apply` | customer | Apply for loan |
| GET | `/api/loans` | customer | List my loans |
| GET | `/api/loans/{id}` | owner/admin | Loan detail + schedule |
| POST | `/api/loans/{id}/approve` | admin | Approve & disburse |
| POST | `/api/loans/{id}/reject` | admin | Reject loan |
| POST | `/api/loans/{id}/repay` | owner/admin | Pay next installment |
| GET | `/api/notifications` | customer | My notification history |

---

## What's Not (Yet) Covered

- Pagination on list endpoints
- Refresh tokens
- Rate limiting
- Real amortization schedule (principal/interest split per installment)
- Real email/SMS provider integration
- Request/response logging middleware
- API versioning
- Distributed tracing
- High-availability database replication

---

## Development Workflow

1. **Understand one domain** (read `app/customer_service/` top-to-bottom)
2. **Apply the same pattern** to other domains - they're structurally identical
3. **Modify business logic** in `service.py`, queries in `repository.py`
4. **Add endpoints** in `router.py` with Pydantic schema validation
5. **Test** with pytest (tests automatically create tables, use in-memory DB)
6. **Deploy** as a single FastAPI Docker image (or split by domain into microservices later)

---

## Related Projects

- **Java/Spring Boot version** - Same banking concepts, different tech stack: `../Enterprise-digital-banking-java`

---

## NEVER_MODIFY

The following directories and files should **never** be modified:

```
database/
migration/
uat/

contracts/
openapi/
terraform/
kubernetes/
Jenkinsfile
```

These are managed by infrastructure, DevOps, and contract teams and should not be altered without explicit approval from the respective owners.
