"""Records API — read: list, get, table-by-id/name, 404s, auth (SPEC sections 5-6)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm() -> tuple[dict, dict]:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "CRM")
    table = next(t for t in base["tables"].values() if t["name"] == "Contacts")
    return base, table


def test_list_records_by_table_name() -> None:
    base, _ = _crm()
    r = client.get(f"/v0/{base['id']}/Contacts", headers=H)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"records"}
    assert len(data["records"]) == 5
    first = data["records"][0]
    assert set(first) == {"id", "createdTime", "fields"}
    assert first["id"].startswith("rec")


def test_list_records_by_table_id() -> None:
    base, table = _crm()
    r = client.get(f"/v0/{base['id']}/{table['id']}", headers=H)
    assert r.status_code == 200
    assert len(r.json()["records"]) == 5


def test_get_single_record() -> None:
    base, table = _crm()
    rec_id = next(iter(table["records"]))
    r = client.get(f"/v0/{base['id']}/{table['id']}/{rec_id}", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == rec_id
    assert "createdTime" in body and "fields" in body


def test_unknown_record_is_403_model_not_found() -> None:
    # Verified live: a missing record under a valid base+table → 403, not a bare 404.
    base, table = _crm()
    r = client.get(f"/v0/{base['id']}/{table['id']}/recDoesNotExist00", headers=H)
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_unknown_base_is_404() -> None:
    # Verified live: a missing base (routing root) stays a bare 404.
    _crm()
    r = client.get("/v0/appNope0000000000/Contacts", headers=H)
    assert r.status_code == 404
    assert r.json() == {"error": "NOT_FOUND"}


def test_unknown_table_is_403_model_not_found() -> None:
    # Verified live: a missing table under a valid base → 403, not a bare 404.
    base, _ = _crm()
    r = client.get(f"/v0/{base['id']}/NoSuchTable", headers=H)
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_list_requires_auth() -> None:
    base, _ = _crm()
    r = client.get(f"/v0/{base['id']}/Contacts")
    assert r.status_code == 401
    assert r.json()["error"]["type"] == "AUTHENTICATION_REQUIRED"


def test_list_rejects_invalid_token() -> None:
    base, _ = _crm()
    r = client.get(f"/v0/{base['id']}/Contacts", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_readonly_token_can_read() -> None:
    base, _ = _crm()
    r = client.get(f"/v0/{base['id']}/Contacts", headers={"Authorization": f"Bearer {config.READONLY_PAT}"})
    assert r.status_code == 200
