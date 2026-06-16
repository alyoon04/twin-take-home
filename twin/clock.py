"""Deterministic clock.

Starts at ``config.SEED_INSTANT`` and advances by ``config.CLOCK_STEP`` each
``stamp()``. ``reset()`` returns it to the seed instant, so a reset + identical
call sequence yields identical timestamps. No wall-clock reads anywhere.
"""

from twin.config import CLOCK_STEP, SEED_INSTANT

_current = SEED_INSTANT


def reset() -> None:
    """Return the clock to the seed instant."""
    global _current
    _current = SEED_INSTANT


def _iso(dt) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now_iso() -> str:
    """Current clock value as Airtable-style ISO 8601 (does not advance)."""
    return _iso(_current)


def stamp() -> str:
    """Return the current clock value, then advance by one step."""
    global _current
    value = _iso(_current)
    _current = _current + CLOCK_STEP
    return value
