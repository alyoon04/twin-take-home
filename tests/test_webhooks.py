"""Webhooks API + generated-event payloads (SPEC section 10)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}
RO = {"Authorization": f"Bearer {config.READONLY_PAT}"}


def _crm() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def _seed_hook(base: str) -> str:
    return client.get(f"/v0/bases/{base}/webhooks", headers=H).json()["webhooks"][0]["id"]


def test_list_seeded_webhook() -> None:
    base = _crm()
    hooks = client.get(f"/v0/bases/{base}/webhooks", headers=H).json()["webhooks"]
    assert len(hooks) == 1
    w = hooks[0]
    assert w["id"].startswith("ach") and w["isHookEnabled"] is True
    assert "macSecretBase64" not in w  # secret only returned on creation


def test_create_webhook() -> None:
    base = _crm()
    r = client.post(f"/v0/bases/{base}/webhooks", headers=H, json={
        "notificationUrl": "https://x.test/hook",
        "specification": {"options": {"filters": {"dataTypes": ["tableData"]}}},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["id"].startswith("ach") and body["macSecretBase64"]
    assert body["expirationTime"] == config.WEBHOOK_EXPIRATION
    assert len(client.get(f"/v0/bases/{base}/webhooks", headers=H).json()["webhooks"]) == 2


def test_create_webhook_requires_data_types() -> None:
    base = _crm()
    r = client.post(f"/v0/bases/{base}/webhooks", headers=H, json={"specification": {"options": {"filters": {}}}})
    assert r.status_code == 422


def test_delete_webhook() -> None:
    base = _crm()
    wid = _seed_hook(base)
    assert client.delete(f"/v0/bases/{base}/webhooks/{wid}", headers=H).status_code == 200
    assert client.get(f"/v0/bases/{base}/webhooks", headers=H).json()["webhooks"] == []


def test_refresh_webhook() -> None:
    base = _crm()
    wid = _seed_hook(base)
    r = client.post(f"/v0/bases/{base}/webhooks/{wid}/refresh", headers=H)
    assert r.status_code == 200 and r.json()["expirationTime"] == config.WEBHOOK_EXPIRATION_REFRESHED


def test_webhook_manage_requires_scope() -> None:
    base = _crm()
    assert client.get(f"/v0/bases/{base}/webhooks", headers=RO).status_code == 403


def test_create_record_generates_payload() -> None:
    base = _crm()
    wid = _seed_hook(base)
    assert client.get(f"/v0/bases/{base}/webhooks/{wid}/payloads", headers=H).json()["payloads"] == []
    new = client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Name": "Hooked"}}).json()
    payloads = client.get(f"/v0/bases/{base}/webhooks/{wid}/payloads", headers=H).json()["payloads"]
    assert len(payloads) == 1
    p = payloads[0]
    assert p["payloadFormat"] == "v0" and p["baseTransactionNumber"] == 1
    created = next(iter(p["changedTablesById"].values()))["createdRecordsById"]
    assert new["id"] in created


def test_delete_record_generates_destroy_payload() -> None:
    base = _crm()
    wid = _seed_hook(base)
    contacts = next(t for t in store.state["bases"][base]["tables"].values() if t["name"] == "Contacts")
    rid = next(iter(contacts["records"]))
    client.delete(f"/v0/{base}/Contacts/{rid}", headers=H)
    payloads = client.get(f"/v0/bases/{base}/webhooks/{wid}/payloads", headers=H).json()["payloads"]
    assert rid in next(iter(payloads[0]["changedTablesById"].values()))["destroyedRecordIds"]


def test_payloads_readable_with_records_read_scope() -> None:
    base = _crm()
    wid = _seed_hook(base)
    assert client.get(f"/v0/bases/{base}/webhooks/{wid}/payloads", headers=RO).status_code == 200


def test_records_routes_still_resolve() -> None:
    base = _crm()
    r = client.get(f"/v0/{base}/Contacts", headers=H)
    assert r.status_code == 200 and len(r.json()["records"]) == 5
