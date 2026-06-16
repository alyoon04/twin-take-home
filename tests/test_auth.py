"""Real PAT auth: valid / missing / invalid / wrong-scheme / scope (SPEC section 2)."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from twin import auth, config, errors, store


def _client() -> TestClient:
    store.reset_state()
    app = FastAPI()
    errors.register_handlers(app)

    @app.get("/read")
    def read(token: Annotated[dict, Depends(auth.get_token)]) -> dict:
        return {"userId": token["userId"]}

    @app.post("/write")
    def write(token: Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_WRITE))]) -> dict:
        return {"ok": True}

    return TestClient(app)


def _h(pat: str) -> dict:
    return {"Authorization": f"Bearer {pat}"}


def test_valid_pat_authenticates() -> None:
    r = _client().get("/read", headers=_h(config.VALID_PAT))
    assert r.status_code == 200
    assert r.json()["userId"].startswith("usr")


def test_missing_auth_is_401_authentication_required() -> None:
    r = _client().get("/read")
    assert r.status_code == 401
    assert r.json() == {"error": {"type": "AUTHENTICATION_REQUIRED", "message": "Authentication required"}}


def test_unknown_token_is_401_identical_to_missing() -> None:
    r = _client().get("/read", headers=_h(config.INVALID_PAT_EXAMPLE))
    assert r.status_code == 401
    assert r.json()["error"]["type"] == "AUTHENTICATION_REQUIRED"


def test_basic_scheme_is_rejected_401() -> None:
    r = _client().get("/read", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert r.status_code == 401


def test_write_scope_enforced() -> None:
    c = _client()
    assert c.post("/write", headers=_h(config.VALID_PAT)).status_code == 200
    forbidden = c.post("/write", headers=_h(config.READONLY_PAT))
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"


def test_readonly_token_can_read() -> None:
    r = _client().get("/read", headers=_h(config.READONLY_PAT))
    assert r.status_code == 200
