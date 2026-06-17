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
PREFIX_SELECT = "sel"

ALL_PREFIXES = (
    PREFIX_BASE, PREFIX_TABLE, PREFIX_FIELD, PREFIX_VIEW,
    PREFIX_RECORD, PREFIX_USER, PREFIX_COMMENT, PREFIX_WEBHOOK, PREFIX_SELECT,
)

# --- Deterministic clock --------------------------------------------------
# Fixed base instant, advanced by a fixed step per stamp(). All timestamps
# derive from this so a reset + identical replay is byte-identical.
SEED_INSTANT = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
CLOCK_STEP = timedelta(seconds=1)

# --- Auth (AIRTABLE_SPEC.md section 2) ------------------------------------
SCOPE_RECORDS_READ = "data.records:read"
SCOPE_RECORDS_WRITE = "data.records:write"
SCOPE_SCHEMA_READ = "schema.bases:read"
SCOPE_SCHEMA_WRITE = "schema.bases:write"
SCOPE_WEBHOOK_MANAGE = "webhook:manage"

ALL_SCOPES = [
    SCOPE_RECORDS_READ,
    SCOPE_RECORDS_WRITE,
    SCOPE_SCHEMA_READ,
    SCOPE_SCHEMA_WRITE,
    SCOPE_WEBHOOK_MANAGE,
]

# Documented fake credentials (README + twin-contract.yaml). Only seeded tokens
# are accepted; any other Bearer value -> 401 (indistinguishable from missing).
# Shaped like Airtable PATs (`pat<id>.<secret>`) for auth fidelity, but with an
# obviously-fake, non-hex body so secret scanners don't match them; auth is pure
# string equality, so the literal value is opaque to behavior.
VALID_PAT = "patTwinDevFull001.FAKE-not-a-real-secret-do-not-use-full-scope"
READONLY_PAT = "patTwinReadOnly01.FAKE-not-a-real-secret-do-not-use-readonly"
INVALID_PAT_EXAMPLE = "patInvalidExmpl01.FAKE-not-a-real-secret-do-not-use-invalid"

# --- Webhooks (AIRTABLE_SPEC.md section 10) -------------------------------
# Deterministic, fixed expiration (real Airtable: 7 days after creation).
WEBHOOK_EXPIRATION = (SEED_INSTANT + timedelta(days=7)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
WEBHOOK_EXPIRATION_REFRESHED = (SEED_INSTANT + timedelta(days=14)).isoformat(timespec="milliseconds").replace("+00:00", "Z")

# --- Rate limiting (AIRTABLE_SPEC.md section 11) --------------------------
# Off by default; opt-in via POST /_arga/admin/rate-limit so it never breaks the
# validator's normal sampling. Counter-based (not wall-clock) to stay
# deterministic; mirrors Airtable's documented 5 requests/second/base.
RATE_LIMIT_PER_BASE = 5
