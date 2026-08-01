from tests.conftest import auth_headers, register_customer


def test_register_and_login(client):
    data = register_customer(client, email="bob@example.com")
    assert data["customer"]["email"] == "bob@example.com"
    assert data["customer"]["role"] == "CUSTOMER"
    assert data["access_token"]

    response = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret123"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_rejected(client):
    register_customer(client, email="carol@example.com")
    response = client.post("/api/auth/login", json={"email": "carol@example.com", "password": "wrong-password"})
    assert response.status_code == 400


def test_duplicate_email_rejected(client):
    register_customer(client, email="dave@example.com")
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Dave Two", "email": "dave@example.com", "phone": "1112223333", "password": "secret123"},
    )
    assert response.status_code == 400


def test_get_me_requires_auth(client):
    response = client.get("/api/customers/me")
    assert response.status_code in (401, 403)


def test_get_and_update_my_profile(client):
    data = register_customer(client, email="erin@example.com")
    headers = auth_headers(data["access_token"])

    response = client.get("/api/customers/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "erin@example.com"

    response = client.put("/api/customers/me", json={"full_name": "Erin Updated"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Erin Updated"


def test_non_admin_cannot_list_customers(client):
    data = register_customer(client, email="frank@example.com")
    headers = auth_headers(data["access_token"])
    response = client.get("/api/customers", headers=headers)
    assert response.status_code == 403
