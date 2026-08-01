from tests.conftest import auth_headers, register_customer


def test_notifications_require_auth(client):
    response = client.get("/api/notifications")
    assert response.status_code in (401, 403)


def test_account_and_payment_events_generate_notifications(client):
    data = register_customer(client, email="ruth@example.com")
    headers = auth_headers(data["access_token"])

    account = client.post("/api/accounts", json={"account_type": "SAVINGS"}, headers=headers).json()
    client.post("/api/payments/deposit", json={"account_number": account["account_number"], "amount": "100.00"}, headers=headers)
    client.post("/api/payments/withdraw", json={"account_number": account["account_number"], "amount": "40.00"}, headers=headers)

    response = client.get("/api/notifications", headers=headers)
    assert response.status_code == 200
    types = [n["type"] for n in response.json()]
    assert "ACCOUNT_CREATED" in types
    assert "DEPOSIT" in types
    assert "WITHDRAWAL" in types


def test_loan_application_generates_notification(client):
    data = register_customer(client, email="sam@example.com")
    headers = auth_headers(data["access_token"])
    account = client.post("/api/accounts", json={"account_type": "SAVINGS"}, headers=headers).json()

    client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "15000", "tenure_months": 12},
        headers=headers,
    )

    response = client.get("/api/notifications", headers=headers)
    types = [n["type"] for n in response.json()]
    assert "LOAN_APPLIED" in types
