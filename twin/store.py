"""In-memory state for the twin — the single source of mutable state.

``reset_state()`` rebuilds from ``seed.build()`` and resets the deterministic id
counters + clock, so ``POST /_arga/admin/reset`` makes the twin byte-identical
across runs. ``snapshot()`` is the debug view returned by ``/_arga/admin/state``.
"""

from copy import deepcopy

from twin import clock, ids, seed

# Live state. Built once at import from the deterministic seed, then mutated in
# place by reset_state() so module-level references (the routers) stay valid.
state = seed.build()


def reset_state() -> None:
    """Reset to the deterministic default: clear counters + clock, rebuild seed."""
    ids.reset_counters()
    clock.reset()
    fresh = seed.build()
    state.clear()
    state.update(fresh)


def _counts() -> dict:
    bases = state.get("bases", {})
    tables = [t for b in bases.values() for t in b["tables"].values()]
    return {
        "bases": len(bases),
        "tables": len(tables),
        "records": sum(len(t["records"]) for t in tables),
        "users": len(state.get("users", {})),
        "tokens": len(state.get("tokens", {})),
        "webhooks": len(state.get("webhooks", {})),
    }


def snapshot() -> dict:
    """Debug snapshot for /_arga/admin/state: full state plus a counts summary."""
    snap = deepcopy(state)
    snap["counts"] = _counts()
    return snap
