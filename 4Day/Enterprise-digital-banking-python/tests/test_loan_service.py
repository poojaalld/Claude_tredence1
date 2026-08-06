from decimal import Decimal

from app.loan_service.service import calculate_emi
from tests.conftest import auth_headers, make_admin, register_customer


def _open_account(client, headers):
    response = client.post("/api/accounts", json={"account_type": "SAVINGS"}, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_calculate_emi_matches_standard_formula():
    emi = calculate_emi(Decimal("100000"), Decimal("12"), 12)
    # Standard reducing-balance EMI for 100000 @ 12% APR over 12 months ~ 8884.88
    assert emi == Decimal("8884.88")


def test_calculate_emi_zero_interest_is_flat_split():
    emi = calculate_emi(Decimal("12000"), Decimal("0"), 12)
    assert emi == Decimal("1000.00")


def test_apply_amount_below_minimum_rejected(client):
    data = register_customer(client, email="nora@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "500", "tenure_months": 6},
        headers=headers,
    )
    assert response.status_code == 400


def test_non_admin_cannot_approve_loan(client):
    data = register_customer(client, email="oscar@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    apply_response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "60000", "tenure_months": 3},
        headers=headers,
    )
    assert apply_response.status_code == 200
    loan_id = apply_response.json()["id"]

    response = client.post(f"/api/loans/{loan_id}/approve", headers=headers)
    assert response.status_code == 403


def test_full_loan_lifecycle_apply_approve_repay_close(client):
    data = register_customer(client, email="petra@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    apply_response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "60000", "tenure_months": 3},
        headers=headers,
    )
    assert apply_response.status_code == 200
    loan = apply_response.json()
    assert loan["status"] == "PENDING"
    loan_id = loan["id"]

    make_admin("petra@example.com")
    approve_response = client.post(f"/api/loans/{loan_id}/approve", headers=headers)
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "ACTIVE"

    account_after_disbursement = client.get(f"/api/accounts/{account['account_number']}", headers=headers).json()
    assert account_after_disbursement["balance"] == "60000.00"

    # Top up so the account can also cover the interest portion of the EMIs,
    # not just the disbursed principal.
    client.post("/api/payments/deposit", json={"account_number": account["account_number"], "amount": "5000.00"}, headers=headers)

    for _ in range(3):
        repay_response = client.post(f"/api/loans/{loan_id}/repay", headers=headers)
        assert repay_response.status_code == 200

    final = repay_response.json()
    assert final["status"] == "CLOSED"
    assert all(i["status"] == "PAID" for i in final["installments"])

    over_repay_response = client.post(f"/api/loans/{loan_id}/repay", headers=headers)
    assert over_repay_response.status_code == 400


def test_admin_can_reject_pending_loan(client):
    data = register_customer(client, email="quinn@example.com")
    headers = auth_headers(data["access_token"])
    account = _open_account(client, headers)

    apply_response = client.post(
        "/api/loans/apply",
        json={"account_number": account["account_number"], "principal_amount": "20000", "tenure_months": 6},
        headers=headers,
    )
    loan_id = apply_response.json()["id"]

    make_admin("quinn@example.com")
    response = client.post(f"/api/loans/{loan_id}/reject", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
