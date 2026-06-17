# Fidelity Audit (S24)

Adversarial multi-agent audit (8 reviewers → per-finding skeptics → completeness critic),
20 agents, run 2026-06-17. Each reviewer compared the implementation to `AIRTABLE_SPEC.md`
+ the official docs for valid **and** invalid inputs; every finding was independently
verified (skeptic tries to refute) before inclusion.

**Result:** 11 raw findings → **8 confirmed**, 3 refuted (false positives). Overall fidelity
rated high. All 8 are small, well-scoped fixes; addressed in S25.

## Confirmed findings → fix plan

| # | Sev | Area | Issue | Fix |
|---|---|---|---|---|
| 1 | med | records | `GET …/{recordId}` ignores `returnFieldsByFieldId` (list/create/update honor it; single GET doesn't) | thread the flag into `get_record` |
| 2 | low | records | create >10 → generic message, not verbatim `"A maximum of 10 records can be created per request but you have provided N."` | use the verbatim count message |
| 3 | low | list | ascending `sort[]` puts blank cells **last**; Airtable puts them **first** | flip blank ordering in `_sort_key` |
| 4 | med | meta | `whoami` always returns `scopes`; Airtable omits it for PATs (only OAuth tokens get `scopes`) | return `{id}` only (our tokens are PAT-style) |
| 5 | low | meta | `POST /v0/meta/bases` doesn't require `workspaceId` | validate `workspaceId` present |
| 6 | med | comments | list-comments omits `offset` on the last page; Airtable returns `offset: null` | always include `offset` (null when done) |
| 7 | med | webhooks | `cursorForNextPayload` frozen at 1; should advance as payloads are generated | bump it in `events.emit_change` |
| 8 | med | errors | `405` leaks FastAPI `{"detail": …}` instead of an Airtable envelope | reshape non-404 Starlette errors to the object envelope |

## Completeness gap → fix plan

- **Missing:** `POST /v0/bases/{baseId}/webhooks/{webhookId}/enableNotifications` (enable/disable
  webhook notifications, spec §10.8). → add it (toggles `areNotificationsEnabled`).

Everything else in the documented surface is implemented.

## Refuted (false positives — skeptics rejected)

- Batch update/upsert >10 should use type `INVALID_RECORDS` — *type is community-attested only; the
  closest-documented-shape leniency applies.*
- `sort[]` by an unknown field should 422 — *Airtable's behavior here is undocumented; silently
  ignoring is defensible.*
- `filterByFormula` unknown-field message should be the `"Unknown field names: …"` variant — *the
  generic `INVALID_FILTER_BY_FORMULA` message is acceptable.*
