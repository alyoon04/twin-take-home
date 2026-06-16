"""Airtable error model: catalog bodies + exception handlers (SPEC section 4)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app import app as twin_app
from twin import errors


# --- catalog bodies (unit) ------------------------------------------------

def test_authentication_required() -> None:
    e = errors.authentication_required()
    assert e.status_code == 401
    assert e.body == {"error": {"type": "AUTHENTICATION_REQUIRED", "message": "Authentication required"}}


def test_not_found_object_form_has_no_message() -> None:
    e = errors.not_found()
    assert e.status_code == 404
    assert e.body == {"error": {"type": "NOT_FOUND"}}


def test_not_found_bare_string_form() -> None:
    assert errors.not_found(bare=True).body == {"error": "NOT_FOUND"}


def test_invalid_permissions_or_model_not_found_is_verbatim() -> None:
    e = errors.invalid_permissions_or_model_not_found()
    assert e.status_code == 403
    assert e.body["error"]["type"] == "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"
    assert e.body["error"]["message"].startswith("Invalid permissions, or the requested model was not found.")


def test_rate_limit_reached_is_singular_envelope_no_trailing_period() -> None:
    e = errors.rate_limit_reached()
    assert e.status_code == 429
    assert e.body == {
        "error": {"type": "RATE_LIMIT_REACHED", "message": "Rate limit exceeded. Please try again later"}
    }


def test_retriable_error_uses_corrected_503_message() -> None:
    e = errors.retriable_error()
    assert e.status_code == 503
    assert e.body["error"]["message"] == (
        "Server encountered an error while processing your request, and it is safe to retry the request"
    )


def test_unknown_field_name_interpolates() -> None:
    e = errors.unknown_field_name("Payment_Type")
    assert e.body["error"] == {"type": "UNKNOWN_FIELD_NAME", "message": "Could not find a field named Payment_Type"}


# --- handlers (integration) -----------------------------------------------

def _handler_client() -> TestClient:
    a = FastAPI()
    errors.register_handlers(a)

    class Body(BaseModel):
        name: str

    @a.get("/boom")
    def boom() -> dict:
        raise errors.not_found()

    @a.post("/needs-name")
    def needs_name(b: Body) -> dict:
        return {"ok": True}

    return TestClient(a)


def test_airtable_error_is_serialized_by_handler() -> None:
    r = _handler_client().get("/boom")
    assert r.status_code == 404
    assert r.json() == {"error": {"type": "NOT_FOUND"}}


def test_request_validation_is_airtable_shaped() -> None:
    r = _handler_client().post("/needs-name", json={})
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "INVALID_REQUEST_UNKNOWN"


def test_unknown_route_returns_airtable_not_found() -> None:
    r = TestClient(twin_app).get("/v0/this/does/not/exist")
    assert r.status_code == 404
    assert r.json() == {"error": "NOT_FOUND"}
