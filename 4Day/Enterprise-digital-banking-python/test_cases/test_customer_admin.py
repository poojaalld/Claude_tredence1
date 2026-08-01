from test_cases.conftest import auth_headers, make_admin, register_customer


def test_admin_can_list_customers(client):
    data = register_customer(client, email="admin1@example.com")
    make_admin("admin1@example.com")
    headers = auth_headers(data["access_token"])

    register_customer(client, email="member1@example.com")

    response = client.get("/api/customers", headers=headers)
    assert response.status_code == 200
    emails = [c["email"] for c in response.json()]
    assert "admin1@example.com" in emails
    assert "member1@example.com" in emails


def test_admin_can_get_customer_by_id(client):
    admin_data = register_customer(client, email="admin2@example.com")
    make_admin("admin2@example.com")
    admin_headers = auth_headers(admin_data["access_token"])

    member_data = register_customer(client, email="member2@example.com")
    member_id = member_data["customer"]["id"]

    response = client.get(f"/api/customers/{member_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "member2@example.com"


def test_non_admin_cannot_get_other_customer_by_id(client):
    data = register_customer(client, email="member3@example.com")
    headers = auth_headers(data["access_token"])

    other_data = register_customer(client, email="member4@example.com")
    other_id = other_data["customer"]["id"]

    response = client.get(f"/api/customers/{other_id}", headers=headers)
    assert response.status_code == 403


def test_admin_get_nonexistent_customer_returns_404(client):
    data = register_customer(client, email="admin3@example.com")
    make_admin("admin3@example.com")
    headers = auth_headers(data["access_token"])

    response = client.get("/api/customers/999999", headers=headers)
    assert response.status_code == 404


def test_register_with_short_password_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Short Pw", "email": "shortpw@example.com", "phone": "1234567890", "password": "short"},
    )
    assert response.status_code == 422


def test_register_with_invalid_email_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Bad Email", "email": "not-an-email", "phone": "1234567890", "password": "secret123"},
    )
    assert response.status_code == 422


def test_update_profile_partial_update_keeps_other_fields(client):
    data = register_customer(client, email="partial@example.com", full_name="Original Name")
    headers = auth_headers(data["access_token"])

    response = client.put("/api/customers/me", json={"phone": "9998887777"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "9998887777"
    assert body["full_name"] == "Original Name"
