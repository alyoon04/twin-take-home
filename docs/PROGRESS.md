# Progress Log

> **Resume here:** ✅ **BUILD COMPLETE (S0–S26) + post-audit polish.** 136 pytest, `docker build`/`run`
> (brief's exact commands), `verify.py` 16/16 vs container, determinism replay byte-identical. Polish:
> `pat…`-shaped fake tokens (scanner-safe, more auth-faithful) + `reactions` field on the comment object.
> Full Airtable surface (Records, Meta, Comments, Webhooks) + control. Ready to push.

**Last updated:** 2026-06-17 — S26 (complete)
**Current phase:** ✅ Complete

## Checklist
### Phase 0 — Setup & Research
- [x] S0 Planning + docs scaffolding
- [x] S1 Baseline verification (uv sync, pytest, docker build)
- [x] S2 Fidelity research → AIRTABLE_SPEC.md  `[FAN-OUT]`
### Phase 1 — Foundation
- [x] S3 twin/ skeleton + control endpoints ported
- [x] S4 Deterministic IDs + clock
- [x] S5 Store + reset + richer /state
- [x] S6 Error model + handlers
- [x] S7 Auth (missing/invalid/scope)
- [x] S8 Seed graph
### Phase 2 — Records API
- [x] S9 Records read (list + get + 404)
- [x] S10 List query (pagination, fields[], sort[])
- [x] S11 filterByFormula subset
- [x] S12 Records create (single/batch/typecast/validation)
- [x] S13 Records update (patch/put/upsert)
- [x] S14 Records delete (single/batch)
### Phase 3 — Meta / Comments / Webhooks
- [x] S15 Meta read (whoami/bases/schema)
- [x] S16 Meta write (create/update base/table/field)
- [x] S17 Comments CRUD
- [x] S18 Webhooks + payload event log
### Phase 4 — Hardening
- [x] S19 Rate limiting (429)
- [x] S20 Cross-cutting polish (errors, request-id, OpenAPI examples)
### Phase 5 — Contract / Verify / Docs
- [x] S21 twin-contract.yaml complete
- [x] S22 scripts/verify.py
- [x] S23 README rewrite
### Phase 6 — Adversarial Audit
- [x] S24 Fidelity + completeness audit  `[FAN-OUT]`
- [x] S25 Fix findings + re-audit clean
- [x] S26 Final verification + submission polish

## Baseline (S1) — verified 2026-06-16
- Tooling: uv 0.11.21, Docker 28.3.3 (daemon up). `.python-version` = 3.12 → uv provisioned CPython 3.12.13.
- `uv sync`: OK — 25 packages (fastapi 0.115.6, uvicorn 0.34.0, pytest 8.3.4, httpx 0.28.1).
- `uv run pytest`: **4/4 passed** (`tests/test_control.py`).
- `docker build -t candidate-twin .`: OK — image `candidate-twin` (sha256 `669d2097…`).
- Container runtime smoke: `docker run -p 8080:8080` → `GET /_arga/healthz` → `{"status":"ok"}` (uvicorn on 0.0.0.0:8080).
- Gotcha for `verify.py` (S22): health takes ~1s; the port proxy resets the connection before uvicorn is ready, so the verifier must **retry on connection-reset**, not just connection-refused.

## S2 research outcome (2026-06-16) — load-bearing facts for the build
10 sections vs official docs (5 high / 5 medium confidence); 5 critical sections independently
re-verified — all 5 surfaced real corrections, now authoritative in `AIRTABLE_SPEC.md`. Essentials:

- **IDs:** 17 chars = 3-char lowercase prefix + 14× `[0-9A-Za-z]`. base `app`, table `tbl`, field `fld`,
  view `viw`, record `rec`, user `usr`, comment `com`, webhook `ach`. Generator emits this; validator stays
  lenient (charset/length not a documented invariant).
- **Two error envelopes coexist (official):** object `{"error":{"type","message"}}` AND bare string
  `{"error":"NOT_FOUND"}`. Object-form 404 is `{"error":{"type":"NOT_FOUND"}}` with **no** `message`. `errors.py` supports both.
- **429 = singular envelope** `{"error":{"type":"RATE_LIMIT_REACHED","message":"Rate limit exceeded. Please try again later"}}`
  (no trailing period) — NOT a plural array. Limits: 5 req/s/base + 50 req/s/token; 30s cooldown; no `Retry-After` on 429.
- **List paging:** `pageSize` default 100 / max 100; `maxRecords` caps total; **stale/unknown `offset` →
  `422 LIST_RECORDS_ITERATOR_NOT_AVAILABLE`**; `cellFormat=string` needs `timeZone`+`userLocale`; `sort` overrides `view`;
  GET & POST `/listRecords` (16,000-char URL limit); `INVALID_FILTER_BY_FORMULA` is 422.
- **filterByFormula exclusion set:** `0, false, "", NaN, [], #Error!`.
- **Status set:** 200, 400, 401, 403, 404, 413, 422, 429, 500, 502, 503. 422 includes `FAILED_STATE_CHECK`.
- **Auth:** `Authorization: Bearer <pat…|oauth>`; Basic rejected; `api_key` query param unsupported. 401
  `AUTHENTICATION_REQUIRED`; 403 `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` (verbatim). Don't enforce PAT length.

## Decision log
- **2026-06-16** — Provider = **Airtable Web API** (user-confirmed). Rationale: compact +
  fully completable surface, native list/query semantics, clean reproducible errors.
- **2026-06-16** — **Hybrid agent strategy**: build the coupled core solo in one context;
  multi-agent only for S2 (fidelity research) and S24 (adversarial audit). Parallelizing
  the build would cause cross-family inconsistency, which is exactly what fails fidelity.
- **2026-06-16** — **Zero new runtime deps**; determinism via seeded IDs + a fixed seed clock.
- **2026-06-16 (S2)** — Source of truth = `AIRTABLE_SPEC.md`; per step, read its relevant section.
  Verifier `⚠` notes override the section drafts they annotate.
- **2026-06-16 (S2)** — Adversarial verification changed real decisions: 429 uses the **singular** error
  envelope (not the plural-array third-party shape); stale offset → `422 LIST_RECORDS_ITERATOR_NOT_AVAILABLE`;
  404 supports both bare-string and message-less object forms.

## Open questions (carried to build / S24 audit)
S2 resolved the big ones (see outcome above). Remaining unconfirmed items live in `AIRTABLE_SPEC.md`
→ "Open questions & low-confidence items". Notable ones to settle while implementing:
- Exact `type`/`message` for 400, 413, 500 (official docs don't enumerate them).
- `filterByFormula` subset boundary — finalize in S11 from SPEC §7's recommendation.
- Per-route choice of bare-string vs object 404 envelope (docs show both; not disambiguated).

## Notes for the next session
- `AIRTABLE_SPEC.md` is the build's source of truth — read the relevant section before each step.
- Package: `twin/{api,config,ids,clock,store,errors,auth,formula,recordutil,events}.py` + `twin/routers/{control,meta,comments,webhooks,records}.py`; `app.py` re-exports `twin.api:app`. **Router order in `api.py`: control → meta → comments → webhooks → records** (specific paths before generic `/v0/{baseId}/{table}`).
- Webhooks live per-base (`base["webhooks"]`, `base["transactionNumber"]`); `events.emit_change(table, …)` appends `record.created/updated/destroyed` payloads on every record mutation (the "generated events" stream). One webhook seeded on CRM.
- Rate limiting: opt-in per-base counter in `store.state["rateLimit"]`, toggled via `POST /_arga/admin/rate-limit {enabled,perBase}` (middleware in `api.py`). **Off by default** (avoids spurious 429s during validation); counter-based → deterministic; reset clears+disables.
- `api.py` middleware also sets a deterministic `X-Request-Id` (`req…`, from `store.state["requestSeq"]`, reset-clearable) on every response. OpenAPI has per-tag descriptions.
- `comments.py`: list/create/update/delete on a record; `recordMetadata[]=commentCount` wired into records list; stored at `record["comments"]`. **Scope simplification (flag for S24): comments reuse `data.records:read/write`, not Airtable's `data.recordComments:*`.**
- `meta.py`: **complete** — read (whoami, list bases, base schema) + write (create base/table/field, update table/field). Meta uses **object-form 404** (`not_found()`), unlike the data API's bare-string. Field type immutable on PATCH.
- `store.py` + `seed.py` real; `/_arga/admin/reset` resets ids+clock+state deterministically. Stable seed IDs: CRM base `app1MrVfxTUgJuBm0`, Contacts table `tblSopvR8A6870fpC` (5 records).
- `errors.py` real (AirtableError catalog + handlers: 422 override, unmatched-route NOT_FOUND). **Data-API not-found uses `not_found(bare=True)` → `{"error":"NOT_FOUND"}`.**
- `auth.py` real: `get_token` + `require_scope(scope)`. Fake creds: `config.VALID_PAT` (full), `config.READONLY_PAT` (read-only), `config.INVALID_PAT_EXAMPLE` (invalid).
- `seed.py` full graph: CRM/Contacts (5) + Project Tracker/Projects (3) + Tasks (5), Projects↔Tasks links. Records hold only non-empty cells (`seed._clean`) — **S12/S13 writes must apply the same rule.** Comments + webhook arrive in S17/S18.
- `records.py`: **Records API COMPLETE** — read / query / create / update (PATCH+PUT, batch, upsert) / delete. `typecast` auto-creates select options; type validation strict for singleSelect, lenient otherwise (documented partial for S24). Deferred query gaps: `view`, `cellFormat=string`/`timeZone`/`userLocale`.
- **Not-found / validation model (LIVE-VERIFIED 2026-06-17 vs real Airtable, read + write — the API is NOT uniform):**
  - Missing **base** or **unrouted path** → bare `404 {"error":"NOT_FOUND"}`.
  - Missing **table** (valid base) → `403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`.
  - Missing **record**, *single* GET/PATCH/PUT/DELETE → `403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`.
  - Missing id in *batch* update **or** upsert → `422 ROW_DOES_NOT_EXIST` ("Record ID X does not exist in this table").
  - Missing id in *batch* DELETE → `404 {"error":{"type":"NOT_FOUND","message":"Could not find a record with ID \"X\"."}}`.
  - `pageSize=0` / `maxRecords=0` → `200` empty; non-numeric pageSize/maxRecords → ignored; pageSize outside [0,100] → `422 INVALID_PAGE_SIZE_ARGUMENT`.
  - Offset: malformed → `422 INVALID_OFFSET_VALUE`; well-formed-but-stale → `422 LIST_RECORDS_ITERATOR_NOT_AVAILABLE` (message-less object).
  - `UNKNOWN_FIELD_NAME` message is `Unknown field name: "X"`; `INVALID_FILTER_BY_FORMULA` message is `The formula for filtering records is invalid: <Invalid formula...|Unknown field names: <lowercased>>`.
  - **Meta API (LIVE-VERIFIED read):** `whoami` (`{id}`), `bases` (`{id,name,permissionLevel}`), and base schema (`tables[].{id,name,primaryFieldId,fields[],views[]}`) all match real shapes. **Missing base in meta → `403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`** (existence-hiding) — fixed in `meta.py:base_schema` (was object-form 404). Note this differs from the *data* API, where a missing base is a bare 404. Meta-**write** missing-model cases (create/update table·field on a missing base/table) remain **unverified** — the test token lacked `schema.bases:write`.
  - **Known divergence (not yet matched):** real Airtable did NOT enforce the 10-record create limit (created 11, `200`); twin still returns `422` per the documented limit. `maxRecords=-1` has an undocumented quirk on real (returned n-1) not replicated.
- `recordutil.clean_fields` = the shared "omit empty cells" rule (used by seed + writes).
- `formula.py`: filterByFormula subset (recursive-descent). Out of scope (documented): date/time, regex, array/rollup, record-meta functions.
- Pagination `offset` = `itr<index>/<recordId>` (opaque, deterministic); `_decode_offset` raises iterator-422 on bad/stale values.
