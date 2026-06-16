"""Authentication (AIRTABLE_SPEC.md section 2).

Real Airtable PAT auth via ``Authorization: Bearer <token>``. Missing, malformed,
wrong-scheme (e.g. Basic), and unknown tokens are indistinguishable -> 401
``AUTHENTICATION_REQUIRED``. A recognized token lacking the required scope -> 403
``INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND``. ``get_token`` authenticates; the
``require_scope(scope)`` factory adds a scope gate.

``require_auth`` (legacy ``Bearer sk_test_twin_123``) remains only for the
temporary example router and is removed with it in S9.
"""

from typing import Annotated, Callable

from fastapi import Depends, Header, status

from twin import errors, store

VALID_AUTH_HEADER = "Bearer sk_test_twin_123"  # legacy: example router only
_BEARER_PREFIX = "Bearer "


def require_auth(authorization: Annotated[str | None, Header()] = None) -> None:
    """Legacy starter auth used by the temporary example router (removed in S9)."""
    if authorization != VALID_AUTH_HEADER:
        raise errors.provider_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Invalid or missing API key.",
        )


def get_token(authorization: Annotated[str | None, Header()] = None) -> dict:
    """Authenticate a Bearer token against the seeded tokens. 401 on any failure."""
    if not authorization or not authorization.startswith(_BEARER_PREFIX):
        raise errors.authentication_required()
    token = authorization[len(_BEARER_PREFIX):].strip()
    record = store.state.get("tokens", {}).get(token)
    if record is None:
        raise errors.authentication_required()
    return record


def require_scope(scope: str) -> Callable[..., dict]:
    """Dependency factory: authenticate, then require ``scope`` (403 if absent)."""

    def dependency(token: Annotated[dict, Depends(get_token)]) -> dict:
        if scope not in token.get("scopes", []):
            raise errors.invalid_permissions_or_model_not_found()
        return token

    return dependency
