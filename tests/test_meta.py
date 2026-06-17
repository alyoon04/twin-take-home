"""Meta API read: whoami, list bases, base schema (SPEC section 8)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def test_whoami() -> None:
    store.reset_state()
    r = client.get("/v0/meta/whoami", headers=H)
    assert r.status_code == 200
    assert r.json()["id"].startswith("usr")


def test_whoami_requires_auth() -> None:
    store.reset_state()
    assert client.get("/v0/meta/whoami").status_code == 401


def test_list_bases() -> None:
    store.reset_state()
    r = client.get("/v0/meta/bases", headers=H)
    assert r.status_code == 200
    bases = r.json()["bases"]
    assert {b["name"] for b in bases} == {"CRM", "Project Tracker"}
    assert all(set(b) == {"id", "name", "permissionLevel"} for b in bases)
    assert all(b["id"].startswith("app") for b in bases)


def test_base_schema() -> None:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "Project Tracker")
    r = client.get(f"/v0/meta/bases/{base['id']}/tables", headers=H)
    assert r.status_code == 200
    tables = r.json()["tables"]
    assert {t["name"] for t in tables} == {"Projects", "Tasks"}
    tasks = next(t for t in tables if t["name"] == "Tasks")
    assert tasks["id"].startswith("tbl") and tasks["primaryFieldId"].startswith("fld")
    status = next(f for f in tasks["fields"] if f["name"] == "Status")
    assert status["type"] == "singleSelect"
    assert all(c["id"].startswith("sel") for c in status["options"]["choices"])
    link = next(f for f in tasks["fields"] if f["name"] == "Project")
    assert link["type"] == "multipleRecordLinks"
    assert link["options"]["linkedTableId"].startswith("tbl")
    assert all(v["type"] == "grid" for v in tasks["views"])


def test_base_schema_unknown_base_is_403_model_not_found() -> None:
    # Verified live: the meta API returns 403 for a missing base (not a 404 like the data API).
    store.reset_state()
    r = client.get("/v0/meta/bases/appNope0000000000/tables", headers=H)
    assert r.status_code == 403
    assert r.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_base_schema_include_visible_field_ids() -> None:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "CRM")
    r = client.get(f"/v0/meta/bases/{base['id']}/tables?include[]=visibleFieldIds", headers=H)
    grid = r.json()["tables"][0]["views"][0]
    assert "visibleFieldIds" in grid
    assert all(fid.startswith("fld") for fid in grid["visibleFieldIds"])


def test_records_routes_still_resolve() -> None:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]
    r = client.get(f"/v0/{base}/Contacts", headers=H)
    assert r.status_code == 200 and len(r.json()["records"]) == 5
