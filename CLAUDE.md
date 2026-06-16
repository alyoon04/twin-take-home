# Airtable Web API Twin — Agent Guide

A Dockerized FastAPI service that emulates the **Airtable Web API** for the Arga
"SaaS twin" take-home. It is graded black-box on **fidelity to the real API for
valid *and* invalid inputs**, plus **completeness** of the documented surface.

## Read these first — every session, in order
1. `docs/PROGRESS.md` — current status, the **"Resume here"** pointer, decision log. **Start here.**
2. `docs/ARCHITECTURE.md` — module map and the invariants you must preserve.
3. `docs/AIRTABLE_SPEC.md` — researched real-API behavior. **Build to this, not from memory.**
4. `docs/PLAN.md` — the step-by-step roadmap (one commit per step).

## Hard invariants — never break
- Entry point stays importable as `app:app` (Dockerfile CMD + tests depend on it).
- Listens on `0.0.0.0:8080` inside the container.
- **Determinism:** no `uuid`, no `datetime.now()`/`time.time()` for values, no `random`.
  IDs and timestamps come from seeded counters / a fixed clock, so the same calls
  after `POST /_arga/admin/reset` always produce byte-identical output.
- Error responses match the envelope + status in `AIRTABLE_SPEC.md`.
- Control endpoints `/_arga/healthz`, `/_arga/admin/state`, `/_arga/admin/reset` always work.
- **Zero new runtime dependencies** (stdlib + FastAPI only).

## Workflow
- **One step from `docs/PLAN.md` per commit.** Small, reviewable diffs.
- Before every commit: `uv run pytest` is green and `from app import app` works.
- **Run verification proactively, without asking** (standing instruction): `pytest` every step; a `docker build` + container smoke test at milestones and whenever Docker-affecting files change (`Dockerfile`, `pyproject.toml`, `uv.lock`).
- After every step: update `docs/PROGRESS.md` — tick the box, move **"Resume here"**, append any decision.
- Build the coupled core **solo**, in one context. Use multi-agent workflows **only** for the
  steps flagged `[FAN-OUT]` (S2 research, S24 audit), where independent perspectives help.
- Don't commit unless the human asks; branch off `main` is already set (origin = twin-take-home).

## Commands
- Dev server: `uv run uvicorn app:app --reload --port 8080`
- Tests: `uv run pytest`
- Black-box verify: `uv run python scripts/verify.py`
- Docker: `docker build -t candidate-twin .` then `docker run --rm -p 8080:8080 candidate-twin`
