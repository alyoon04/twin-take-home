# Airtable Web API Twin

A local, Dockerized, **fake Airtable** that another app can point at instead of
`https://api.airtable.com` during development or testing. It speaks the Airtable
Web API — same paths, request/response shapes, auth style, pagination, and error
envelopes — backed by deterministic in-memory state.

- **Provider:** [Airtable Web API](https://airtable.com/developers/web/api/introduction)
- **Why Airtable:** a compact, fully-completable REST surface (Records, Meta, Comments,
  Webhooks) with rich list semantics (`filterByFormula`, sort, pagination), distinctive
  IDs, and a clean, reproducible error model — so the twin can cover the *whole* public
  API faithfully rather than a slice.

## Quick start

```bash
docker build -t candidate-twin .
docker run --rm -p 8080:8080 candidate-twin
```

The service listens on `0.0.0.0:8080`. Health check: `curl localhost:8080/_arga/healthz`.

Local dev (no Docker):

```bash
uv sync
uv run uvicorn app:app --reload --port 8080
```

## Authentication

Airtable-style bearer tokens (`Authorization: Bearer <token>`). Only the seeded
fake tokens are accepted; **any other token returns `401`, indistinguishable from a
missing one** (matching Airtable). The tokens are `pat…`-shaped like real Airtable
PATs but carry an obviously-fake body, so they won't trip secret scanners.

| Credential | Token | Scopes |
|---|---|---|
| **Valid (full)** | `Bearer patTwinDevFull001.FAKE-not-a-real-secret-do-not-use-full-scope` | records r/w, schema r/w, webhook:manage |
| **Read-only** | `Bearer patTwinReadOnly01.FAKE-not-a-real-secret-do-not-use-readonly` | records:read, schema:read |
| **Invalid (example)** | `Bearer patInvalidExmpl01.FAKE-not-a-real-secret-do-not-use-invalid` | → `401` |

```bash
# valid
curl -H "Authorization: Bearer patTwinDevFull001.FAKE-not-a-real-secret-do-not-use-full-scope" \
  localhost:8080/v0/app1MrVfxTUgJuBm0/Contacts
# invalid -> 401 {"error":{"type":"AUTHENTICATION_REQUIRED","message":"Authentication required"}}
curl -H "Authorization: Bearer nope" localhost:8080/v0/app1MrVfxTUgJuBm0/Contacts
```

## Seed data (deterministic, stable across resets)

| Base | Base ID | Tables |
|---|---|---|
| CRM | `app1MrVfxTUgJuBm0` | Contacts (`tblSopvR8A6870fpC`, 5 records) |
| Project Tracker | `appJwuyfMWjjzLTqL` | Projects (3) · Tasks (5) — bidirectional linked records |

Plus a seeded user, two tokens, 2 comments on the first Contact, and one webhook
(`achyvqFnzpkVeAs4f`) on the CRM base. IDs and timestamps are generated from seeded
counters and a fixed clock, so the **same sequence of calls after `reset` always
produces identical output** (no `uuid`/`datetime.now()`/`random` anywhere).

## API surface

The full documented Airtable public API is implemented:

| Family | Endpoints |
|---|---|
| **Records** | `GET /v0/{baseId}/{table}` (list — `fields[]`, `filterByFormula`, `sort[]`, `pageSize`/`maxRecords`/`offset`, `returnFieldsByFieldId`, `recordMetadata[]=commentCount`) · `POST …/listRecords` · `GET …/{recId}` · `POST …` (create, single/batch≤10, `typecast`) · `PATCH`/`PUT …` & `…/{recId}` (update — merge/replace, batch, upsert via `performUpsert`) · `DELETE …/{recId}` & `DELETE …?records[]=` |
| **Meta** | `GET /v0/meta/whoami` · `GET /v0/meta/bases` · `GET /v0/meta/bases/{baseId}/tables` · `POST /v0/meta/bases` · `POST`/`PATCH …/tables[/{id}]` · `POST`/`PATCH …/fields[/{id}]` |
| **Comments** | `GET`/`POST /v0/{baseId}/{table}/{recId}/comments` · `PATCH`/`DELETE …/comments/{commentId}` |
| **Webhooks** | `POST`/`GET /v0/bases/{baseId}/webhooks` · `DELETE …/{webhookId}` · `POST …/{webhookId}/refresh` · `POST …/{webhookId}/enableNotifications` · `GET …/{webhookId}/payloads` (the generated-event stream) |
| **Control** | `GET /_arga/healthz` · `GET /_arga/admin/state` · `POST /_arga/admin/reset` · `POST /_arga/admin/rate-limit` · `GET /openapi.json` (+ `/docs`) |

Error responses mirror Airtable: the dual envelope (object `{"error":{"type","message"}}`
and bare-string `{"error":"NOT_FOUND"}`), the singular `429 RATE_LIMIT_REACHED`, and the
catalog (`AUTHENTICATION_REQUIRED`, `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`,
`UNKNOWN_FIELD_NAME`, `INVALID_VALUE_FOR_COLUMN`, `INVALID_FILTER_BY_FORMULA`,
`INVALID_PAGE_SIZE_ARGUMENT`, `INVALID_OFFSET_VALUE`, `LIST_RECORDS_ITERATOR_NOT_AVAILABLE`,
`ROW_DOES_NOT_EXIST`, and more — the full set is in `twin/errors.py`).

## Example calls

```bash
B=app1MrVfxTUgJuBm0
A='Authorization: Bearer patTwinDevFull001.FAKE-not-a-real-secret-do-not-use-full-scope'

# list with filter + sort + pagination
curl -H "$A" "localhost:8080/v0/$B/Contacts?filterByFormula=%7BActive%7D%3DTRUE()&sort[0][field]=Name&pageSize=2"

# create
curl -X POST -H "$A" -H 'Content-Type: application/json' \
  -d '{"fields":{"Name":"Ada II","Email":"ada2@example.com","Active":true}}' \
  "localhost:8080/v0/$B/Contacts"

# update (partial merge) / destructive (PUT) / upsert
curl -X PATCH -H "$A" -H 'Content-Type: application/json' \
  -d '{"fields":{"Company":"Arga"}}' "localhost:8080/v0/$B/Contacts/recnrpvne9QsSB5o7"

# base schema, whoami, webhook payloads
curl -H "$A" "localhost:8080/v0/meta/bases/$B/tables"
curl -H "$A" "localhost:8080/v0/meta/whoami"
curl -H "$A" "localhost:8080/v0/bases/$B/webhooks/achyvqFnzpkVeAs4f/payloads"
```

See [twin-contract.yaml](twin-contract.yaml) for a machine-readable example set.

## Determinism & control endpoints

- `POST /_arga/admin/reset` rebuilds the seed and resets all counters/clock — repeated
  test runs are byte-identical.
- `GET /_arga/admin/state` is a debug snapshot (per-collection counts + full state).
- `POST /_arga/admin/rate-limit` `{"enabled":true,"perBase":5}` enables a deterministic,
  counter-based per-base rate limiter that then returns `429 RATE_LIMIT_REACHED` once the
  threshold is exceeded. **Off by default** so normal validation isn't disrupted; `reset`
  clears and disables it.

## Tests

```bash
uv run pytest                      # 139 in-process tests
uv run python scripts/verify.py    # black-box checks against a running container
```

`scripts/verify.py` mirrors the Arga loop (wait for health → reset → provider-shaped
requests) and exits non-zero on any failure. It targets `http://localhost:8080` by
default (override with `TWIN_BASE_URL`).

## Known gaps (deliberate)

- **`filterByFormula`** implements a well-defined subset — literals, `{Field}`/bare refs,
  comparison/arithmetic/`&`, `AND/OR/NOT/XOR/IF/SWITCH`, and ~20 text/number functions.
  Date/time, regex, array/rollup, and record-meta functions are out of scope; an unknown
  field or unparseable formula returns `422 INVALID_FILTER_BY_FORMULA`.
- **List `cellFormat=string` / `timeZone` / `userLocale`** and **`view`** filtering are
  not applied (responses use `cellFormat=json`; the seed views are plain grid views).
- **Field-type validation** is strict for `singleSelect` (with `typecast` option
  auto-creation); other types accept values leniently.
- **Comments** reuse the `data.records:*` scopes rather than Airtable's
  `data.recordComments:*`. **Webhook** `macSecretBase64` is deterministic (this is a fake).
- A few low-frequency error exacts (`400`/`413`/`500` `type`/`message`) are not enumerated
  by Airtable's docs, so the twin keeps the closest documented shape. These and the items
  above are tracked for the fidelity audit.
- No real **OAuth** flow — PAT-style bearer tokens only (no token endpoint).

## Project layout

```
app.py                 # entry: re-exports twin.api:app (keeps `app:app`)
twin/                  # implementation package (api, store, seed, errors, auth,
                       #   ids, clock, formula, events, recordutil, routers/*)
tests/                 # pytest suite
scripts/verify.py      # black-box verifier
docs/                  # AIRTABLE_SPEC.md (researched source of truth), ARCHITECTURE.md,
                       #   PLAN.md, PROGRESS.md
twin-contract.yaml     # Arga handoff contract
```
