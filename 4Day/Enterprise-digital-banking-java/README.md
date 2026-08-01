# Enterprise Digital Banking

A modular-monolith digital banking backend built with Spring Boot 3 (Java 17). It exposes REST
APIs for customer authentication, account management, and money movement (deposits, withdrawals,
transfers), backed by PostgreSQL.

## Prerequisites

- Java 17+
- Maven 3.9+ (or use the included `mvnw` wrapper if present)
- PostgreSQL 14+ running locally, or a connection string to a remote instance

## Configuration

The app reads its config from environment variables, all with sane local defaults
(see `src/main/resources/application.yml`):

| Variable | Default | Purpose |
|---|---|---|
| `DB_URL` | `jdbc:postgresql://localhost:5432/digital_banking` | JDBC connection string |
| `DB_USERNAME` | `postgres` | Database user |
| `DB_PASSWORD` | `postgres` | Database password |
| `SERVER_PORT` | `8080` | HTTP port |
| `JWT_SECRET` | (dev placeholder) | HMAC signing key for JWTs — **override in every real environment** |
| `JWT_EXPIRATION_MS` | `86400000` (24h) | JWT token lifetime |

## Running locally

```bash
mvn spring-boot:run
```

## Building

```bash
mvn clean package
```

## Testing

```bash
mvn test
```

Tests run against an in-memory H2 database (`src/test/resources/application.yml`), so no
PostgreSQL instance is required to run the test suite.

## API overview

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | none | Create a customer account |
| POST | `/api/auth/login` | none | Exchange credentials for a JWT |
| POST | `/api/accounts` | Bearer JWT | Open a new account for the authenticated user |
| GET | `/api/accounts` | Bearer JWT | List the authenticated user's accounts |
| GET | `/api/accounts/{accountNumber}` | Bearer JWT | Fetch a single account |
| POST | `/api/transactions/deposit` | Bearer JWT | Deposit funds into an account |
| POST | `/api/transactions/withdraw` | Bearer JWT | Withdraw funds from an account |
| POST | `/api/transactions/transfer` | Bearer JWT | Move funds between two accounts |
| GET | `/api/transactions/account/{accountNumber}` | Bearer JWT | Transaction history for an account |

All endpoints other than `/api/auth/**` require an `Authorization: Bearer <token>` header.
