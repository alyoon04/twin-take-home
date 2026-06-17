"""Deterministic, opt-in per-base rate limiting (SPEC section 11)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def test_disabled_by_default() -> None:
    base = _crm()
    for _ in range(20):
        assert client.get(f"/v0/{base}/Contacts", headers=H).status_code == 200


def test_enabled_trips_429_after_threshold() -> None:
    base = _crm()
    client.post("/_arga/admin/rate-limit", json={"enabled": True, "perBase": 5})
    statuses = [client.get(f"/v0/{base}/Contacts", headers=H).status_code for _ in range(6)]
    assert statuses == [200, 200, 200, 200, 200, 429]
    body = client.get(f"/v0/{base}/Contacts", headers=H).json()
    assert body == {
        "error": {"type": "RATE_LIMIT_REACHED", "message": "Rate limit exceeded. Please try again later"}
    }


def test_reset_clears_and_disables_limiter() -> None:
    base = _crm()
    client.post("/_arga/admin/rate-limit", json={"enabled": True, "perBase": 2})
    for _ in range(3):
        client.get(f"/v0/{base}/Contacts", headers=H)  # trips the limiter
    client.post("/_arga/admin/reset")
    assert client.get(f"/v0/{base}/Contacts", headers=H).status_code == 200


def test_limit_is_per_base() -> None:
    base = _crm()
    tracker = next(b for b in store.state["bases"].values() if b["name"] == "Project Tracker")["id"]
    client.post("/_arga/admin/rate-limit", json={"enabled": True, "perBase": 3})
    for _ in range(4):
        client.get(f"/v0/{base}/Contacts", headers=H)  # trips CRM only
    assert client.get(f"/v0/{base}/Contacts", headers=H).status_code == 429
    assert client.get(f"/v0/{tracker}/Tasks", headers=H).status_code == 200
