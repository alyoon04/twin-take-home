# Development Plan — Airtable Web API Twin

One step ≈ one commit. Each step ends at a **green gate** (tests pass, `app:app`
imports) before committing. Update `PROGRESS.md` after every step. `[FAN-OUT]`
marks a multi-agent workflow; everything else is built solo in one context.
Commit messages are conventional-commits style.

## Phase 0 — Setup & Research
- **S0 — Planning + docs scaffolding** *(this step)*
  - Create `CLAUDE.md` + `docs/{PLAN,PROGRESS,ARCHITECTURE,AIRTABLE_SPEC}.md`.
  - Gate: docs present. Commit: `docs: development plan, progress log, architecture, fidelity spec`
- **S1 — Baseline verification**
  - `uv sync`; `uv run pytest` (starter tests green); `docker build -t candidate-twin .`. Record results + tool versions in PROGRESS.
  - Gate: starter builds + tests pass unchanged. Commit: `chore: record verified starter baseline`
- **S2 — Fidelity research → AIRTABLE_SPEC.md  [FAN-OUT]**
  - Parallel agents read the official Airtable Web API reference and fill each SPEC
    section with VERIFIED, cited shapes (auth/scopes, error catalog, records, list
    query, formula grammar, meta, comments, webhooks, rate limits). An independent
    verifier cross-checks contested claims.
  - Gate: every SPEC section marked VERIFIED with a source link. Commit: `docs: airtable fidelity spec from official API reference`

## Phase 1 — Foundation (solo)
- **S3 — Package skeleton + control endpoints** — `twin/` package; thin `app.py`
  (`from twin.api import app`); port `/_arga/*`. Gate: existing tests pass.
  Commit: `refactor: extract twin package; preserve app:app + control endpoints`
- **S4 — Deterministic IDs + clock** — `twin/ids.py`, `SEED_CLOCK`. Unit tests. Commit: `feat: deterministic id + clock generators`
- **S5 — Store + reset + richer /state** — `twin/store.py`. Gate: determinism/reset tests. Commit: `feat: in-memory store with deterministic reset`
- **S6 — Error model + handlers** — `twin/errors.py`; override FastAPI 422. Commit: `feat: airtable-shaped error model + exception handlers`
- **S7 — Auth** — `twin/auth.py` (missing / invalid / insufficient-scope). Commit: `feat: bearer PAT auth with missing/invalid/scope cases`
- **S8 — Seed graph** — `twin/seed.py` (CRM + Project Tracker bases). Document stable IDs in ARCHITECTURE. Commit: `feat: deterministic seed graph`

## Phase 2 — Records API (solo)
- **S9 — Read** — list (basic) + get + not-found. Commit: `feat: records list + get`
- **S10 — List query** — pageSize/maxRecords/offset, `fields[]`, `sort[]`. Commit: `feat: records pagination, projection, sort`
- **S11 — filterByFormula subset** — `twin/formula.py`. Commit: `feat: filterByFormula subset evaluator`
- **S12 — Create** — single + batch (≤10) + `typecast` + validation errors. Commit: `feat: records create with validation`
- **S13 — Update** — PATCH (partial) + PUT (destructive) + upsert. Commit: `feat: records update (patch/put/upsert)`
- **S14 — Delete** — single + batch. Commit: `feat: records delete (single/batch)`

## Phase 3 — Meta / Comments / Webhooks (solo)
- **S15 — Meta read** — whoami, list bases, base schema. Commit: `feat: meta api read`
- **S16 — Meta write** — create/update base, table, field. Commit: `feat: meta api writes`
- **S17 — Comments CRUD**. Commit: `feat: record comments`
- **S18 — Webhooks + payload event log** (wired to record mutations). Commit: `feat: webhooks + payload event log`

## Phase 4 — Hardening (solo)
- **S19 — Rate limiting** — deterministic, reset-clearable per-base → 429. Commit: `feat: deterministic rate limiting`
- **S20 — Cross-cutting polish** — error-consistency sweep, `X-Request-Id` header, OpenAPI tags/examples. Commit: `polish: error consistency, request id, openapi examples`

## Phase 5 — Contract / Verify / Docs (solo)
- **S21 — twin-contract.yaml** fully populated. Commit: `docs: complete twin-contract.yaml`
- **S22 — scripts/verify.py** black-box verifier (build→health→reset→sample). Commit: `test: black-box verification script`
- **S23 — README** rewrite (provider, coverage matrix, creds, run, examples, gaps). Commit: `docs: applicant readme`

## Phase 6 — Adversarial Audit
- **S24 — Fidelity + completeness audit  [FAN-OUT]** → `docs/AUDIT.md`. One agent per
  family compares twin vs SPEC/docs for valid + invalid inputs; verifiers confirm/refute
  each finding; a completeness critic diffs implemented routes vs the documented surface.
  Commit: `docs: fidelity audit findings`
- **S25 — Fix findings** (small commits) + re-audit until clean. Gate: full pytest + `docker run` + `verify.py` green. Commit: `fix: <finding>` per fix
- **S26 — Final verification + submission polish**. Gate: brief's exact build/run commands pass; determinism re-check; coverage matrix final. Commit: `chore: final verification`
