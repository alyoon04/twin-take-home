"""Records list query: pagination, projection, sort, offset, POST variant (SPEC section 6)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm_base() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def test_pagesize_paginates_with_offset() -> None:
    base = _crm_base()
    r1 = client.get(f"/v0/{base}/Contacts?pageSize=2", headers=H).json()
    assert len(r1["records"]) == 2 and "offset" in r1
    r2 = client.get(f"/v0/{base}/Contacts?pageSize=2&offset={r1['offset']}", headers=H).json()
    assert len(r2["records"]) == 2 and "offset" in r2
    r3 = client.get(f"/v0/{base}/Contacts?pageSize=2&offset={r2['offset']}", headers=H).json()
    assert len(r3["records"]) == 1 and "offset" not in r3
    ids = [rec["id"] for rec in r1["records"] + r2["records"] + r3["records"]]
    assert len(ids) == len(set(ids)) == 5  # full coverage, no overlap


def test_max_records_caps_total() -> None:
    base = _crm_base()
    r1 = client.get(f"/v0/{base}/Contacts?maxRecords=3&pageSize=2", headers=H).json()
    assert len(r1["records"]) == 2 and "offset" in r1
    r2 = client.get(f"/v0/{base}/Contacts?maxRecords=3&pageSize=2&offset={r1['offset']}", headers=H).json()
    assert len(r2["records"]) == 1 and "offset" not in r2  # capped at 3 total


def test_fields_projection() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?fields[]=Name", headers=H).json()
    assert all(set(rec["fields"]) <= {"Name"} for rec in r["records"])


def test_sort_desc() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?sort[0][field]=Name&sort[0][direction]=desc", headers=H).json()
    names = [rec["fields"]["Name"] for rec in r["records"]]
    assert names == sorted(names, reverse=True)


def test_return_fields_by_field_id() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?returnFieldsByFieldId=true&pageSize=1", headers=H).json()
    assert all(k.startswith("fld") for k in r["records"][0]["fields"])


def test_pagesize_over_100_is_422() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?pageSize=101", headers=H)
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "INVALID_REQUEST_UNKNOWN"


def test_stale_offset_is_422_iterator() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?offset=itr999/recZZZZZZZZZZZZZ", headers=H)
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "LIST_RECORDS_ITERATOR_NOT_AVAILABLE"


def test_garbage_offset_is_422_iterator() -> None:
    base = _crm_base()
    r = client.get(f"/v0/{base}/Contacts?offset=garbage", headers=H)
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "LIST_RECORDS_ITERATOR_NOT_AVAILABLE"


def test_offset_is_deterministic_across_reset() -> None:
    base = _crm_base()
    o1 = client.get(f"/v0/{base}/Contacts?pageSize=2", headers=H).json()["offset"]
    base2 = _crm_base()
    o2 = client.get(f"/v0/{base2}/Contacts?pageSize=2", headers=H).json()["offset"]
    assert o1 == o2


def test_post_list_records_matches_get() -> None:
    base = _crm_base()
    r = client.post(f"/v0/{base}/Contacts/listRecords", headers=H, json={"pageSize": 2}).json()
    assert len(r["records"]) == 2 and "offset" in r
