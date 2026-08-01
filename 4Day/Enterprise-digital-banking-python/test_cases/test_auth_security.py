from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from test_cases.conftest import auth_headers, register_customer


def test_hash_password_is_salted_and_verifies_correctly():
    hashed_a = hash_password("secret123")
    hashed_b = hash_password("secret123")
    assert hashed_a != hashed_b
    assert verify_password("secret123", hashed_a)
    assert verify_password("secret123", hashed_b)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("secret123")
    assert not verify_password("wrong-password", hashed)


def test_decode_access_token_round_trips_subject_and_role():
    token = create_access_token("alice@example.com", "CUSTOMER")
    payload = decode_access_token(token)
    assert payload["sub"] == "alice@example.com"
    assert payload["role"] == "CUSTOMER"


def test_decode_access_token_rejects_tampered_signature():
    token = create_access_token("alice@example.com", "CUSTOMER")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_decode_access_token_rejects_expired_token():
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "alice@example.com",
        "role": "CUSTOMER",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=1),
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(expired_token)


def test_protected_endpoint_rejects_malformed_bearer_token(client):
    response = client.get("/api/customers/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_protected_endpoint_rejects_missing_authorization_header(client):
    response = client.get("/api/customers/me")
    assert response.status_code in (401, 403)


def test_protected_endpoint_rejects_token_for_unknown_customer(client):
    token = create_access_token("ghost@example.com", "CUSTOMER")
    response = client.get("/api/customers/me", headers=auth_headers(token))
    assert response.status_code == 401


def test_protected_endpoint_rejects_expired_token(client):
    register_customer(client, email="expired@example.com")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "expired@example.com",
        "role": "CUSTOMER",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=1),
    }
    expired_token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    response = client.get("/api/customers/me", headers=auth_headers(expired_token))
    assert response.status_code == 401
