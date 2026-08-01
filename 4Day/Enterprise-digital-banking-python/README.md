# Enterprise Digital Banking (Python)

A Python/FastAPI implementation of the digital banking platform, alongside
the sibling Spring Boot project at `../Enterprise-digital-banking-java`.
Same core ideas - modular monolith, package-per-domain, JWT auth, thin
routers over a service layer - re-expressed in FastAPI + SQLAlchemy, and
extended with two new domains the Java project doesn't have: **Loan
Service** and **Notification Service**.

## Architecture

One deployable FastAPI app, organized into package-per-domain modules under
`app/`. Each module follows the same shape - `models.py` / `repository.py`
/ `service.py` / `router.py` (+ `schemas.py` for request/response DTOs) -
so once you've read one module the others follow the same pattern.

```
app/
├── main.py                 # FastAPI app: routers, exception handlers, lifespan table creation
├── core/
│   ├── config.py             # Loads application.yml (${VAR:default} interpolation) -> settings
│   ├── database.py            # SQLAlchemy engine/session/Base + get_db dependency
│   ├── security.py             # bcrypt password hashing + JWT issue/verify
│   ├── deps.py                  # get_current_customer / require_admin FastAPI dependencies
│   └── exceptions.py             # ResourceNotFoundException/BadRequestException/... -> HTTP responses
├── customer_service/         # Registration, login, profile (mirrors Java's auth/ module)
├── payment_service/           # Accounts + deposits/withdrawals/transfers
├── loan_service/                # Loan application, approval, EMI, repayment schedule
└── notification_service/         # Event notifications (console-logged in this lab)
```

### Customer Service

Registration, login (JWT issuance), and profile management. `Customer.role`
is `CUSTOMER` or `ADMIN` - admin-only endpoints are gated by the
`require_admin` FastAPI dependency in `core/deps.py`. There's no self-service
promotion to admin (as in a real bank); for this lab, promote a test user by
updating their row directly (see `tests/conftest.py::make_admin` for the
pattern), e.g.:

```python
# one-off, e.g. via `python -c` with the app importable
from app.core.database import SessionLocal
from app.customer_service.models import Customer, Role
db = SessionLocal()
c = db.query(Customer).filter_by(email="you@example.com").one()
c.role = Role.ADMIN
db.commit()
```

### Payment Service

Accounts and money movement. **Invariant** (mirrors the Java project's
`AccountService.credit`/`debit`): `payment_service.service.credit()` and
`debit()` are the *only* functions anywhere in the codebase that mutate
`Account.balance`, and every mutation is written together with its audit
`Transaction` row in the same commit. `loan_service` disburses/collects
money by calling `record_loan_disbursement`/`record_loan_repayment` in this
module - it never touches `Account.balance` itself.

`Account` also carries a `version` column mapped as SQLAlchemy's
`version_id_col`, mirroring the Java entity's `@Version` field: two
concurrent credit/debit calls on the same account can't silently clobber
each other's balance write (a `StaleDataError` is raised instead).

### Loan Service

Loan application, admin approval/rejection, and EMI repayment, built on top
of Payment Service:

- `apply` - validates the amount/tenure against `application.yml` limits,
  computes the EMI with the standard reducing-balance formula, and
  generates one `LoanInstallment` row per month (status `PENDING`).
- `approve` (admin) - credits the principal into the loan's account via
  `payment_service.record_loan_disbursement` and moves the loan to `ACTIVE`.
- `repay` - pays the next pending installment by debiting the account via
  `payment_service.record_loan_repayment`; once every installment is
  `PAID`, the loan moves to `CLOSED`.

Simplification for this lab: each installment is a flat EMI amount rather
than a full principal/interest amortization split. Because the EMI includes
interest, the account needs deposits beyond the disbursed principal to fully
repay the loan - see `tests/test_loan_service.py::test_full_loan_lifecycle_*`
for a worked example.

### Notification Service

