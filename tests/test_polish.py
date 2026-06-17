"""Cross-cutting polish: X-Request-Id header, OpenAPI tags, error-envelope sweep (S20)."""

from fastapi.testclient import TestClient

from app import app
from twin import config, store

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def test_x_request_id_header_present_and_deterministic() -> None:
    store.reset_state()
    r1 = client.get("/_arga/healthz")
    rid1 = r1.headers.get("x-request-id")
    assert rid1 and rid1.startswith("req")
    store.reset_state()
    rid2 = client.get("/_arga/healthz").headers.get("x-request-id")
    assert rid1 == rid2  # same call sequence after reset -> same id


def test_error_envelopes_never_leak_fastapi_detail() -> None:
    base = _crm()
    responses = [
        client.get(f"/v0/{base}/Contacts"),                                 # 401 missing auth
        client.get(f"/v0/{base}/Contacts/recNope0000000000", headers=H),    # 404 record (bare string)
        client.get("/v0/nope/nope/nope/nope", headers=H),                   # 404 unmatched route
        client.get("/v0/meta/bases/appNope0000000000/tables", headers=H),   # 404 meta (object)
        client.post(f"/v0/{base}/Contacts", headers=H, json={"fields": {"Nope": 1}}),  # 422 unknown field
    ]
    for r in responses:
        body = r.json()
        assert "detail" not in body, body   # no leaked FastAPI shape
        assert "error" in body, body        # Airtable envelope


def test_openapi_exposes_tags() -> None:
    schema = client.get("/openapi.json").json()
    tag_names = {t["name"] for t in schema.get("tags", [])}
    assert {"control", "records", "meta", "comments", "webhooks"} <= tag_names
