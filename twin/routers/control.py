"""Arga control endpoints: health, state snapshot, deterministic reset, rate-limit toggle.

Required by the Arga validator regardless of provider; must always work.
"""

from typing import Annotated

from fastapi import APIRouter, Body

from twin import config, store

router = APIRouter(tags=["control"])


@router.get("/_arga/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/_arga/admin/state")
def admin_state() -> dict:
    return store.snapshot()


@router.post("/_arga/admin/reset")
def admin_reset() -> dict[str, str]:
    store.reset_state()
    return {"status": "reset"}


@router.post("/_arga/admin/rate-limit")
def admin_rate_limit(body: Annotated[dict | None, Body()] = None) -> dict:
    """Enable/configure the deterministic per-base rate limiter (off by default)."""
    body = body or {}
    rl = store.state.setdefault(
        "rateLimit", {"enabled": False, "perBase": config.RATE_LIMIT_PER_BASE, "counts": {}}
    )
    if "enabled" in body:
        rl["enabled"] = bool(body["enabled"])
    if "perBase" in body:
        try:
            rl["perBase"] = int(body["perBase"])
        except (TypeError, ValueError):
            pass
    rl["counts"] = {}  # reconfiguring clears the counters
    return {"rateLimit": {"enabled": rl["enabled"], "perBase": rl["perBase"]}}
