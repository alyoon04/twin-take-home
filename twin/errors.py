"""Airtable-shaped error model (AIRTABLE_SPEC.md section 4).

Two envelope forms coexist in the real API and both are reproduced here:
  - object form:      {"error": {"type": "...", "message": "..."}}
  - bare-string form: {"error": "NOT_FOUND"}

``AirtableError`` carries an HTTP status + the exact body to serialize. The
constructors below cover the documented catalog with verbatim messages copied
from the spec (where a verifier note corrected the draft — e.g. the 503 body —
the corrected string is used). ``register_handlers(app)`` wires the handlers:
custom errors, the 422 validation override, and unmatched-route 404s.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AirtableError(Exception):
    """An error whose JSON body mirrors a real Airtable response."""

    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        super().__init__(str(body.get("error")))
        self.status_code = status_code
        self.body = body


# --- envelope builders ----------------------------------------------------

def error_object(status_code: int, type_: str, message: str | None = None) -> AirtableError:
    """Object-form error. Omits ``message`` when None (e.g. the 404 NOT_FOUND form)."""
    err: dict[str, Any] = {"type": type_}
    if message is not None:
        err["message"] = message
    return AirtableError(status_code, {"error": err})


def error_string(status_code: int, value: str) -> AirtableError:
    """Bare-string-form error, e.g. ``{"error": "NOT_FOUND"}``."""
    return AirtableError(status_code, {"error": value})


# --- catalog (verbatim per AIRTABLE_SPEC.md section 4) --------------------

def authentication_required() -> AirtableError:
    """401 — identical body for missing, malformed, and invalid tokens."""
    return error_object(
        status.HTTP_401_UNAUTHORIZED,
        "AUTHENTICATION_REQUIRED",
        "Authentication required",
    )


def invalid_permissions_or_model_not_found() -> AirtableError:
    """403 — authenticated but lacking scope/permission, or the model is hidden."""
    return error_object(
        status.HTTP_403_FORBIDDEN,
        "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND",
        "Invalid permissions, or the requested model was not found. Check that both your "
        "user and your token have the required permissions, and that the model names and/or "
        "ids are correct.",
    )


def invalid_permissions(message: str = "You are not permitted to perform this operation") -> AirtableError:
    """403 — operation-specific permission failure (message varies)."""
    return error_object(status.HTTP_403_FORBIDDEN, "INVALID_PERMISSIONS", message)


def not_found(bare: bool = False) -> AirtableError:
    """404 — both forms are official; default is the object form with no message."""
    if bare:
        return error_string(status.HTTP_404_NOT_FOUND, "NOT_FOUND")
    return error_object(status.HTTP_404_NOT_FOUND, "NOT_FOUND")


def invalid_request(
    message: str = "Invalid request: parameter validation failed. Check your request data.",
) -> AirtableError:
    """422 — generic validation failure (the only officially enumerated 422 type)."""
    return error_object(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_REQUEST_UNKNOWN", message)


def invalid_request_missing_fields(
    message: str = 'Could not find field "fields" in the request body',
) -> AirtableError:
    """422 — top-level ``fields`` object missing from the body."""
    return error_object(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_REQUEST_MISSING_FIELDS", message)


def unknown_field_name(field_name: str) -> AirtableError:
    """422 — a referenced field does not exist on the table."""
    return error_object(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "UNKNOWN_FIELD_NAME",
        f"Could not find a field named {field_name}",
    )


def invalid_value_for_column(message: str) -> AirtableError:
    """422 — value not valid for the field's type."""
    return error_object(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_VALUE_FOR_COLUMN", message)


def failed_state_check(
    message: str = "values and/or parameters in the endpoint path have been mismatched",
) -> AirtableError:
    """422 — path params/values mismatched."""
    return error_object(status.HTTP_422_UNPROCESSABLE_ENTITY, "FAILED_STATE_CHECK", message)


def list_records_iterator_not_available() -> AirtableError:
    """422 — stale/unknown list-records pagination offset (offset is time-windowed)."""
    return error_object(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "LIST_RECORDS_ITERATOR_NOT_AVAILABLE",
        "The list records iterator is no longer available. Restart pagination without an offset.",
    )


def invalid_filter_by_formula(
    message: str = "The formula for filtering records is invalid. Please check your formula text.",
) -> AirtableError:
    """422 — malformed filterByFormula (or an unknown field referenced in it)."""
    return error_object(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_FILTER_BY_FORMULA", message)


def record_not_found() -> AirtableError:
    """404 — a referenced record id does not exist (delete / single-record write); object form."""
    return error_object(status.HTTP_404_NOT_FOUND, "MODEL_ID_NOT_FOUND", "Record not found")


def row_does_not_exist(record_id: str) -> AirtableError:
    """422 — a batch update/upsert referenced a non-existent record id."""
    return error_object(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "ROW_DOES_NOT_EXIST",
        f"Record ID {record_id} does not exist in this table",
    )


def rate_limit_reached() -> AirtableError:
    """429 — singular envelope (NOT a plural array); message has no trailing period."""
    return error_object(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "RATE_LIMIT_REACHED",
        "Rate limit exceeded. Please try again later",
    )


def retriable_error() -> AirtableError:
    """503 — message per the verifier correction (the section draft's was wrong)."""
    return error_object(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "RETRIABLE_ERROR",
        "Server encountered an error while processing your request, and it is safe to retry the request",
    )


# --- handlers -------------------------------------------------------------

def register_handlers(app: FastAPI) -> None:
    """Install the exception handlers so every error comes out Airtable-shaped."""

    @app.exception_handler(AirtableError)
    async def _airtable_error(request: Request, exc: AirtableError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.body)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI/pydantic body validation -> Airtable's generic 422.
        err = invalid_request()
        return JSONResponse(status_code=err.status_code, content=err.body)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Unmatched routes (and other bare 404s) -> Airtable NOT_FOUND; otherwise
        # preserve the default {"detail": ...} shape (the temporary example router
        # still relies on it until S9).
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            err = not_found(bare=True)  # data-API 404s use the bare-string form
            return JSONResponse(status_code=err.status_code, content=err.body)
        # Any other framework error (e.g. 405) -> Airtable object envelope, never {"detail": ...}.
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"type": detail.upper().replace(" ", "_"), "message": detail}},
            headers=getattr(exc, "headers", None),
        )
