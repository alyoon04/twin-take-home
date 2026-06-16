"""Authentication.

S3: ported as-is from the starter (a single ``Bearer sk_test_twin_123`` check).
S7 replaces this with Airtable PAT auth: ``Authorization: Bearer pat...``,
distinguishing missing vs invalid vs insufficient-scope. See AIRTABLE_SPEC.md §2.
"""

from typing import Annotated

from fastapi import Header, status

from twin.errors import provider_error

VALID_AUTH_HEADER = "Bearer sk_test_twin_123"


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    if authorization != VALID_AUTH_HEADER:
        raise provider_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Invalid or missing API key.",
        )
