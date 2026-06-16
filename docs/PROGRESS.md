# Progress Log

> **Resume here:** S0 (planning + docs scaffolding) complete.
> **Next → S1: baseline verification** — `uv sync`, `uv run pytest`, `docker build`
> on the untouched starter; record results below. Then S2 (fidelity research).

**Last updated:** 2026-06-16 — S0
**Current phase:** Phase 0 — Setup & Research

## Checklist
### Phase 0 — Setup & Research
- [x] S0 Planning + docs scaffolding
- [ ] S1 Baseline verification (uv sync, pytest, docker build)
- [ ] S2 Fidelity research → AIRTABLE_SPEC.md  `[FAN-OUT]`
### Phase 1 — Foundation
- [ ] S3 twin/ skeleton + control endpoints ported
- [ ] S4 Deterministic IDs + clock
- [ ] S5 Store + reset + richer /state
- [ ] S6 Error model + handlers
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

## Decision log
- **2026-06-16** — Provider = **Airtable Web API** (user-confirmed). Rationale: compact +
  fully completable surface, native list/query semantics, clean reproducible errors.
- **2026-06-16** — **Hybrid agent strategy**: build the coupled core solo in one context;
  multi-agent only for S2 (fidelity research) and S24 (adversarial audit). Parallelizing
  the build would cause cross-family inconsistency, which is exactly what fails fidelity.
- **2026-06-16** — **Zero new runtime deps**; determinism via seeded IDs + a fixed seed clock.

## Open questions / to verify (resolve in S2)
- Exact Airtable error envelopes (object `{"error":{type,message}}` vs string `{"error":"NOT_FOUND"}`) per endpoint.
- `filterByFormula` subset boundary — which operators/functions we support vs document as a gap.
- Exact 429 body + headers and whether real Airtable returns extra rate-limit headers.

## Notes for the next session
- Nothing in flight. Working tree should be clean after S0 is committed.
- `app.py` is still the untouched starter; the `twin/` package does not exist yet (created in S3).
