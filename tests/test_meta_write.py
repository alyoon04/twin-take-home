"""Meta API writes: create base/table/field, update table/field, scope (SPEC 8.5-8.7)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}
RO = {"Authorization": f"Bearer {config.READONLY_PAT}"}

BASE_BODY = {
    "name": "Inventory",
    "workspaceId": "wspTwinTest000001",
    "tables": [{
        "name": "Items",
        "fields": [
            {"name": "Name", "type": "singleLineText"},
            {"name": "Qty", "type": "number", "options": {"precision": 0}},
        ],
    }],
}


def _crm() -> dict:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")


def test_create_base() -> None:
    store.reset_state()
    r = client.post("/v0/meta/bases", headers=H, json=BASE_BODY)
    assert r.status_code == 200
    body = r.json()
    assert body["id"].startswith("app")
    table = body["tables"][0]
    assert table["id"].startswith("tbl")
    assert table["primaryFieldId"] == table["fields"][0]["id"]
    assert table["views"][0]["type"] == "grid"
    assert "Inventory" in {b["name"] for b in client.get("/v0/meta/bases", headers=H).json()["bases"]}
    schema = client.get(f"/v0/meta/bases/{body['id']}/tables", headers=H).json()
    assert schema["tables"][0]["name"] == "Items"


def test_create_table() -> None:
    base = _crm()["id"]
    r = client.post(f"/v0/meta/bases/{base}/tables", headers=H,
                    json={"name": "Deals", "fields": [{"name": "Title", "type": "singleLineText"}]})
    assert r.status_code == 200 and r.json()["name"] == "Deals"
    names = {t["name"] for t in client.get(f"/v0/meta/bases/{base}/tables", headers=H).json()["tables"]}
    assert names == {"Contacts", "Deals"}


def test_update_table() -> None:
    base = _crm()
    tid = next(iter(base["tables"]))
    r = client.patch(f"/v0/meta/bases/{base['id']}/tables/{tid}", headers=H, json={"name": "People"})
    assert r.status_code == 200 and r.json()["name"] == "People"


def test_create_field_appears_in_schema() -> None:
    base = _crm()
    tid = next(iter(base["tables"]))
    r = client.post(f"/v0/meta/bases/{base['id']}/tables/{tid}/fields", headers=H,
                    json={"name": "Phone", "type": "phoneNumber"})
    assert r.status_code == 200
    assert r.json()["id"].startswith("fld") and r.json()["type"] == "phoneNumber"
    schema = client.get(f"/v0/meta/bases/{base['id']}/tables", headers=H).json()
    table = next(t for t in schema["tables"] if t["id"] == tid)
    assert "Phone" in {f["name"] for f in table["fields"]}


def test_update_field_name_but_not_type() -> None:
    base = _crm()
    table = next(iter(base["tables"].values()))
    fid = table["fields"][1]["id"]  # Email
    ok = client.patch(f"/v0/meta/bases/{base['id']}/tables/{table['id']}/fields/{fid}", headers=H,
                      json={"name": "Email Address"})
    assert ok.status_code == 200 and ok.json()["name"] == "Email Address"
    bad = client.patch(f"/v0/meta/bases/{base['id']}/tables/{table['id']}/fields/{fid}", headers=H,
                       json={"type": "number"})
    assert bad.status_code == 422


def test_meta_write_requires_schema_write_scope() -> None:
    store.reset_state()
    assert client.post("/v0/meta/bases", headers=RO, json=BASE_BODY).status_code == 403


def test_create_base_missing_tables_is_422() -> None:
    store.reset_state()
    assert client.post("/v0/meta/bases", headers=H, json={"name": "X", "workspaceId": "wsp1"}).status_code == 422


def test_meta_writes_are_deterministic() -> None:
    store.reset_state()
    id1 = client.post("/v0/meta/bases", headers=H, json=BASE_BODY).json()["id"]
    store.reset_state()
    id2 = client.post("/v0/meta/bases", headers=H, json=BASE_BODY).json()["id"]
    assert id1 == id2
