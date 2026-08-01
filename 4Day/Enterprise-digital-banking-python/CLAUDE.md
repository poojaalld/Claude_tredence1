# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## What this is

A FastAPI + SQLAlchemy digital banking backend - the Python sibling of
`../Enterprise-digital-banking-java` (Spring Boot). Same modular-monolith idea, package-per-domain,
re-expressed in Python, plus two domains the Java project doesn't have: Loan Service and
Notification Service. See `README.md` for the full architecture writeup and API table.

## Commands

```bash
# Install dependencies (from a venv)
venv\Scripts\pip install -r requirements.txt

# Run the app locally (reads config from application.yml / .env, creates SQLite tables on startup)
venv\Scripts\python run.py
# or: venv\Scripts\python -m uvicorn app.main:app --reload

# Run the full test suite (isolated in-memory SQLite, no external DB needed)
venv\Scripts\python -m pytest -q

# Run a single test file
venv\Scripts\python -m pytest tests/test_loan_service.py -q

# Run a single test
venv\Scripts\python -m pytest tests/test_loan_service.py::test_full_loan_lifecycle_apply_approve_repay_close -q
```

There is no linter/formatter configured in the project yet.

## Architecture

One deployable FastAPI app, organized into package-per-domain modules under `app/`. Each module
follows the same shape - `models.py` / `repository.py` / `service.py` / `router.py` (+
`schemas.py` for request/response DTOs) - so once you've read one module the others follow the
same pattern.

- **`core/`** - cross-cutting concerns shared by every domain: `config.py` loads
  `application.yml` (`${VAR:default}` interpolation, same style as the Java project's Spring
  config) into a single `settings` object; `database.py` owns the SQLAlchemy engine/session/
  `Base`; `security.py` does bcrypt hashing + JWT issue/verify; `deps.py` has the
  `get_current_customer`/`require_admin` FastAPI dependencies; `exceptions.py` maps domain
  exceptions to HTTP responses in one place.
- **`customer_service/`** - registration, login (JWT issuance), profile. `Role` is `CUSTOMER` or
  `ADMIN`; there is no self-service promotion to admin by design (see Never modify below).
- **`payment_service/`** - accounts + deposits/withdrawals/transfers. `credit()`/`debit()` in
  `payment_service/service.py` are the *only* functions that mutate `Account.balance` anywhere in
  the codebase, and `Account.version` is mapped as `version_id_col` (optimistic locking) so
  concurrent transactions can't silently clobber a balance - mirrors the Java project's
  `AccountService.credit`/`debit` + `@Version` invariant exactly.
- **`loan_service/`** - loan application, admin approve/reject, EMI repayment. Disbursement and
  repayment call into `payment_service.record_loan_disbursement`/`record_loan_repayment`, which
  themselves go through `credit()`/`debit()` - loan_service never touches `Account.balance`
  directly. Each installment is a flat EMI amount (interest is baked into the EMI formula but not
  split out per-installment) - a documented simplification, not a bug.
- **`notification_service/`** - `notify()` is called by the other three services on every
  customer-facing event. Persists a `Notification` row and logs it under the `CONSOLE` channel
  from `application.yml`; swap in a real email/SMS provider call inside `notify()` without
  touching any calling service.

### Request flow

`Router` -> `Service` (business rules) -> `Repository` (SQLAlchemy). Routers stay thin: Pydantic
schemas for request validation, `Depends(get_current_customer)`/`Depends(require_admin)` for auth,
response mapping via `SomeResponse.model_validate(entity)`. Services raise
`ResourceNotFoundException` (404), `BadRequestException` (400), or `ForbiddenException` (403)
instead of building HTTP responses themselves - `core/exceptions.py` is the single place that maps
them to JSON.

## Never modify

- **Never mutate `Account.balance` outside `payment_service/service.py`'s `credit()`/`debit()`.**
  Every balance change must be written together with its audit `Transaction` row in the same
  commit. This includes loan disbursement/repayment - route those through
  `record_loan_disbursement`/`record_loan_repayment`, not direct field assignment.
- **Never let customer self-registration set `role=ADMIN`.** `customer_service/service.py::register`
  always creates `Role.CUSTOMER`. Admin promotion is a manual, out-of-band DB operation (see
  README's snippet / `tests/conftest.py::make_admin`) - don't add an API path that lets a caller
  choose their own role.
- **Never hardcode secrets into `application.yml`.** Use the existing `${VAR:default}` placeholders
  and put real values in `.env` (gitignored). Don't commit `.env`, `*.db`, or `venv/`.
- **Never remove the `Account.version` / `version_id_col` optimistic-locking column** when touching
  `payment_service/models.py` - it's what prevents concurrent credit/debit calls from silently
  clobbering each other.
- **Never bypass the service layer from a router.** Routers must not import `repository.py` or
  query models directly - only call functions in the matching `service.py`, so business rules stay
  in one place and stay testable without the HTTP layer.
