"""Static configuration constants for the twin.

Pure constants only — no state, no wall-clock or entropy sources. The
deterministic clock (clock.py) and ID generator (ids.py) build on these.
"""

from datetime import datetime, timedelta, timezone

# --- Object IDs (AIRTABLE_SPEC.md section 3) ------------------------------
# 17 chars total: a 3-char lowercase prefix + 14 base62 chars.
ID_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
ID_SUFFIX_LEN = 14
ID_TOTAL_LEN = 17

PREFIX_BASE = "app"
PREFIX_TABLE = "tbl"
PREFIX_FIELD = "fld"
PREFIX_VIEW = "viw"
PREFIX_RECORD = "rec"
PREFIX_USER = "usr"
PREFIX_COMMENT = "com"
PREFIX_WEBHOOK = "ach"

ALL_PREFIXES = (
    PREFIX_BASE, PREFIX_TABLE, PREFIX_FIELD, PREFIX_VIEW,
    PREFIX_RECORD, PREFIX_USER, PREFIX_COMMENT, PREFIX_WEBHOOK,
)

# --- Deterministic clock --------------------------------------------------
# Fixed base instant, advanced by a fixed step per stamp(). All timestamps
# derive from this so a reset + identical replay is byte-identical.
SEED_INSTANT = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
CLOCK_STEP = timedelta(seconds=1)
