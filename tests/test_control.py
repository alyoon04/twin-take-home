"""Arga control endpoints: health, deterministic reset, OpenAPI."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/_arga/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reset_restores_seed_counts() -> None:
    reset = client.post("/_arga/admin/reset")
    state = client.get("/_arga/admin/state")
    assert reset.status_code == 200
    assert reset.json() == {"status": "reset"}
    counts = state.json()["counts"]
    assert counts["bases"] == 2
    assert counts["records"] == 13


def test_openapi_schema_is_served() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Airtable Web API Twin"
