"""Deterministic object-ID generation (AIRTABLE_SPEC.md section 3).

IDs are derived from per-prefix counters via a stable hash, so the Nth id of a
given type after ``reset_counters()`` is always identical. No entropy sources:
the only variability is the counter, which the store resets deterministically.
"""

import hashlib

from twin.config import (
    ALL_PREFIXES,
    ID_ALPHABET,
    ID_SUFFIX_LEN,
    ID_TOTAL_LEN,
    PREFIX_BASE,
    PREFIX_COMMENT,
    PREFIX_FIELD,
    PREFIX_RECORD,
    PREFIX_SELECT,
    PREFIX_TABLE,
    PREFIX_USER,
    PREFIX_VIEW,
    PREFIX_WEBHOOK,
)

_counters: dict[str, int] = {}


def make_id(prefix: str, counter: int) -> str:
    """Pure, deterministic id for ``(prefix, counter)``. Same inputs -> same id."""
    digest = hashlib.sha256(f"{prefix}:{counter}".encode()).digest()
    n = int.from_bytes(digest, "big")
    base = len(ID_ALPHABET)
    chars = []
    for _ in range(ID_SUFFIX_LEN):
        n, rem = divmod(n, base)
        chars.append(ID_ALPHABET[rem])
    return prefix + "".join(chars)


def next_id(prefix: str) -> str:
    """Next deterministic id for ``prefix`` (1-based per-prefix counter)."""
    count = _counters.get(prefix, 0) + 1
    _counters[prefix] = count
    return make_id(prefix, count)


def reset_counters() -> None:
    """Clear all per-prefix counters (the store calls this on reset)."""
    _counters.clear()


def is_well_formed(value: str) -> bool:
    """True if ``value`` matches the 17-char prefixed shape this twin emits."""
    if not isinstance(value, str) or len(value) != ID_TOTAL_LEN:
        return False
    return value[:3] in ALL_PREFIXES and all(c in ID_ALPHABET for c in value[3:])


def base_id() -> str:
    return next_id(PREFIX_BASE)


def table_id() -> str:
    return next_id(PREFIX_TABLE)


def field_id() -> str:
    return next_id(PREFIX_FIELD)


def view_id() -> str:
    return next_id(PREFIX_VIEW)


def record_id() -> str:
    return next_id(PREFIX_RECORD)


def user_id() -> str:
    return next_id(PREFIX_USER)


def comment_id() -> str:
    return next_id(PREFIX_COMMENT)


def webhook_id() -> str:
    return next_id(PREFIX_WEBHOOK)


def select_id() -> str:
    return next_id(PREFIX_SELECT)
