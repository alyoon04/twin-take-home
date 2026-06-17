"""Record comments: list/create/update/delete + commentCount (SPEC section 9)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}
RO = {"Authorization": f"Bearer {config.READONLY_PAT}"}


def _first_contact() -> tuple[str, str]:
    store.reset_state()
    base = next(b for b in store.state["bases"].values() if b["name"] == "CRM")
    contacts = next(t for t in base["tables"].values() if t["name"] == "Contacts")
    rec = next(iter(contacts["records"].values()))
    return base["id"], rec["id"]


def test_list_seeded_comments() -> None:
    base, rid = _first_contact()
    r = client.get(f"/v0/{base}/Contacts/{rid}/comments", headers=H)
    assert r.status_code == 200
    comments = r.json()["comments"]
    assert len(comments) == 2
    c = comments[0]
    assert c["id"].startswith("com")
    assert set(c) >= {"id", "author", "text", "createdTime", "lastUpdatedTime"}
    assert c["lastUpdatedTime"] is None
    assert c["author"]["id"].startswith("usr")


def test_create_comment() -> None:
    base, rid = _first_contact()
    r = client.post(f"/v0/{base}/Contacts/{rid}/comments", headers=H, json={"text": "New comment"})
    assert r.status_code == 200
    assert r.json()["text"] == "New comment" and r.json()["id"].startswith("com")
    assert len(client.get(f"/v0/{base}/Contacts/{rid}/comments", headers=H).json()["comments"]) == 3


def test_create_comment_requires_text() -> None:
    base, rid = _first_contact()
    assert client.post(f"/v0/{base}/Contacts/{rid}/comments", headers=H, json={}).status_code == 422


def test_update_comment_sets_last_updated() -> None:
    base, rid = _first_contact()
    cid = client.get(f"/v0/{base}/Contacts/{rid}/comments", headers=H).json()["comments"][0]["id"]
    r = client.patch(f"/v0/{base}/Contacts/{rid}/comments/{cid}", headers=H, json={"text": "Edited"})
    assert r.status_code == 200
    assert r.json()["text"] == "Edited" and r.json()["lastUpdatedTime"] is not None


def test_delete_comment() -> None:
    base, rid = _first_contact()
    cid = client.get(f"/v0/{base}/Contacts/{rid}/comments", headers=H).json()["comments"][0]["id"]
    r = client.delete(f"/v0/{base}/Contacts/{rid}/comments/{cid}", headers=H)
    assert r.json() == {"id": cid, "deleted": True}
    assert len(client.get(f"/v0/{base}/Contacts/{rid}/comments", headers=H).json()["comments"]) == 1


def test_comment_write_requires_scope() -> None:
    base, rid = _first_contact()
    assert client.post(f"/v0/{base}/Contacts/{rid}/comments", headers=RO, json={"text": "x"}).status_code == 403


def test_comments_on_unknown_record_is_404() -> None:
    base, _ = _first_contact()
    assert client.get(f"/v0/{base}/Contacts/recNope0000000000/comments", headers=H).status_code == 404


def test_record_metadata_comment_count() -> None:
    base, rid = _first_contact()
    r = client.get(f"/v0/{base}/Contacts?recordMetadata[]=commentCount", headers=H).json()
    by_id = {rec["id"]: rec for rec in r["records"]}
    assert by_id[rid]["commentCount"] == 2
    others = [rec for rid2, rec in by_id.items() if rid2 != rid]
    assert others[0]["commentCount"] == 0
