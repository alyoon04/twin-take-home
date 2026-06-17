"""Webhooks API (AIRTABLE_SPEC.md section 10). Rooted at /v0/bases/{baseId}/webhooks.

The payloads endpoint is the 'generated events' stream — record mutations append
payloads via twin.events. Registered before the records router (its `/v0/bases/...`
paths would otherwise be matched by `/v0/{baseId}/{table}`).
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from twin import auth, config, errors, ids, store

router = APIRouter(tags=["webhooks"])

ManageScope = Annotated[dict, Depends(auth.require_scope(config.SCOPE_WEBHOOK_MANAGE))]
PayloadScope = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_READ))]


def _base(base_id: str) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found()
    return base


def _webhook(base_id: str, webhook_id: str) -> dict:
    webhook = _base(base_id).get("webhooks", {}).get(webhook_id)
    if webhook is None:
        raise errors.not_found()
    return webhook


def _public(w: dict) -> dict:
    return {
        "id": w["id"],
        "specification": w["specification"],
        "notificationUrl": w["notificationUrl"],
        "cursorForNextPayload": w["cursorForNextPayload"],
        "isHookEnabled": w["isHookEnabled"],
        "areNotificationsEnabled": w["areNotificationsEnabled"],
        "expirationTime": w["expirationTime"],
        "lastSuccessfulNotificationTime": w["lastSuccessfulNotificationTime"],
        "lastNotificationResult": w["lastNotificationResult"],
    }


def _parse_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise errors.invalid_request()


@router.post("/v0/bases/{base_id}/webhooks")
def create_webhook(base_id: str, _: ManageScope, body: Annotated[dict, Body()]) -> dict:
    base = _base(base_id)
    spec = body.get("specification")
    filters = spec.get("options", {}).get("filters") if isinstance(spec, dict) else None
    if not isinstance(filters, dict) or not filters.get("dataTypes"):
        raise errors.invalid_request()
    wid = ids.webhook_id()
    base.setdefault("webhooks", {})[wid] = {
        "id": wid,
        "specification": spec,
        "notificationUrl": body.get("notificationUrl"),
        "isHookEnabled": True,
        "areNotificationsEnabled": bool(body.get("notificationUrl")),
        "cursorForNextPayload": 1,
        "expirationTime": config.WEBHOOK_EXPIRATION,
        "lastSuccessfulNotificationTime": None,
        "lastNotificationResult": None,
        "payloads": [],
        "macSecretBase64": ids.webhook_mac(wid),
    }
    return {"id": wid, "macSecretBase64": ids.webhook_mac(wid), "expirationTime": config.WEBHOOK_EXPIRATION}


@router.get("/v0/bases/{base_id}/webhooks")
def list_webhooks(base_id: str, _: ManageScope) -> dict:
    base = _base(base_id)
    return {"webhooks": [_public(w) for w in base.get("webhooks", {}).values()]}


@router.delete("/v0/bases/{base_id}/webhooks/{webhook_id}")
def delete_webhook(base_id: str, webhook_id: str, _: ManageScope) -> dict:
    base = _base(base_id)
    if webhook_id not in base.get("webhooks", {}):
        raise errors.not_found()
    del base["webhooks"][webhook_id]
    return {}


@router.post("/v0/bases/{base_id}/webhooks/{webhook_id}/refresh")
def refresh_webhook(base_id: str, webhook_id: str, _: ManageScope) -> dict:
    webhook = _webhook(base_id, webhook_id)
    webhook["expirationTime"] = config.WEBHOOK_EXPIRATION_REFRESHED
    return {"expirationTime": webhook["expirationTime"]}


@router.get("/v0/bases/{base_id}/webhooks/{webhook_id}/payloads")
def list_payloads(base_id: str, webhook_id: str, request: Request, _: PayloadScope) -> dict:
    webhook = _webhook(base_id, webhook_id)
    cursor = _parse_int(request.query_params.get("cursor"), 1)
    limit = min(max(_parse_int(request.query_params.get("limit"), 50), 1), 50)
    matching = [p for p in webhook["payloads"] if p["baseTransactionNumber"] >= cursor]
    page = matching[:limit]
    next_cursor = (page[-1]["baseTransactionNumber"] + 1) if page else cursor
    return {"payloads": page, "cursor": next_cursor, "mightHaveMore": len(matching) > len(page)}
