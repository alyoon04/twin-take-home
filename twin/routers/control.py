"""Arga control endpoints: health, state snapshot, deterministic reset.

Required by the Arga validator regardless of provider; must always work.
"""

from fastapi import APIRouter

from twin import store

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