`notify()` is called by the other three services whenever a customer-facing
event happens (account opened, deposit/withdrawal/transfer, loan applied/
approved/rejected/repaid/closed). Every notification is persisted
(`GET /api/notifications`) and "dispatched" by logging to stdout under the
`CONSOLE` channel configured in `application.yml` - swap in a real email/SMS
provider call inside `notification_service/service.py::notify` without
touching any calling service.

### Request flow & error handling

`Router` -> `Service` (business rules, transaction boundary) -> `Repository`
(SQLAlchemy). Routers stay thin: request validation via Pydantic schemas,
auth via `Depends(get_current_customer)` / `Depends(require_admin)`.
Services raise `ResourceNotFoundException` (404), `BadRequestException`
(400), or `ForbiddenException` (403) instead of building HTTP responses
themselves; `core/exceptions.py::register_exception_handlers` is the single
place that maps them (plus request validation errors) to JSON responses.

## Configuration - `application.yml`

Config lives in `application.yml` at the project root, using the same
`${VAR:default}` interpolation style as the Java project's Spring Boot
config, loaded by `app/core/config.py`:

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

Copy `.env.example` to `.env` to override any of these without editing
`application.yml` directly - `${VAR:default}` falls back to `default` only
when `VAR` isn't set in the environment or `.env`.

Storage defaults to a local SQLite file (`digital_banking.db`), matching the
Java project's "no external DB needed to try it" H2-for-tests convention.
Point `DB_URL` at a Postgres connection string for anything beyond local
development - SQLAlchemy handles the rest.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run

```bash
python run.py
# or: venv\Scripts\python -m uvicorn app.main:app --reload
```

Tables are created automatically on startup. Interactive API docs:
`http://localhost:8000/docs`. Health check: `GET /health`.

## Test

```bash
venv\Scripts\python -m pytest -q
```

20 tests across all four services, using an isolated in-memory SQLite
database (see `tests/conftest.py`) - registration/login, profile updates,
admin-only access checks, account creation, deposit/withdraw/transfer
(including insufficient-funds and cross-customer access denial), the EMI
formula, and a full loan lifecycle (apply -> admin approve -> disburse ->
repay to closure).

## API summary

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | - | Register a customer, returns a JWT |
| POST | `/api/auth/login` | - | Log in, returns a JWT |
| GET | `/api/customers/me` | customer | Current profile |
| PUT | `/api/customers/me` | customer | Update name/phone |
| GET | `/api/customers` | admin | List all customers |
| GET | `/api/customers/{id}` | admin | Get a customer by id |
| POST | `/api/accounts` | customer | Open an account |
| GET | `/api/accounts` | customer | List my accounts |
| GET | `/api/accounts/{account_number}` | owner/admin | Get account details |
| POST | `/api/payments/deposit` | customer | Deposit into own account |
| POST | `/api/payments/withdraw` | customer | Withdraw from own account |
| POST | `/api/payments/transfer` | customer | Transfer to any account |
| GET | `/api/payments/{account_number}/transactions` | owner/admin | Transaction history |
| POST | `/api/loans/apply` | customer | Apply for a loan against one of my accounts |
| GET | `/api/loans` | customer | List my loans |
| GET | `/api/loans/{id}` | owner/admin | Loan detail + installment schedule |
| POST | `/api/loans/{id}/approve` | admin | Approve + disburse a pending loan |
| POST | `/api/loans/{id}/reject` | admin | Reject a pending loan |
| POST | `/api/loans/{id}/repay` | owner/admin | Pay the next due installment |
| GET | `/api/notifications` | customer | My notification history |

## Differences from the Java project / possible next steps

- Adds Loan Service and Notification Service, which the Java project
  doesn't have.
- This is a modular monolith, not four independently deployed
  microservices - each package is written with clear boundaries (own
  models/schemas/router, cross-module calls only through another module's
  `service.py`) specifically so it could be split into separately deployed
  services later (one FastAPI app per package, HTTP/queue calls in place of
  direct Python calls) without restructuring the business logic itself.
- Not yet covered: pagination on list endpoints, refresh tokens, rate
  limiting, a real amortization (principal/interest split) schedule, and a
  real email/SMS provider behind `notification_service`.
