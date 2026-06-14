from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/_arga/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reset_restores_seed_state() -> None:
    client.post(
        "/v1/example-resources",
        headers={"Authorization": "Bearer sk_test_twin_123"},
        json={"name": "Temporary resource"},
    )

    reset_response = client.post("/_arga/admin/reset")
    state_response = client.get("/_arga/admin/state")

    assert reset_response.status_code == 200
    assert state_response.json()["example_resources"] == [
        {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
    ]


def test_invalid_auth_is_rejected() -> None:
    response = client.get(
        "/v1/example-resources",
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error"]["type"] == "authentication_error"


def test_valid_auth_can_list_seeded_resources() -> None:
    response = client.get(
        "/v1/example-resources",
        headers={"Authorization": "Bearer sk_test_twin_123"},
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "res_twin_001"
