from test_cases.conftest import auth_headers, register_customer


def _open_account(client, headers, account_type="SAVINGS"):
    response = client.post("/api/accounts", json={"account_type": account_type}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_deposit_zero_amount_rejected(client):
    data = register_customer(client, email="zero@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/payments/deposit",
        json={"account_number": account["account_number"], "amount": "0"},
        headers=headers,
    )
    assert response.status_code == 422


def test_deposit_negative_amount_rejected(client):
    data = register_customer(client, email="negative@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/payments/deposit",
        json={"account_number": account["account_number"], "amount": "-50"},
        headers=headers,
    )
    assert response.status_code == 422


def test_withdraw_negative_amount_rejected(client):
    data = register_customer(client, email="negwithdraw@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/payments/withdraw",
        json={"account_number": account["account_number"], "amount": "-10"},
        headers=headers,
    )
    assert response.status_code == 422


def test_transfer_to_same_account_rejected(client):
    data = register_customer(client, email="selftransfer@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)
    client.post("/api/payments/deposit", json={"account_number": account["account_number"], "amount": "100.00"}, headers=headers)

    response = client.post(
        "/api/payments/transfer",
        json={
            "source_account_number": account["account_number"],
            "target_account_number": account["account_number"],
            "amount": "10.00",
        },
        headers=headers,
    )
    assert response.status_code == 400


def test_transfer_to_nonexistent_account_rejected(client):
    data = register_customer(client, email="badtarget@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)
    client.post("/api/payments/deposit", json={"account_number": account["account_number"], "amount": "100.00"}, headers=headers)

    response = client.post(
        "/api/payments/transfer",
        json={
            "source_account_number": account["account_number"],
            "target_account_number": "ACCT0000000000",
            "amount": "10.00",
        },
        headers=headers,
    )
    assert response.status_code == 404


def test_deposit_to_nonexistent_account_rejected(client):
    data = register_customer(client, email="ghostaccount@example.com")
    headers = auth_headers(data["access_token"])

    response = client.post(
        "/api/payments/deposit",
        json={"account_number": "ACCT0000000000", "amount": "10.00"},
        headers=headers,
    )
    assert response.status_code == 404


def test_get_nonexistent_account_returns_404(client):
    data = register_customer(client, email="lookupmiss@example.com")
    headers = auth_headers(data["access_token"])

    response = client.get("/api/accounts/ACCT0000000000", headers=headers)
    assert response.status_code == 404


def test_transfer_source_not_owned_rejected(client):
    owner = register_customer(client, email="transferowner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    owner_account = _open_account(client, owner_headers)
    client.post("/api/payments/deposit", json={"account_number": owner_account["account_number"], "amount": "100.00"}, headers=owner_headers)

    other = register_customer(client, email="transferother@example.com")
    other_headers = auth_headers(other["access_token"])
    other_account = _open_account(client, other_headers)

    response = client.post(
        "/api/payments/transfer",
        json={
            "source_account_number": owner_account["account_number"],
            "target_account_number": other_account["account_number"],
            "amount": "10.00",
        },
        headers=other_headers,
    )
    assert response.status_code == 403
