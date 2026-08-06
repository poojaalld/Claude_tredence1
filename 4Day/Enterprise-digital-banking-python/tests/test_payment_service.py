from tests.conftest import auth_headers, register_customer


def _open_account(client, headers, account_type="SAVINGS"):
    response = client.post("/api/accounts", json={"account_type": account_type}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_create_account_and_deposit(client):
    data = register_customer(client, email="gina@example.com")
    headers = auth_headers(data["access_token"])

    account = _open_account(client, headers)
    assert account["balance"] == "0.00"

    response = client.post(
        "/api/payments/deposit",
        json={"account_number": account["account_number"], "amount": "500.00"},
        headers=headers,
    )
    assert response.status_code == 200
    txn = response.json()
    assert txn["type"] == "DEPOSIT"
    assert txn["balance_after"] == "500.00"


def test_withdraw_insufficient_funds_rejected(client):
    data = register_customer(client, email="henry@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/payments/withdraw",
        json={"account_number": account["account_number"], "amount": "100.00"},
        headers=headers,
    )
    assert response.status_code == 400


def test_transfer_between_accounts(client):
    sender = register_customer(client, email="ivan@example.com")
    sender_headers = auth_headers(sender["access_token"])
    sender_account = _open_account(client, sender_headers)
    client.post(
        "/api/payments/deposit",
        json={"account_number": sender_account["account_number"], "amount": "1000.00"},
        headers=sender_headers,
    )

    receiver = register_customer(client, email="julia@example.com")
    receiver_headers = auth_headers(receiver["access_token"])
    receiver_account = _open_account(client, receiver_headers)

    response = client.post(
        "/api/payments/transfer",
        json={
            "source_account_number": sender_account["account_number"],
            "target_account_number": receiver_account["account_number"],
            "amount": "300.00",
        },
        headers=sender_headers,
    )
    assert response.status_code == 200

    sender_balance = client.get(f"/api/accounts/{sender_account['account_number']}", headers=sender_headers).json()
    receiver_balance = client.get(f"/api/accounts/{receiver_account['account_number']}", headers=receiver_headers).json()
    assert sender_balance["balance"] == "700.00"
    assert receiver_balance["balance"] == "300.00"


def test_cannot_access_another_customers_account(client):
    owner = register_customer(client, email="ken@example.com")
    owner_headers = auth_headers(owner["access_token"])
    account = _open_account(client, owner_headers)

    intruder = register_customer(client, email="liam@example.com")
    intruder_headers = auth_headers(intruder["access_token"])

    response = client.get(f"/api/accounts/{account['account_number']}", headers=intruder_headers)
    assert response.status_code == 403


def test_transaction_history_records_deposit_and_withdrawal(client):
    data = register_customer(client, email="mona@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    client.post("/api/payments/deposit", json={"account_number": account["account_number"], "amount": "200.00"}, headers=headers)
    client.post("/api/payments/withdraw", json={"account_number": account["account_number"], "amount": "50.00"}, headers=headers)

    response = client.get(f"/api/payments/{account['account_number']}/transactions", headers=headers)
    assert response.status_code == 200
    types = [t["type"] for t in response.json()]
    assert types == ["WITHDRAWAL", "DEPOSIT"]
