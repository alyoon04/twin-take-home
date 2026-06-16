# Progress Log

> **Resume here:** S6 (Airtable error model) complete — `errors.py` with the dual envelope, the verified
> catalog (verbatim messages), and handlers (custom errors + 422 override + unmatched-route NOT_FOUND);
> 26 tests passing. **Next → S7: real PAT auth** (`twin/auth.py`) — `Authorization: Bearer pat…`,
> distinguishing missing/invalid (401 `AUTHENTICATION_REQUIRED`) from insufficient scope (403), seeding a
> valid token in the store + documenting an invalid one.

**Last updated:** 2026-06-16 — S6
**Current phase:** Phase 1 — Foundation (S7 next)

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
- [ ] S7 Auth (missing/invalid/scope)
- [ ] S8 Seed graph
### Phase 2 — Records API
- [ ] S9 Records read (list + get + 404)
- [ ] S10 List query (pagination, fields[], sort[])
- [ ] S11 filterByFormula subset
- [ ] S12 Records create (single/batch/typecast/validation)
- [ ] S13 Records update (patch/put/upsert)
- [ ] S14 Records delete (single/batch)
### Phase 3 — Meta / Comments / Webhooks
- [ ] S15 Meta read (whoami/bases/schema)
- [ ] S16 Meta write (create/update base/table/field)
- [ ] S17 Comments CRUD
- [ ] S18 Webhooks + payload event log
### Phase 4 — Hardening
- [ ] S19 Rate limiting (429)
- [ ] S20 Cross-cutting polish (errors, request-id, OpenAPI examples)
### Phase 5 — Contract / Verify / Docs
- [ ] S21 twin-contract.yaml complete
- [ ] S22 scripts/verify.py
- [ ] S23 README rewrite
### Phase 6 — Adversarial Audit
- [ ] S24 Fidelity + completeness audit  `[FAN-OUT]`
- [ ] S25 Fix findings + re-audit clean
- [ ] S26 Final verification + submission polish

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
- Package: `twin/{api,config,ids,clock,store,errors,auth}.py` + `twin/routers/{control,example}.py`; `app.py` re-exports `twin.api:app`.
- `store.py` + `seed.py` are real; `/_arga/admin/reset` resets ids+clock+state deterministically. Stable seed IDs: CRM base `app1MrVfxTUgJuBm0`, Contacts table `tblSopvR8A6870fpC` (3 records).
- `twin/routers/example.py` is a TEMPORARY placeholder — delete it in S9 when the real records routes land.
- `errors.py` is real (catalog + handlers: AirtableError, 422 override, unmatched-route NOT_FOUND). `provider_error` lingers only for the example router.
- `twin/auth.py` still holds the starter placeholder (`Bearer sk_test_twin_123`, used by example) — real PAT auth added alongside it in S7.
- `seed.py` is minimal (1 base) — S8 expands it to the full graph (2 bases, all field types, links, comments, a webhook).
