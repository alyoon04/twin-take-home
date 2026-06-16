"""Records create: single/batch, validation, typecast, write scope (SPEC section 5)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}
RO = {"Authorization": f"Bearer {config.READONLY_PAT}"}


def _crm() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def _tracker() -> tuple[str, dict]:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "Project Tracker")
    tasks = next(t for t in base["tables"].values() if t["name"] == "Tasks")
    return base["id"], tasks


def test_create_single() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Name": "Linus Torvalds", "Active": True}})
    assert r.status_code == 200
    body = r.json()
    assert body["id"].startswith("rec") and "createdTime" in body
    assert body["fields"] == {"Name": "Linus Torvalds", "Active": True}
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 6


def test_create_batch() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H, json={"records": [
        {"fields": {"Name": "A"}}, {"fields": {"Name": "B"}},
    ]})
    assert r.status_code == 200
    assert [rec["fields"]["Name"] for rec in r.json()["records"]] == ["A", "B"]


def test_create_batch_over_10_is_422() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H,
                    json={"records": [{"fields": {"Name": str(i)}} for i in range(11)]})
    assert r.status_code == 422


def test_missing_fields_is_422() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H, json={})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "INVALID_REQUEST_MISSING_FIELDS"


def test_unknown_field_is_422() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Nope": "x"}})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "UNKNOWN_FIELD_NAME"


def test_write_requires_scope() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=RO, json={"fields": {"Name": "X"}})
    assert r.status_code == 403


def test_false_cells_dropped_on_write() -> None:
    base = _crm()
    r = client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Name": "X", "Active": False}})
    assert "Active" not in r.json()["fields"]


def test_single_select_invalid_option_without_typecast_422() -> None:
    base, _ = _tracker()
    r = client.post(f"/v0/{base}/Tasks", headers=H, json={"fields": {"Name": "T", "Status": "Blocked"}})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "INVALID_VALUE_FOR_COLUMN"


def test_single_select_typecast_creates_option() -> None:
    base, tasks = _tracker()
    r = client.post(f"/v0/{base}/Tasks", headers=H,
                    json={"fields": {"Name": "T", "Status": "Blocked"}, "typecast": True})
    assert r.status_code == 200
    assert r.json()["fields"]["Status"] == "Blocked"
    status = next(f for f in tasks["fields"] if f["name"] == "Status")
    assert "Blocked" in {c["name"] for c in status["options"]["choices"]}


def test_create_is_deterministic_across_reset() -> None:
    base = _crm()
    r1 = client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Name": "Z"}}).json()
    base2 = _crm()
    r2 = client.post(f"/v0/{base2}/Contacts", headers=H, json={"fields": {"Name": "Z"}}).json()
    assert r1["id"] == r2["id"] and r1["createdTime"] == r2["createdTime"]
