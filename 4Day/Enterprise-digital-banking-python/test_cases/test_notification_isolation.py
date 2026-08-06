from test_cases.conftest import auth_headers, register_customer


def _open_account(client, headers):
    response = client.post("/api/accounts", json={"account_type": "SAVINGS"}, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_customer_only_sees_own_notifications(client):
    alice = register_customer(client, email="notifalice@example.com")
    alice_headers = auth_headers(alice["access_token"])
    _open_account(client, alice_headers)

    bob = register_customer(client, email="notifbob@example.com")
    bob_headers = auth_headers(bob["access_token"])
    _open_account(client, bob_headers)

    alice_notifications = client.get("/api/notifications", headers=alice_headers).json()
    bob_notifications = client.get("/api/notifications", headers=bob_headers).json()

    assert len(alice_notifications) >= 1
    assert len(bob_notifications) >= 1
    assert {n["id"] for n in alice_notifications}.isdisjoint({n["id"] for n in bob_notifications})


def test_transfer_generates_notification_for_both_sender_and_receiver(client):
    sender = register_customer(client, email="notifsender@example.com")
    sender_headers = auth_headers(sender["access_token"])
    sender_account = _open_account(client, sender_headers)
    client.post(
        "/api/payments/deposit",
        json={"account_number": sender_account["account_number"], "amount": "500.00"},
        headers=sender_headers,
    )

    receiver = register_customer(client, email="notifreceiver@example.com")
    receiver_headers = auth_headers(receiver["access_token"])
    receiver_account = _open_account(client, receiver_headers)

    client.post(
        "/api/payments/transfer",
        json={
            "source_account_number": sender_account["account_number"],
            "target_account_number": receiver_account["account_number"],
            "amount": "150.00",
        },
        headers=sender_headers,
    )

    sender_types = [n["type"] for n in client.get("/api/notifications", headers=sender_headers).json()]
    receiver_types = [n["type"] for n in client.get("/api/notifications", headers=receiver_headers).json()]

    assert "TRANSFER" in sender_types
    assert "TRANSFER" in receiver_types
