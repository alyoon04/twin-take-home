# Airtable Web API — Fidelity Spec (source of truth)

> **STATUS: skeleton.** Phase 0 research (PLAN step **S2**) populates each section
> from the official docs and marks each claim **VERIFIED** with a source link.
> Until then, unverified notes are hypotheses — **do not implement from them blindly.**

**Primary references to cite (S2):**
- https://airtable.com/developers/web/api/introduction
- https://airtable.com/developers/web/api/errors
- https://airtable.com/developers/web/api/list-records
- https://airtable.com/developers/web/api/rate-limits
- Meta, comments, and webhooks subpages of the same reference.

---

## 1. Base URL & versioning
- Real: `https://api.airtable.com/v0`. Twin mounts the same `/v0` paths. *(VERIFY)*

## 2. Auth & scopes
- `Authorization: Bearer <token>` — personal access token (`pat…`) or OAuth access token.
- Scopes (e.g. `data.records:read`, `data.records:write`, `schema.bases:read`,
  `schema.bases:write`, `webhook:manage`). *(VERIFY full list + which routes need which.)*
- Behaviors to pin down: **missing** header vs **invalid** token vs **insufficient scope**
  → exact status + body for each. *(VERIFY)*

## 3. IDs
- `app…` base, `tbl…` table, `fld…` field, `viw…` view, `rec…` record, `usr…` user.
  *(VERIFY exact lengths + charset.)*

## 4. Error model
- Envelope: object `{"error": {"type": "...", "message": "..."}}` **vs** bare string
  `{"error": "NOT_FOUND"}` — *(VERIFY which endpoints use which.)*
- Catalog (status → type) — VERIFY each shape + message:
  - 401 — authentication required / invalid token
  - 403 — not authorized / insufficient permissions or model not found
  - 404 — record `NOT_FOUND`, `TABLE_NOT_FOUND`, `MODEL_ID_NOT_FOUND`
  - 422 — `INVALID_REQUEST_MISSING_FIELDS`, `UNKNOWN_FIELD_NAME`, `INVALID_VALUE_FOR_COLUMN`, `INVALID_REQUEST_UNKNOWN`
  - 429 — rate limit: exact body + any headers
  - 413 — request entity too large; 400 — malformed JSON

## 5. Records API
- Operations: list, get, create (single / batch ≤10 / `typecast`), PATCH (partial),
  PUT (destructive), delete (single / batch), upsert (`performUpsert.fieldsToMergeOn`).
- VERIFY exact JSON for each: `records[]`, `fields`, `id`, `createdTime`, `deleted`,
  `offset`, `returnFieldsByFieldId`, `cellFormat`, `typeCast` vs `typecast` casing.

## 6. List query semantics
- Params: `fields[]`, `filterByFormula`, `maxRecords`, `pageSize` (default/ max),
  `sort[i][field]`/`sort[i][direction]`, `view`, `cellFormat`, `timeZone`, `userLocale`,
  `offset`, `recordMetadata[]`. *(VERIFY caps + the error when `pageSize` is exceeded.)*

## 7. filterByFormula grammar (the subset we implement)
- Planned subset: literals (string/number/bool), field refs `{Field Name}`,
  comparison `= != < > <= >=`, logical `AND() OR() NOT()`, a few functions
  (`FIND() LOWER() UPPER()`). Everything else → **documented gap**.
- *(VERIFY operator/function names + semantics against docs; finalize the boundary in S11.)*

## 8. Meta API
- `whoami`; list bases (pagination); base schema (tables → typed `fields[]` → `views[]`);
  create/update base, table, field. *(VERIFY the field-type catalog + all shapes.)*

## 9. Comments
- list / create / update / delete on a record; pagination. *(VERIFY shapes + `author` object.)*

## 10. Webhooks
- create / list / delete; list **payloads** (cursor); refresh; enable notifications.
- Payload shape for `record.created` / `record.updated` / `record.destroyed` — this is the
  twin's "generated events" stream. *(VERIFY payload + cursor mechanics.)*

## 11. Rate limits
- Documented as 5 requests/sec per base, ~30s penalty after a burst. *(VERIFY exact 429
  body + headers.)* Twin implements this **counter-based** for determinism (see ARCHITECTURE).
