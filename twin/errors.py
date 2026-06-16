"""Error helpers.

S3: ported as-is from the starter (generic ``{"error": {"type", "message"}}``).
S6 replaces this with the real Airtable error model: the dual envelope
(object form and bare-string form), the documented status/type catalog, and
FastAPI exception handlers that override the default 422. See AIRTABLE_SPEC.md §4.
"""

from fastapi import HTTPException


def provider_error(status_code: int, error_type: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"error": {"type": error_type, "message": message}},
    )
