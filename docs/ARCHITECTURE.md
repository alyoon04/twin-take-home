# Architecture & Implementation Notes

Living design doc. Update it whenever a convention changes. Pairs with
`AIRTABLE_SPEC.md` (what the *real* API does); this doc is *how we implement it*.

## Module map (`twin/` package)
| Module | Responsibility |
|---|---|
| `app.py` (root) | Thin re-export `from twin.api import app`. Keeps `app:app` stable. |
| `twin/api.py` | App factory: build FastAPI, register routers, exception handlers, middleware. |
| `twin/config.py` | Constants: valid PAT(s) + scopes, seed base IDs, rate-limit thresholds, `SEED_CLOCK`. |
| `twin/ids.py` | Deterministic ID generators per type (`app/tbl/fld/viw/rec/usr/com/ach`) from seeded counters. |
| `twin/clock.py` | Deterministic clock: fixed seed instant + fixed step. `reset()` / `stamp()` / `now_iso()`. |
| `twin/store.py` | The in-memory state object + `reset()` + deterministic clock + counters. Single source of mutable state. |
| `twin/seed.py` | Builds the default object graph (bases→tables→fields→views→records, user, webhook). |
| `twin/errors.py` | Error types + helpers + FastAPI exception handlers. Owns the response envelope. |
| `twin/auth.py` | Bearer PAT dependency: missing vs invalid vs insufficient-scope. |
| `twin/pagination.py` | Offset encode/decode, pageSize/maxRecords enforcement, `fields[]` projection. |
| `twin/sorting.py` | Multi-key `sort[]`. |
| `twin/formula.py` | `filterByFormula` subset parser/evaluator. |
| `twin/ratelimit.py` | Deterministic per-base request counter → 429. |
| `twin/routers/*` | Thin HTTP layer per family: `control`, `records`, `meta`, `comments`, `webhooks`. |

Principle: routers are thin; all behavior (validation, errors, pagination, IDs,
clock) lives in shared modules so **every family behaves identically**. That
uniformity is what makes the twin read as one real API.

## Invariants (authoritative)
- **Entry:** `app:app` importable; control endpoints always mounted.
- **Determinism:** all non-determinism funnels through `ids.py` + `clock.py` (the store resets both).
  Forbidden in value generation: `uuid`, `datetime.now`, `time.time`, `random`.
  A guard test greps the package for these.
- **State:** all mutable state lives in `store`; routers hold no module-level mutable data.
  `reset()` fully rebuilds from `seed.py` and clears counters, clock, rate-limit, webhook log.
- **Errors:** every failure path returns via `errors.py`; no raw FastAPI/Starlette default
  body leaks (the 422 handler is overridden to the Airtable shape).

## ID formats
`app… tbl… fld… viw… rec… usr… cmt… wbh…` — exact prefixes/lengths per
`AIRTABLE_SPEC.md` §3. Generated as `<prefix> + deterministic-suffix(counter)` so
IDs are stable, readable, and identical across runs after reset.

## Determinism design
- `config.SEED_INSTANT` = a fixed UTC instant; `clock.stamp()` returns the current value as
  Airtable-style ISO 8601 (`...Z`, ms precision) and advances by `config.CLOCK_STEP`; `clock.reset()` restores it.
- `ids.make_id(prefix, counter)` is a pure hash → base62 suffix; `ids.next_id(prefix)` walks a per-prefix
  counter; `ids.reset_counters()` clears them. The store calls `clock.reset()` + `ids.reset_counters()` on reset (from S5).
- A guard test (`tests/test_determinism.py`) scans `twin/` for entropy sources (`uuid`/`random`/wall-clock) and fails the build if any appear.

## Pagination
Offset = an opaque, deterministic token encoding (table, position). Default
`pageSize` 100, max 100; `maxRecords` caps the total returned; an `offset` is
returned only when more records remain.

## Rate limiting
Per-base counter incremented per request since the last reset; threshold from
`config.py` (mirrors Airtable's 5 req/s/base but counter-based for determinism).
Over threshold → 429 `RATE_LIMIT_REACHED`. `reset()` clears counters. The README
documents the exact reproducible trigger.

## Error catalog
Filled from `AIRTABLE_SPEC.md` §4 as research lands: case → status → `type` →
message template. `errors.py` is the single implementation of this table.

## Testing strategy
- **Unit:** id/clock determinism, formula evaluator, pagination, sort.
- **Endpoint:** per family via FastAPI `TestClient`.
- **Fidelity:** exact status + envelope for each error case in the spec.
- **Determinism:** identical call sequences before/after reset → identical output.
- **Black-box:** `scripts/verify.py` against a running container (mirrors Arga's loop).

## Known, deliberate scope boundaries (documented as gaps)
- `filterByFormula`: a documented subset only (see SPEC §7) — not the full formula language.
- Rate limiting is counter-based, not wall-clock, to keep runs deterministic.
- (Add others here as they arise.)
