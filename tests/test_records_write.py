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


# --- update / upsert ---

def _contacts() -> tuple[str, dict]:
    base = _crm()
    contacts = next(t for t in store.state["bases"][base]["tables"].values() if t["name"] == "Contacts")
    return base, contacts


def test_patch_merges_partial() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    r = client.patch(f"/v0/{base}/Contacts/{rid}", headers=H, json={"fields": {"Company": "Updated Inc"}})
    assert r.status_code == 200
    fields = r.json()["fields"]
    assert fields["Company"] == "Updated Inc"
    assert fields["Name"] == "Ada Lovelace"  # untouched fields preserved


def test_put_clears_omitted() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    r = client.put(f"/v0/{base}/Contacts/{rid}", headers=H, json={"fields": {"Name": "Only Name"}})
    assert r.status_code == 200
    assert r.json()["fields"] == {"Name": "Only Name"}  # Email/Company/Active cleared


def test_patch_unknown_record_is_403_model_not_found() -> None:
    # Verified live: PATCH on a missing record → 403, not a bare 404.
    base = _crm()
    r = client.patch(f"/v0/{base}/Contacts/recNope0000000000", headers=H, json={"fields": {"Name": "X"}})
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_batch_patch_by_id() -> None:
    base, contacts = _contacts()
    rids = list(contacts["records"])[:2]
    r = client.patch(f"/v0/{base}/Contacts", headers=H, json={"records": [
        {"id": rids[0], "fields": {"Company": "C0"}},
        {"id": rids[1], "fields": {"Company": "C1"}},
    ]})
    assert r.status_code == 200
    assert [rec["fields"]["Company"] for rec in r.json()["records"]] == ["C0", "C1"]


def test_upsert_updates_existing() -> None:
    base = _crm()
    r = client.patch(f"/v0/{base}/Contacts", headers=H, json={
        "performUpsert": {"fieldsToMergeOn": ["Name"]},
        "records": [{"fields": {"Name": "Ada Lovelace", "Company": "Babbage Co"}}],
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["updatedRecords"]) == 1 and body["createdRecords"] == []
    assert body["records"][0]["fields"]["Company"] == "Babbage Co"
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 5  # no new record


def test_upsert_creates_when_no_match() -> None:
    base = _crm()
    r = client.patch(f"/v0/{base}/Contacts", headers=H, json={
        "performUpsert": {"fieldsToMergeOn": ["Name"]},
        "records": [{"fields": {"Name": "Brand New"}}],
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["createdRecords"]) == 1 and body["updatedRecords"] == []
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 6


def test_update_requires_write_scope() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    r = client.patch(f"/v0/{base}/Contacts/{rid}", headers=RO, json={"fields": {"Name": "X"}})
    assert r.status_code == 403


# --- delete ---

def test_delete_single() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    r = client.delete(f"/v0/{base}/Contacts/{rid}", headers=H)
    assert r.status_code == 200
    assert r.json() == {"deleted": True, "id": rid}
    assert client.get(f"/v0/{base}/Contacts/{rid}", headers=H).status_code == 403
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 4


def test_delete_batch() -> None:
    base, contacts = _contacts()
    rids = list(contacts["records"])[:2]
    r = client.delete(f"/v0/{base}/Contacts?records[]={rids[0]}&records[]={rids[1]}", headers=H)
    assert r.status_code == 200
    assert r.json() == {"records": [{"deleted": True, "id": rids[0]}, {"deleted": True, "id": rids[1]}]}
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 3


def test_delete_single_missing_is_403_model_not_found() -> None:
    # Verified live: SINGLE delete of a missing record → 403 (unlike batch delete, below).
    base = _crm()
    r = client.delete(f"/v0/{base}/Contacts/recNope0000000000", headers=H)
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_delete_batch_missing_is_404_not_found() -> None:
    # Verified live: BATCH delete of a missing id → 404 NOT_FOUND object form with message.
    base = _crm()
    r = client.delete(f"/v0/{base}/Contacts?records[]=recNope0000000000", headers=H)
    assert r.status_code == 404
    assert r.json() == {"error": {"type": "NOT_FOUND",
                                  "message": 'Could not find a record with ID "recNope0000000000".'}}


def test_batch_update_missing_id_is_422_row_does_not_exist() -> None:
    # Verified live: a missing id in a batch update → 422 ROW_DOES_NOT_EXIST.
    base = _crm()
    r = client.patch(f"/v0/{base}/Contacts", headers=H,
                     json={"records": [{"id": "recNope0000000000", "fields": {"Name": "X"}}]})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "ROW_DOES_NOT_EXIST"


def test_delete_requires_write_scope() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    assert client.delete(f"/v0/{base}/Contacts/{rid}", headers=RO).status_code == 403


def test_delete_then_reset_restores() -> None:
    base, contacts = _contacts()
    rid = next(iter(contacts["records"]))
    client.delete(f"/v0/{base}/Contacts/{rid}", headers=H)
    store.reset_state()
    assert len(client.get(f"/v0/{base}/Contacts", headers=H).json()["records"]) == 5
