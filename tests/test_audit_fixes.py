"""Tests for the S25 audit-fix changes (see docs/AUDIT.md)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm() -> tuple[dict, dict]:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "CRM")
    contacts = next(t for t in base["tables"].values() if t["name"] == "Contacts")
    return base, contacts


def test_fix1_get_record_honors_return_fields_by_field_id() -> None:
    base, contacts = _crm()
    rid = next(iter(contacts["records"]))
    r = client.get(f"/v0/{base['id']}/Contacts/{rid}?returnFieldsByFieldId=true", headers=H)
    assert r.status_code == 200
    assert all(k.startswith("fld") for k in r.json()["fields"])


def test_fix2_create_over_10_message_is_verbatim() -> None:
    base, _ = _crm()
    r = client.post(f"/v0/{base['id']}/Contacts", headers=H,
                    json={"records": [{"fields": {"Name": str(i)}} for i in range(11)]})
    assert r.status_code == 422
    assert r.json()["error"]["message"] == "A maximum of 10 records can be created per request but you have provided 11."


def test_fix3_ascending_sort_places_blanks_first() -> None:
    base, _ = _crm()
    client.post(f"/v0/{base['id']}/Contacts", headers=H, json={"fields": {"Name": "No Company"}})
    r = client.get(f"/v0/{base['id']}/Contacts?sort[0][field]=Company&sort[0][direction]=asc", headers=H).json()
    assert "Company" not in r["records"][0]["fields"]  # blank sorts first


def test_fix4_whoami_omits_scopes_for_pat() -> None:
    store.reset_state()
    body = client.get("/v0/meta/whoami", headers=H).json()
    assert set(body) == {"id"}


def test_fix5_create_base_requires_workspace_id() -> None:
    store.reset_state()
    r = client.post("/v0/meta/bases", headers=H,
                    json={"name": "X", "tables": [{"name": "T", "fields": [{"name": "N", "type": "singleLineText"}]}]})
    assert r.status_code == 422


def test_fix6_comments_offset_null_on_last_page() -> None:
    base, contacts = _crm()
    rid = next(iter(contacts["records"]))
    r = client.get(f"/v0/{base['id']}/Contacts/{rid}/comments", headers=H).json()
    assert "offset" in r and r["offset"] is None


def test_fix7_cursor_for_next_payload_advances() -> None:
    base, _ = _crm()
    before = client.get(f"/v0/bases/{base['id']}/webhooks", headers=H).json()["webhooks"][0]["cursorForNextPayload"]
    client.post(f"/v0/{base['id']}/Contacts", headers=H, json={"fields": {"Name": "Cursor Test"}})
    after = client.get(f"/v0/bases/{base['id']}/webhooks", headers=H).json()["webhooks"][0]["cursorForNextPayload"]
    assert after == before + 1


def test_fix8_405_returns_airtable_envelope() -> None:
    r = client.put("/_arga/healthz")  # health is GET-only -> 405
    assert r.status_code == 405
    body = r.json()
    assert "detail" not in body and "error" in body


def test_fix9_enable_notifications() -> None:
    base, _ = _crm()
    wid = client.get(f"/v0/bases/{base['id']}/webhooks", headers=H).json()["webhooks"][0]["id"]
    r = client.post(f"/v0/bases/{base['id']}/webhooks/{wid}/enableNotifications", headers=H, json={"enable": False})
    assert r.status_code == 200
    w = client.get(f"/v0/bases/{base['id']}/webhooks", headers=H).json()["webhooks"][0]
    assert w["areNotificationsEnabled"] is False
