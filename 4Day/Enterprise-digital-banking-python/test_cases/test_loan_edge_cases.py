from test_cases.conftest import auth_headers, make_admin, register_customer


def _open_account(client, headers):
    response = client.post("/api/accounts", json={"account_type": "SAVINGS"}, headers=headers)
    assert response.status_code == 200
    return response.json()


def _apply_loan(client, headers, account_number, principal="60000", tenure=3):
    response = client.post(
        "/api/loans/apply",
        json={"account_number": account_number, "principal_amount": principal, "tenure_months": tenure},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_apply_loan_above_maximum_rejected(client):
    data = register_customer(client, email="bigloan@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "10000000", "tenure_months": 12},
        headers=headers,
    )
    assert response.status_code == 400


def test_apply_loan_with_tenure_exceeding_max_rejected(client):
    data = register_customer(client, email="longtenure@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "60000", "tenure_months": 500},
        headers=headers,
    )
    assert response.status_code == 400


def test_apply_loan_on_another_customers_account_rejected(client):
    owner = register_customer(client, email="loanowner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    account = _open_account(client, owner_headers)

    intruder = register_customer(client, email="loanintruder@example.com")
    intruder_headers = auth_headers(intruder["access_token"])

    response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "60000", "tenure_months": 6},
        headers=intruder_headers,
    )
    assert response.status_code == 403


def test_get_nonexistent_loan_returns_404(client):
    data = register_customer(client, email="loanlookup@example.com")
    headers = auth_headers(data["access_token"])

    response = client.get("/api/loans/999999", headers=headers)
    assert response.status_code == 404


def test_non_owner_cannot_view_loan_detail(client):
    owner = register_customer(client, email="loandetailowner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    account = _open_account(client, owner_headers)
    loan = _apply_loan(client, owner_headers, account["account_number"])

    intruder = register_customer(client, email="loandetailintruder@example.com")
    intruder_headers = auth_headers(intruder["access_token"])

    response = client.get(f"/api/loans/{loan['id']}", headers=intruder_headers)
    assert response.status_code == 403


def test_admin_can_view_any_loan_detail(client):
    owner = register_customer(client, email="loanadminowner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    account = _open_account(client, owner_headers)
    loan = _apply_loan(client, owner_headers, account["account_number"])

    admin = register_customer(client, email="loanadmin@example.com")
    make_admin("loanadmin@example.com")
    admin_headers = auth_headers(admin["access_token"])

    response = client.get(f"/api/loans/{loan['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == loan["id"]


def test_repay_installment_on_pending_loan_rejected(client):
    data = register_customer(client, email="pendingrepay@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)
    loan = _apply_loan(client, headers, account["account_number"])

    response = client.post(f"/api/loans/{loan['id']}/repay", headers=headers)
    assert response.status_code == 400


def test_approve_already_approved_loan_rejected(client):
    data = register_customer(client, email="doubleapprove@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)
    loan = _apply_loan(client, headers, account["account_number"])

    make_admin("doubleapprove@example.com")
    first = client.post(f"/api/loans/{loan['id']}/approve", headers=headers)
    assert first.status_code == 200

    second = client.post(f"/api/loans/{loan['id']}/approve", headers=headers)
    assert second.status_code == 400


def test_reject_already_rejected_loan_rejected(client):
    data = register_customer(client, email="doublereject@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)
    loan = _apply_loan(client, headers, account["account_number"])

    make_admin("doublereject@example.com")
    first = client.post(f"/api/loans/{loan['id']}/reject", headers=headers)
    assert first.status_code == 200

    second = client.post(f"/api/loans/{loan['id']}/reject", headers=headers)
    assert second.status_code == 400


def test_approve_nonexistent_loan_returns_404(client):
    data = register_customer(client, email="approveghost@example.com")
    make_admin("approveghost@example.com")
    headers = auth_headers(data["access_token"])

    response = client.post("/api/loans/999999/approve", headers=headers)
    assert response.status_code == 404
