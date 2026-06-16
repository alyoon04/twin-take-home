# Airtable Web API — Fidelity Spec (source of truth)

> **STATUS: populated by S2 research (multi-agent, 2026-06-16).** Each section was researched against the official Airtable docs with inline citations; the five highest-stakes sections were independently re-verified. **Build to this document.** Low-confidence items are flagged below and revisited in the S24 audit. **Where an `⚠ Independent verifier` note conflicts with the section draft above it, the verifier note is authoritative.**

## Coverage & confidence

| Section | Confidence | Open Qs | Independent verify |
|---|---|---|---|
| ids | high | 3 | ⚠ see corrections |
| auth | medium | 6 | ⚠ see corrections |
| errors | medium | 6 | ⚠ see corrections |
| records_write | high | 5 | — |
| records_list | high | 5 | ⚠ see corrections |
| formula | medium | 6 | — |
| meta | high | 7 | — |
| comments | medium | 7 | — |
| webhooks | high | 6 | — |
| ratelimit | medium | 5 | ⚠ see corrections |


## 1 + 3. Base URL, versioning & IDs

### Base URL & versioning

All Airtable Web API requests are made to a single host with a path-based version segment:

```
https://api.airtable.com/v0
```

- The API is versioned **in the URL path** (`/v0`), not via a header or query parameter. Every documented endpoint path begins with `/v0/` (e.g. `GET https://api.airtable.com/v0/bases/{baseId}/webhooks`). ([introduction](https://airtable.com/developers/web/api/introduction), confirmed via [list-webhooks](https://airtable.com/developers/web/api/list-webhooks))
- **`v0` is the only version that has ever existed.** There is no `v1`, and Airtable has not published a deprecation/version-negotiation scheme. ([Using Airtable's API guide](https://www.airtable.com/guides/scale/using-airtable-api))
- The API "closely follows REST semantics, uses JSON to encode objects, and relies on standard HTTP codes to signal operation outcomes." Requests must be over HTTPS. ([introduction](https://airtable.com/developers/web/api/introduction))

> **Twin note:** There is no `Api-Version` / `X-API-Version` request or response header to emulate. The version is purely the literal `/v0` path prefix. Any request whose path does not begin with `/v0/` (e.g. `/v1/...`) does not match a real Airtable route.

### ID formats (general rule)

Almost every Airtable object ID is a fixed **17-character** string: a **3-character lowercase type prefix** followed by **14 characters** drawn from the **mixed-case alphanumeric** set `[0-9A-Za-z]`. ([Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids))

> **Twin note:** The 14-character suffix is **case-sensitive and mixed-case** — real example suffixes contain both uppercase and lowercase letters and digits (e.g. `recbtRHd9o7vKZAQr`, `fldh1CQ7PXBJtLWUU`). A faithful validation regex for the standard objects is:
> `^<prefix>[0-9A-Za-z]{14}$` (total length 17).
> The docs' webhook placeholders like `ach00000000000000` are illustrative zero-padded forms; real webhook IDs follow the same mixed-case pattern (e.g. `achA8ctcRcIw0XsRi`).

### Per-object prefixes (the set this spec needs)

| Object | Prefix | Total length | Char set | Verbatim example (from official docs) | Source |
|---|---|---|---|---|---|
| Base | `app` | 17 | `app` + 14× `[0-9A-Za-z]` | `appeqX9XTkHZNfSbn` | [Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids) |
| Table | `tbl` | 17 | `tbl` + 14× `[0-9A-Za-z]` | `tbl99vKzVh7NwLwm8` | [Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids) |
| Field | `fld` | 17 | `fld` + 14× `[0-9A-Za-z]` | `fldh1CQ7PXBJtLWUU` | [Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids) |
| View | `viw` | 17 | `viw` + 14× `[0-9A-Za-z]` | `viwQpsuEDqHFqegkp` | [list-views](https://airtable.com/developers/web/api/list-views) |
| Record | `rec` | 17 | `rec` + 14× `[0-9A-Za-z]` | `recbtRHd9o7vKZAQr` | [Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids) |
| User / collaborator | `usr` | 17 | `usr` + 14× `[0-9A-Za-z]` | `usrL2PNC5o3H4lBEi` | [list-comments](https://airtable.com/developers/web/api/list-comments) |
| Comment | `com` | 17 | `com` + 14× `[0-9A-Za-z]` | `comB5z37Mg9zaEPw6` | [list-comments](https://airtable.com/developers/web/api/list-comments) |
| Webhook | `ach` | 17 | `ach` + 14× `[0-9A-Za-z]` | `achA8ctcRcIw0XsRi` | [list-webhooks](https://airtable.com/developers/web/api/list-webhooks), [Rollout integration guide](https://rollout.com/integration-guides/airtable/quick-guide-to-implementing-webhooks-in-airtable) |

### Additional prefixes (not required, documented for completeness)

These appear on the same official [Finding Airtable IDs](https://support.airtable.com/docs/finding-airtable-ids) page and are mostly **not 17 characters**, so they are useful as a caution that "17 chars" is the common case, not a universal invariant:

| Object | Prefix | Total length | Verbatim example |
|---|---|---|---|
| Interface page | `pag` | 17 | `pagIk60ZUF9P5UP72` |
| Workspace | `wsp` | 18 | `wspqrdtEQXErvBMXXU` |
| User group | `ugp` | 17 | `ugpDUHUnftA7H9bG8` |
| Data set | `pds` | 15 | `pdsJhMGPUJgBNKc` |
| Org unit / enterprise | `ent` | 17 | `entSyVgzzNKssX72X` |
| Interface (admin / `pbd`) | `pbd` | 16 | `pbdxBwNfbZXGVkoK` |

> **Twin note:** For the objects this twin actually serves (base/table/field/view/record/user/comment/webhook) treat 17 chars as authoritative. Do **not** generalize "17" to workspace/data-set/interface IDs if those are ever added — their lengths differ (15–18).


**⚠ Independent verifier (DISAGREES — apply these corrections):**

VERDICT: The draft's substantive claims (base URL, path versioning, ID prefixes/examples) are CONFIRMED and accurate. I set agrees=false because the verification scope explicitly required confirming the error-envelope shape, HTTP status codes, response headers, and documented limits — and the draft section is SILENT on all of these, while the official errors page reveals a load-bearing nuance (two distinct error-body shapes) that any high-fidelity twin MUST reproduce. Plus two minor over-claims in the ID text. Corrections below; everything else in the draft can stand as written.

=== CONFIRMED (no change needed) ===

1. Base URL & path versioning. CONFIRMED. The host is `https://api.airtable.com` and every endpoint path begins with `/v0/` (e.g. `https://api.airtable.com/v0/{baseId}/{tableIdOrName}`). Versioning is purely the literal `/v0` path segment — no version header or query param. Source: https://airtable.com/developers/web/api/introduction and the canonical pattern shown across endpoints e.g. https://airtable.com/developers/web/api/list-records

2. REST/JSON/HTTP-codes statement. CONFIRMED VERBATIM: "The API closely follows REST semantics, uses JSON to encode objects, and relies on standard HTTP codes to signal operation outcomes." Source: https://airtable.com/developers/web/api/introduction

3. ID prefixes + verbatim examples. CONFIRMED against the official support page. app `appeqX9XTkHZNfSbn` (17), tbl `tbl99vKzVh7NwLwm8` (17), fld `fldh1CQ7PXBJtLWUU` (17), rec `recbtRHd9o7vKZAQr` (17), wsp `wspqrdtEQXErvBMXXU` (18), pag `pagIk60ZUF9P5UP72` (17), ugp `ugpDUHUnftA7H9bG8` (17), pds `pdsJhMGPUJgBNKc` (15), ent `entSyVgzzNKssX72X` (17), pbd `pbdxBwNfbZXGVkoK` (16). All match. Source: https://support.airtable.com/docs/finding-airtable-ids . NOTE: the `viw`/`usr`/`com`/`ach` examples and the case-sensitivity/mixed-case observation are reasonable but are NOT on that support page — see correction (C) below.

=== CORRECTIONS / REQUIRED ADDITIONS ===

(A) CRITICAL — The error envelope is NOT a single shape; document BOTH. The official errors page shows TWO distinct response-body forms, and a faithful twin must emit both:
  - Bare-string form: `{"error":"NOT_FOUND"}`  (value is a plain string, no nesting)
  - Object form: `{"error":{"type":"<TYPE>","message":"<human-readable>"}}`
The SAME 404 condition is documented with BOTH `{"error":"NOT_FOUND"}` AND `{"error":{"type":"NOT_FOUND"}}` shown side by side. So the twin cannot assume the object envelope universally. Verbatim examples from the docs:
  - 403: `{"error":{"type":"INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND","message":"Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct."}}`
  - 404: `{"error":"NOT_FOUND"}` and also `{"error":{"type":"NOT_FOUND"}}`
  - 422: `{"error":{"type":"INVALID_REQUEST_UNKNOWN","message":"..."}}`
  - 429: `{"error":{"type":"RATE_LIMIT_REACHED","message":"..."}}`
Source: https://airtable.com/developers/web/api/errors (cross-confirmed message text via https://community.airtable.com/development-apis-11/invalid-permissions-or-model-not-found-error-3982 )

(B) ADD — HTTP status codes table (in scope, omitted by draft). Per the official errors page, verbatim short descriptions:
  - 200 OK — "Request completed successfully."
  - 400 Bad Request — "The request encoding is invalid; the request can't be parsed as a valid JSON."
  - 401 Unauthorized — "Accessing a protected resource without authorization or with invalid credentials."
  - 403 Forbidden — "Accessing a protected resource with API credentials that don't have access to that resource."  (type: INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND)
  - 404 Not Found — "Route or resource is not found."  (type: NOT_FOUND; also bare-string form)
  - 413 Request Entity Too Large — "The request exceeded the maximum allowed payload size."
  - 422 Invalid Request — "The request data is invalid."  (type: INVALID_REQUEST_UNKNOWN, among others)
  - 429 Too Many Requests — rate limit; (type: RATE_LIMIT_REACHED)
  - 500 Internal Server Error — "The server encountered an unexpected condition."
  - 502 Bad Gateway — "Airtable's servers are restarting or an unexpected outage is in progress."
  - 503 Service Unavailable — "The server could not process your request in time."  (may include a `Retry-After` response header)
Source: https://airtable.com/developers/web/api/errors

(C) MINOR over-claim in ID section — two parts:
  - (c1) Citations for `viw`/`usr`/`com`/`ach`: The official "Finding Airtable IDs" support page (the cited source) lists only app/tbl/fld/rec + workspace/interface/usergroup/dataset/orgunit/interface-admin. It does NOT contain `viw`, `usr`, `com`, or `ach`. Those four examples come from API endpoint pages (list-views, list-comments, list-webhooks), not from finding-airtable-ids. The draft already cites those pages for them, which is fine — but do NOT attribute them to finding-airtable-ids. The prefixes themselves are real and correct.
  - (c2) "case-sensitive and mixed-case" and the regex `[0-9A-Za-z]{14}`: This is an empirically reasonable inference (the verbatim examples do contain mixed case + digits), but Airtable does NOT document a character set or a length guarantee anywhere I could confirm — the support page explicitly does not state length or charset constraints. Label this as an OBSERVED pattern / twin-implementation heuristic, not a documented Airtable invariant. (This strengthens the draft's own "17 is the common case, not a universal invariant" caution — good — but the charset claim deserves the same hedge.)

(D) ADD (optional, but in scope for "documented limits") — URL length limit: "Requests to Airtable's Web API are limited to a 16,000-character URL length." The status code returned on exceed is NOT documented (community reports point to 422 INVALID_REQUEST, unconfirmed officially — see open question). Source: https://support.airtable.com/docs/enforcement-of-url-length-limit-for-web-api-requests

=== OPEN QUESTIONS (do not invent) ===
  - Rate limit number: the official ERRORS page text rendered as "The API is limited to 5 requests per second per base" with a 30-second cooldown, whereas Airtable's widely-cited rate-limits page states 5 req/sec/base as well — but some third-party docs cite different figures. Confirm against https://airtable.com/developers/web/api/rate-limits before pinning the exact number and the exact `Retry-After` value in the twin. (Out of strict scope for section 1+3, but flagged since "documented limits" was requested.)
  - Exact status code for the 16,000-char URL-length violation is undocumented officially (likely 422, unconfirmed).
  - Whether the bare-string `{"error":"STRING"}` form is emitted by current production for routes the twin serves, vs. being a legacy/edge artifact — the docs show it but don't scope it. The twin should be able to PARSE/emit both; exact triggering conditions are not fully documented.


**Sources:** https://airtable.com/developers/web/api/introduction · https://support.airtable.com/docs/finding-airtable-ids · https://airtable.com/developers/web/api/list-views · https://airtable.com/developers/web/api/list-comments · https://airtable.com/developers/web/api/list-webhooks · https://www.airtable.com/guides/scale/using-airtable-api · https://rollout.com/integration-guides/airtable/quick-guide-to-implementing-webhooks-in-airtable


## 2. Auth & scopes

### 2.1 Transport & token presentation

- All API requests MUST be authenticated and made over HTTPS. ([authentication](https://airtable.com/developers/web/api/authentication))
- Authentication is **bearer-token only**, passed in the HTTP `Authorization` header. The legacy `api_key` URL query parameter is **no longer supported**, and legacy user API keys were fully disabled on **Feb 1, 2024**. ([authentication](https://airtable.com/developers/web/api/authentication); [api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))
- Exact header shape (note: scheme is `Bearer`, capital B; "Basic" auth is rejected):

  ```
  Authorization: Bearer YOUR_TOKEN
  ```

  ([authentication](https://airtable.com/developers/web/api/authentication); [api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

### 2.2 Token types & formats

Two token types are accepted on the same `Authorization: Bearer` header; the API does not require the caller to declare which type it is. ([authentication](https://airtable.com/developers/web/api/authentication))

| Token type | Format | Notes |
|---|---|---|
| Personal access token (PAT) | String beginning with the literal prefix **`pat`** followed by a long alphanumeric body. The "Token ID" shown in the UI is the **first 14 characters** of the PAT (e.g. `pat` + 11 chars); the full secret is longer (community-reported full length ~82 chars). | Acts as the creating user's account; not for sharing with third parties. Managed at `/create/tokens`. ([authentication](https://airtable.com/developers/web/api/authentication); [token format discussion](https://community.airtable.com/development-apis-11/personal-access-tokens-power-automate-connector-3704)) |
| OAuth 2.0 access token | **Opaque, variable-length string** — docs explicitly say "do not rely on tokens having a particular length or format". No documented prefix. | Access token **expires after 60 minutes**; refresh token valid **60 days** (revoked if unused in that window). Obtained via the OAuth grant flow; app registered at `/create/oauth`. ([oauth-reference](https://airtable.com/developers/web/api/oauth-reference)) |

> Twin guidance: For PATs, validate the `pat` prefix; for OAuth tokens treat as opaque (any value your fake issuer minted). Do **not** synthesize an OAuth prefix — there is none in the spec.

### 2.3 Permission model (two independent dimensions)

A token is authorized along **two** axes; failing either is the usual cause of 401/403: ([authentication](https://airtable.com/developers/web/api/authentication); [api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

1. **Scopes** — what actions the token may perform (e.g. `data.records:write`).
2. **Resources / access** — which bases & workspaces the token may touch.

Additionally, the **underlying user** must independently have sufficient collaborator permission on the resource (e.g. editor access to update a record), even if the token's scope/resource grants allow it. ([authentication](https://airtable.com/developers/web/api/authentication))

### 2.4 OAuth scopes (full list, verbatim descriptions)

Source for all rows: [scopes](https://airtable.com/developers/web/api/scopes).

**Standard scopes**

| Scope | Description |
|---|---|
| `data.records:read` | See the data in records |
| `data.records:write` | Create, edit, and delete records |
| `data.recordComments:read` | See comments in records |
| `data.recordComments:write` | Create, edit, and delete record comments |
| `schema.bases:read` | See the structure of a base, like table names or field types |
| `schema.bases:write` | Edit the structure of a base, like adding new fields or tables |
| `workspacesAndBases:read` | View metadata about workspaces, bases, and views |
| `webhook:manage` | View, create, delete webhooks for a base, as well as fetch webhook payloads |
| `block:manage` | Create new releases and submissions for custom extensions via the Blocks CLI |
| `user.email:read` | See the user's email address |

**Enterprise member scopes**

| Scope | Description |
|---|---|
| `enterprise.groups:read` | View information about user groups under the enterprise |
| `workspacesAndBases:write` | Edit metadata of workspaces and bases, including collaborators |
| `workspacesAndBases.shares:manage` | View, enable, disable and delete share links for bases |

**Enterprise admin scopes**

| Scope | Description |
|---|---|
| `enterprise.scim.usersAndGroups:manage` | Manage users and groups via SCIM APIs |
| `enterprise.auditLogs:read` | View the organization's audit logs |
| `enterprise.changeEvents:read` | View the organization's change events |
| `enterprise.exports:manage` | Manage data exports, including eDiscovery exports |
| `enterprise.account:read` | View data about the enterprise account |
| `enterprise.account:write` | Edit data about the enterprise account |
| `enterprise.user:read` | View account information of users under the enterprise |
| `enterprise.user:write` | Manage users under the enterprise account |
| `enterprise.groups:manage` | Manage user groups under the enterprise |
| `workspacesAndBases:manage` | Manage workspaces and bases under the enterprise |
| `hyperDB.records:read` | Read records in the user's HyperDB tables |
| `hyperDB.records:write` | Write records to the user's HyperDB tables |

> Note: PATs can be granted any of the standard scopes from the same picker; enterprise scopes require an enterprise account. The data API endpoints the twin most likely serves need `data.records:read` / `data.records:write` (+ often `schema.bases:read`).

### 2.5 Failure responses — EXACT status + body

All API error bodies use the envelope `{ "error": { "type": ..., "message": ... } }`, with `type` an **UPPER_SNAKE_CASE** string. The standard error `Content-Type` is `application/json`. No `WWW-Authenticate` response header is documented. ([errors](https://airtable.com/developers/web/api/errors))

**(a) Missing `Authorization` header → `401 Unauthorized`**

```json
{
  "error": {
    "type": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

The access token was not present in the request, or was passed incorrectly (e.g. wrong scheme such as Basic, or only the 14-char Token ID instead of the full secret). ([api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting); error body confirmed against [airtable-mcp-server enhanceAirtableError.test.ts](https://raw.githubusercontent.com/domdomegg/airtable-mcp-server/master/src/enhanceAirtableError.test.ts))

**(b) Malformed / invalid / revoked / expired token → `401 Unauthorized`**

Same status, type, and message as (a) — the observed body is identical:

```json
{
  "error": {
    "type": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

Triggered when the supplied token is invalid, expired, or revoked (incl. PAT whose creating user was deleted/deactivated or lost base access; OAuth access token past its 60-min expiry). ([api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting); [oauth-reference](https://airtable.com/developers/web/api/oauth-reference))

> Twin guidance: cases (a) and (b) are **indistinguishable** in the response — a valid-looking-but-unknown token, a garbage token, and no token all yield the exact same `401 AUTHENTICATION_REQUIRED` / "Authentication required" body. The prose distinction ("not present" vs "invalid") is only in support docs, not in the JSON.

**(c) Valid token but insufficient scope / permission (or resource not granted) → `403 Forbidden`**

```json
{
  "error": {
    "type": "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND",
    "message": "Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct."
  }
}
```

Returned when the token authenticates fine but lacks the required **scope** (e.g. write attempted without `data.records:write`), lacks **resource access** (base/workspace not granted to the token), or the **user** lacks the needed collaborator permission. Airtable deliberately conflates "no permission" and "model not found" into this single 403 type so callers cannot probe for the existence of bases/tables they cannot access. A related `INVALID_PERMISSIONS` type also appears for specific record/field-level permission denials. ([errors](https://airtable.com/developers/web/api/errors); [api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

**Key differences among (a)/(b)/(c)**

| Case | Status | `error.type` | `error.message` |
|---|---|---|---|
| Missing header | `401` | `AUTHENTICATION_REQUIRED` | `Authentication required` |
| Malformed/invalid/expired token | `401` | `AUTHENTICATION_REQUIRED` | `Authentication required` |
| Authenticated but no scope/permission/resource | `403` | `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` | `Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct.` |

So the **only** observable boundary is 401 (authentication failed — token absent or unrecognized) vs 403 (token recognized, but not allowed). (a) and (b) are byte-identical.

### 2.6 OAuth token-endpoint errors (distinct from the data API)

The OAuth **token endpoint** (`/oauth2/v1/token`) does **not** use the UPPER_SNAKE_CASE envelope. It follows RFC 6749 with `{ "error": ..., "error_description": ... }` and lowercase error codes: ([oauth-reference](https://airtable.com/developers/web/api/oauth-reference))

- `error: "invalid_client"` → **`401`**
- all other error values (e.g. `invalid_grant`, `invalid_request`) → **`400`**

The token endpoint authenticates the client with HTTP **Basic** auth (`Authorization: Basic {base64url(client_id:client_secret)}`), unlike the bearer-token data API. ([oauth-reference](https://airtable.com/developers/web/api/oauth-reference))

> Twin guidance: keep two distinct error formats — UPPER_SNAKE_CASE `{error:{type,message}}` for the data/metadata API, and RFC 6749 `{error,error_description}` for the OAuth token endpoint.


**⚠ Independent verifier (DISAGREES — apply these corrections):**

I re-fetched the official docs independently. The draft is ~90% correct, but has one load-bearing error (the error-envelope shape claim), three scope-description errors, and a couple of items stated as fact that are only community-sourced. Corrections below; everything not listed was confirmed verbatim against the official pages.

=== CORRECTION 1 (IMPORTANT — error-envelope shape) ===
Draft 2.5 states: "All API error bodies use the envelope `{ "error": { "type": ..., "message": ... } }`." This is WRONG as an absolute. The official errors page documents BOTH shapes:
- Object-with-message: `{"error":{"type":"RETRIABLE_ERROR","message":"Server encountered an error while processing your request, and it is safe to retry the request"}}` (503), and similarly 403/422/429.
- Bare/short form WITHOUT a message: `404 NOT_FOUND` is documented as `{"error": "NOT_FOUND"}` AND as `{"error": {"type": "NOT_FOUND"}}` — i.e. a bare string is a valid documented shape, and the object form for NOT_FOUND carries NO `message` field.
Source: https://airtable.com/developers/web/api/errors
Twin impact: a high-fidelity twin must NOT always emit `{error:{type,message}}`. For NOT_FOUND specifically it should emit the message-less object `{"error":{"type":"NOT_FOUND"}}` (the form returned in practice and confirmed by the support doc), and be aware the bare-string `{"error":"NOT_FOUND"}` form is also documented. The blanket "all error bodies use {type,message}" sentence should be deleted/qualified. (The 401 and 403 auth bodies the section focuses on DO use the full {type,message} object — that part is fine.)

=== CORRECTION 2 (scope descriptions — must be verbatim) ===
Source for all three: https://airtable.com/developers/web/api/scopes
- `workspacesAndBases:read` — Draft: "View metadata about workspaces, bases, and views". CORRECT: "View metadata about workspaces, bases, and views including collaborators".
- `workspacesAndBases:write` — Draft: "Edit metadata of workspaces and bases, including collaborators". CORRECT (fuller): "Edit metadata of workspaces and bases, including collaborators, invites, views, and extensions".
- `enterprise.groups:read` — Draft: "View information about user groups under the enterprise". CORRECT (fuller): "View information about user groups under the enterprise, their access, and their members".
(Also note `enterprise.groups:manage` full text is "Manage user groups under the enterprise, including moving them" — draft's "Manage user groups under the enterprise" is a truncation but harmless.) All OTHER scope rows match the official page verbatim and are confirmed.

=== CORRECTION 3 (provenance of the 401 message) ===
The exact 401 body `{"error":{"type":"AUTHENTICATION_REQUIRED","message":"Authentication required"}}` is NOT shown on the official errors page (that page lists 401 only as a status with prose "Accessing a protected resource without authorization or with invalid credentials", no JSON). The `"Authentication required"` string is confirmed via the cited third-party MCP fixture (https://raw.githubusercontent.com/domdomegg/airtable-mcp-server/master/src/enhanceAirtableError.test.ts) and community reports, plus the support doc's prose. Treat it as high-confidence-but-not-primary, not as a documented official body. The draft's footnote citing the MCP test is good; just don't imply it comes from airtable.com/.../errors.

=== CORRECTION 4 (PAT format stated as fact, but unverified) ===
2.2's PAT row asserts "Token ID = first 14 characters", "pat + 11 chars", and "full length ~82 chars". None of this is in any official Airtable doc — the official authentication/oauth pages never document PAT length or internal structure. These are community-reported only. Recommend: keep "starts with literal prefix `pat`" (this is widely observed) but move the 14-char / 82-char / 11-char specifics to OPEN QUESTIONS, or clearly label them "community-reported, not documented." A twin should accept a `pat`-prefixed string but should not enforce a specific length.

=== CONFIRMED CORRECT (no change needed) ===
- 401 vs 403 boundary, and (a)/(b) being indistinguishable: CONFIRMED. The support doc (https://support.airtable.com/docs/airtable-api-common-troubleshooting) does carry the prose distinction "The access token was not present in the request, or it was passed incorrectly" (missing) vs "The access token that was provided is invalid" (invalid), and explicitly says to use Bearer "rather than basic" — matching the draft. Good.
- 403 `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` exact message and the separate `INVALID_PERMISSIONS` type ("You are not permitted to..."): CONFIRMED verbatim on the errors page.
- Two-axis permission model (scopes + resources + underlying-user collaborator permission) incl. the `data.records:write` editor example: CONFIRMED verbatim on the authentication page.
- `Authorization: Bearer`, Basic rejected, `api_key` query param unsupported, Feb 1 2024 key disablement, HTTPS-only: ALL CONFIRMED.
- OAuth section 2.6: 60-min access token, 60-day refresh, endpoint `https://airtable.com/oauth2/v1/token`, client auth via `Basic {base64url(client_id:client_secret)}`, RFC 6749 `{error,error_description}` with `invalid_client`→401 and all other codes→400, and the "treat tokens as opaque, variable-length; do not rely on length or format" statement: ALL CONFIRMED verbatim on the oauth-reference page.
- No `WWW-Authenticate` header is documented: CONFIRMED (none appears anywhere in the official auth/errors pages); standard error Content-Type application/json is consistent with all documented examples.

Net: set agrees=false primarily for Correction 1 (envelope shape) and Correction 2 (scope text), which directly affect twin fidelity.


**Sources:** https://airtable.com/developers/web/api/authentication · https://airtable.com/developers/web/api/scopes · https://airtable.com/developers/web/api/errors · https://airtable.com/developers/web/api/oauth-reference · https://support.airtable.com/docs/airtable-api-common-troubleshooting · https://raw.githubusercontent.com/domdomegg/airtable-mcp-server/master/src/enhanceAirtableError.test.ts · https://community.airtable.com/development-apis-11/personal-access-tokens-power-automate-connector-3704


## 4. Error model & catalog

### 4.1 Two error envelope forms

The Airtable Web API returns errors in **two distinct JSON shapes**. A faithful twin must emit the correct shape per status code, because real clients (and Airtable's own docs) treat them differently.

**A. Object form** — `error` is an object with `type` and `message`:

```json
{
  "error": {
    "type": "ERROR_TYPE_STRING",
    "message": "Human-readable description"
  }
}
```

**B. Bare-string form** — `error` is just a string (no `type`/`message`):

```json
{
  "error": "NOT_FOUND"
}
```

The official errors reference shows the **bare-string form is used for `404 Not Found`** (it documents `404 Not Found` → `{ "error": "NOT_FOUND" }`), while **403, 422, 429, and 503 use the object form** ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)). This split is the single most important fidelity detail in this section.

Notes / caveats:
- For a plain 404 (wrong/unknown base, table, or record path on the data API), the body is the **bare string** `{"error": "NOT_FOUND"}` ([official errors page](https://airtable.com/developers/web/api/errors); corroborated by [community thread on a `tbl…` used as base id returning NOT_FOUND](https://community.airtable.com/t5/development-apis/api-response-quot-not-found-quot/td-p/82528)).
- However, **some 404s from the API are observed in the object form** with a `type` such as `MODEL_ID_NOT_FOUND` (e.g. a deleted table), e.g. `{"error":{"type":"MODEL_ID_NOT_FOUND","message":"Table not found"}}` ([miniExtensions, quoting a real 404 body](https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found)). So 404 is not exclusively bare-string in practice; see open questions for the exact trigger boundary.
- A `null` error value (`{"error": null}`) and an error object missing `type` or `message` have both been seen as edge cases that clients defensively parse ([airtable-mcp-server test fixtures](https://github.com/domdomegg/airtable-mcp-server/blob/master/src/enhanceAirtableError.test.ts)); these are not first-class documented forms and a twin need not normally emit them.

### 4.2 Catalog by HTTP status

Unless noted, bodies below are the **object form**. The official errors page only enumerates a small canonical set (`NOT_FOUND` 404, `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` 403, `INVALID_PERMISSIONS` 403, `INVALID_REQUEST_UNKNOWN` 422, `RATE_LIMIT_REACHED` 429, `RETRIABLE_ERROR` 503) ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)); the additional `type` strings (e.g. `INVALID_REQUEST_MISSING_FIELDS`, `UNKNOWN_FIELD_NAME`, `INVALID_VALUE_FOR_COLUMN`, `MODEL_ID_NOT_FOUND`, `TABLE_NOT_FOUND`) are **not** in the official enumeration but are well-attested from real API responses (sourced inline). Confidence on those exact strings is therefore medium.

#### 400 Bad Request
Returned when the request cannot be parsed (e.g. malformed JSON). Object form ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors); [support.airtable.com troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting)).

```json
{
  "error": {
    "type": "INVALID_REQUEST_UNKNOWN",
    "message": "Could not parse request body"
  }
}
```
(Exact `type`/`message` for 400 is not enumerated in the official docs — see open questions.)

#### 401 Unauthorized
Token missing, malformed, or invalid. Object form. The attested `type` is `AUTHENTICATION_REQUIRED` with message `"Authentication required"` ([airtable-mcp-server test fixtures showing `{"error":{"type":"AUTHENTICATION_REQUIRED","message":"Authentication required"}}`](https://github.com/domdomegg/airtable-mcp-server/blob/master/src/enhanceAirtableError.test.ts); behavior described in [support.airtable.com troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting)).

```json
{
  "error": {
    "type": "AUTHENTICATION_REQUIRED",
    "message": "Authentication required"
  }
}
```

#### 403 Forbidden
Authenticated but not permitted, OR the model exists but the caller can't see it (Airtable deliberately conflates "no permission" and "not found" here to avoid leaking existence). Two attested types ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors); [community](https://community.airtable.com/development-apis-11/invalid-permissions-or-model-not-found-error-3982)):

`INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`:
```json
{
  "error": {
    "type": "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND",
    "message": "Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct."
  }
}
```

`INVALID_PERMISSIONS`:
```json
{
  "error": {
    "type": "INVALID_PERMISSIONS",
    "message": "You are not permitted to perform this operation"
  }
}
```

#### 404 Not Found
**Bare-string form** for the generic case ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)):
```json
{ "error": "NOT_FOUND" }
```
Object-form 404 also occurs for specific model-resolution failures (e.g. deleted table), e.g. ([miniExtensions](https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found)):
```json
{ "error": { "type": "MODEL_ID_NOT_FOUND", "message": "Table not found" } }
```
Other attested object-form 404 messages: `{"error":{"type":"MODEL_ID_NOT_FOUND","message":"Base not found"}}`, and `TABLE_NOT_FOUND` for a bad table pointer ([miniExtensions / community](https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found)).

#### 413 Payload Too Large
Request body exceeds the maximum allowed size. Object form ([support.airtable.com troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting); [airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)). Exact `type`/`message` not enumerated in official docs — best-known shape:
```json
{
  "error": {
    "type": "REQUEST_TOO_LARGE",
    "message": "Request too large"
  }
}
```
(See open questions — `REQUEST_TOO_LARGE` string is not officially confirmed.)

#### 422 Unprocessable Entity
The most varied status: request is well-formed but semantically invalid. Object form. Official enumerated type is `INVALID_REQUEST_UNKNOWN` ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)); the field/value-specific types below are attested from real responses.

`INVALID_REQUEST_UNKNOWN` (generic validation failure / parameter validation) ([official](https://airtable.com/developers/web/api/errors)):
```json
{
  "error": {
    "type": "INVALID_REQUEST_UNKNOWN",
    "message": "Invalid request: parameter validation failed. Check your request data."
  }
}
```

`INVALID_REQUEST_MISSING_FIELDS` — top-level `fields` object missing from the body ([community 422 thread](https://community.airtable.com/development-apis-11/error-code-422-invalid-request-missing-fields-4535)):
```json
{
  "error": {
    "type": "INVALID_REQUEST_MISSING_FIELDS",
    "message": "Could not find field \"fields\" in the request body"
  }
}
```

`UNKNOWN_FIELD_NAME` — a referenced field does not exist on the table ([community](https://community.airtable.com/t5/development-apis/api-unknown-field-name-error-422/td-p/27792)):
```json
{
  "error": {
    "type": "UNKNOWN_FIELD_NAME",
    "message": "Could not find a field named Payment_Type"
  }
}
```

`INVALID_VALUE_FOR_COLUMN` — value not valid for the field type (e.g. not an existing select option, or unparseable) ([community Invalid_value_for_column thread](https://community.airtable.com/fid-11/tid-7170)):
```json
{
  "error": {
    "type": "INVALID_VALUE_FOR_COLUMN",
    "message": "Field Cancel can not accept value 123"
  }
}
```
Another attested message for the same type:
```json
{
  "error": {
    "type": "INVALID_VALUE_FOR_COLUMN",
    "message": "Cannot parse value \"[object Object]\" for field Rep"
  }
}
```

#### 429 Too Many Requests
Rate limit exceeded (the documented limit is **5 requests/second/base**). Object form. Official verbatim body ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)):
```json
{
  "error": {
    "type": "RATE_LIMIT_REACHED",
    "message": "Rate limit exceeded. Please try again later"
  }
}
```
A separate plan-level cap is attested as `PUBLIC_API_BILLING_LIMIT_EXCEEDED` ("Exceeded your plan's API call limit"), also 429 ([support.airtable.com troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting)).

#### 500 Internal Server Error
Unexpected server condition. Object form; exact `type`/`message` not enumerated officially ([support.airtable.com troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting)):
```json
{
  "error": {
    "type": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred"
  }
}
```
(`type` string unconfirmed — see open questions.)

#### 503 Service Unavailable
Transient; safe to retry with backoff. Object form, type `RETRIABLE_ERROR` ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)):
```json
{
  "error": {
    "type": "RETRIABLE_ERROR",
    "message": "Server encountered an error. It is safe to retry the request."
  }
}
```

### 4.3 Relevant response headers

- **`Retry-After`** — may be provided on `503` responses to indicate when to retry ([airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors)). (Not documented as present on 429, despite that being where it is most commonly expected — see open questions.)
- All error bodies are `Content-Type: application/json` (implied; the bare-string 404 is still valid JSON).

### 4.4 Twin implementation summary

| Status | Envelope | Canonical `type`(s) |
|---|---|---|
| 400 | object | `INVALID_REQUEST_UNKNOWN` (unconfirmed exact) |
| 401 | object | `AUTHENTICATION_REQUIRED` |
| 403 | object | `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`, `INVALID_PERMISSIONS` |
| 404 | **bare string** (generic); object for specific model failures | `"NOT_FOUND"` (string); `MODEL_ID_NOT_FOUND` / `TABLE_NOT_FOUND` (object) |
| 413 | object | `REQUEST_TOO_LARGE` (unconfirmed) |
| 422 | object | `INVALID_REQUEST_UNKNOWN`, `INVALID_REQUEST_MISSING_FIELDS`, `UNKNOWN_FIELD_NAME`, `INVALID_VALUE_FOR_COLUMN` |
| 429 | object | `RATE_LIMIT_REACHED` (and `PUBLIC_API_BILLING_LIMIT_EXCEEDED`) |
| 500 | object | `INTERNAL_SERVER_ERROR` (unconfirmed) |
| 503 | object | `RETRIABLE_ERROR` |

Sources: official enumeration and verbatim 404/429/503 bodies from [airtable.com/developers/web/api/errors](https://airtable.com/developers/web/api/errors); message strings and additional `type`s corroborated by [support.airtable.com/docs/airtable-api-common-troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting), [miniExtensions](https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found), the [airtable-mcp-server test fixtures](https://github.com/domdomegg/airtable-mcp-server/blob/master/src/enhanceAirtableError.test.ts), and Airtable community threads cited inline.


**⚠ Independent verifier (DISAGREES — apply these corrections):**

I re-fetched the official errors page (https://airtable.com/developers/web/api/errors), the support troubleshooting page (https://support.airtable.com/docs/airtable-api-common-troubleshooting), and the API-call-limits page (https://support.airtable.com/docs/managing-api-call-limits-in-airtable). The draft is mostly sound on envelope shapes and the 403/429 bodies, but it has several factual errors and one important structural omission. Set agrees=false. Corrections below, ordered by importance.

### CRITICAL CORRECTION 1 — 503 message string is wrong
The draft's 503 body says: "Server encountered an error. It is safe to retry the request." That is NOT the real wording. The official verbatim message is:
  "Server encountered an error while processing your request, and it is safe to retry the request"
(no period mid-string; single clause joined by ", and"). Confirmed on the official errors page and corroborated independently. A high-fidelity twin must emit this exact string. Source: https://airtable.com/developers/web/api/errors (verbatim 503 message); corroborated https://docs.miniextensions.com/en/articles/5025831 and community 503 reports.
Correct body:
  {"error": {"type": "RETRIABLE_ERROR", "message": "Server encountered an error while processing your request, and it is safe to retry the request"}}

### CRITICAL CORRECTION 2 — the 404 object form is OFFICIAL with type "NOT_FOUND", not just a third-party MODEL_ID_NOT_FOUND quirk
The draft frames 404 as "bare string {\"error\":\"NOT_FOUND\"} officially; object form only seen via third-party MODEL_ID_NOT_FOUND". That mis-states the official docs. The official errors page itself shows 404 in BOTH forms:
  {"error": "NOT_FOUND"}              (bare string)
  {"error": {"type": "NOT_FOUND"}}    (object, type only, no message)
So the canonical object-form 404 uses type "NOT_FOUND" (and frequently no "message" field at all), per Airtable's own page — this is the form a twin should prefer for the object-shaped 404, NOT MODEL_ID_NOT_FOUND. Source: https://airtable.com/developers/web/api/errors (both 404 examples shown).
MODEL_ID_NOT_FOUND / TABLE_NOT_FOUND with a "message" ("Table not found", "Base not found") are real but are third-party-attested (miniExtensions, community), and Airtable acknowledged the 404 shape as inconsistent/buggy. Keep them as "also observed", but they are NOT the documented canonical form. Sources: https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found and https://community.airtable.com/t5/development-apis/api-404-inconsistency/td-p/134432 (Airtable staff acknowledged the inconsistency as a bug).

### CORRECTION 3 — 422 catalog: the official page documents MORE types than the draft credits, and some draft type names are not the official ones
The draft says the official page "only enumerates INVALID_REQUEST_UNKNOWN" for 422 and treats INVALID_REQUEST_MISSING_FIELDS / UNKNOWN_FIELD_NAME / INVALID_VALUE_FOR_COLUMN as purely third-party. Re-reading the official errors + troubleshooting pages, 422 is documented with several scenarios/types beyond INVALID_REQUEST_UNKNOWN, including invalid request body, an invalid-multiple-choice-options case (select option that does not yet exist, when typecast is not used / lacking creator permission), and a FAILED_STATE_CHECK case ("values and/or parameters in the endpoint path have been mismatched"). Only INVALID_REQUEST_UNKNOWN appears inside the JSON example block; the others appear as documented prose/cases. Sources: https://airtable.com/developers/web/api/errors and https://support.airtable.com/docs/airtable-api-common-troubleshooting.
Net: the draft's INVALID_REQUEST_MISSING_FIELDS, UNKNOWN_FIELD_NAME, INVALID_VALUE_FOR_COLUMN are still legitimately community-attested from real responses and fine to keep, but the claim "official only lists INVALID_REQUEST_UNKNOWN" understates the official page, and the twin should also handle FAILED_STATE_CHECK (422) which the draft omits entirely.

### CORRECTION 4 — 429: confirm type/message, but the draft omits documented limits
- type "RATE_LIMIT_REACHED" and message "Rate limit exceeded. Please try again later" are CORRECT and independently confirmed. Sources: https://airtable.com/developers/web/api/errors and https://docs.miniextensions.com/en/articles/7977226-429-errors-error-rate_limit_reached-message-rate-limit-exceeded-please-try-again-later.
- Note: miniExtensions shows a batch/array-wrapped variant {"errors":[{"error":"RATE_LIMIT_REACHED","message":"..."}]}; the canonical single-error body matches the draft.
- DOCUMENTED LIMITS the draft is missing/under-specifies: besides "5 requests/second/base", Airtable also documents "50 requests per second" for all traffic using personal access tokens from a given user/service account, and a fixed "wait 30 seconds" after a 429. Source: https://support.airtable.com/docs/managing-api-call-limits-in-airtable. The draft only states 5 req/s/base.
- PUBLIC_API_BILLING_LIMIT_EXCEEDED (plan monthly cap, also 429) is real per the troubleshooting page; monthly caps are Free = 1,000 calls/month and Team = 100,000 calls/month (Team then throttles to 2 req/s; Business/Enterprise Scale has no monthly cap). Sources: https://support.airtable.com/docs/airtable-api-common-troubleshooting and https://support.airtable.com/docs/managing-api-call-limits-in-airtable. (Note: the managing-api-call-limits page does NOT spell out the literal string PUBLIC_API_BILLING_LIMIT_EXCEEDED — that string is attested on the troubleshooting page / community; lower confidence on the exact string.)

### CORRECTION 5 — 401: type/message plausible but slightly over-stated as official
The draft gives {"type":"AUTHENTICATION_REQUIRED","message":"Authentication required"}. This is corroborated by multiple third-party sources and is very likely correct. BUT the official errors page does NOT show a 401 JSON example at all (only a prose description "Accessing a protected resource without authorization or with invalid credentials"), and the support troubleshooting page refers to it in lowercase prose ("authentication_required"). So treat AUTHENTICATION_REQUIRED / "Authentication required" as well-attested-but-not-verbatim-official (medium-high confidence), not as a quoted official body. The draft cites only the airtable-mcp-server fixtures + support page, which is fair; just don't imply the official errors page shows this body. Sources: https://airtable.com/developers/web/api/errors (no 401 example), https://support.airtable.com/docs/airtable-api-common-troubleshooting.

### CONFIRMED CORRECT (no change needed)
- Two-envelope model (object {"error":{"type","message"}} vs bare string {"error":"..."}) — CORRECT. Both shapes appear on the official page. Field names "type" and "message" are exact. Source: https://airtable.com/developers/web/api/errors.
- 403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND body + message ("Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct.") — CORRECT/verbatim. Source: official page + community https://community.airtable.com/other-questions-13/...-44852.
- 403 INVALID_PERMISSIONS — CORRECT; official page additionally shows context-specific messages ("You are not permitted to create records in table ...", "You are not permitted to write cell values in field ...", "You are not permitted to perform this operation"). The draft's "You are not permitted to perform this operation" is one valid instance. Source: https://airtable.com/developers/web/api/errors.
- Full status-code set on the official page (in order): 200, 400, 401, 403, 404, 413, 422, 429, 500, 502, 503. The draft omits 502 Bad Gateway ("Airtable's servers are restarting or an unexpected outage"); a faithful twin should include 502 (object form, no type enumerated). Source: https://airtable.com/developers/web/api/errors.
- 413: draft's REQUEST_TOO_LARGE string is NOT officially confirmed — correct to keep in open questions. Official page only says "You shouldn't encounter this under normal use," no type/message. Source: https://airtable.com/developers/web/api/errors.
- 400 / 500: exact type/message not enumerated officially — correct to flag as unconfirmed. 400 context = "request encoding is invalid; can't be parsed as valid JSON"; 500 = "server encountered an unexpected condition." Source: https://airtable.com/developers/web/api/errors.
- Retry-After: documented as "may be provided" on 503; NOT documented for 429 — the draft's note is CORRECT. Source: https://airtable.com/developers/web/api/errors.

### CLEAN MARKDOWN — corrected section ready to paste (replaces draft 4.x where it conflicts)

#### 4.1 Two error envelope forms
Confirmed exactly as drafted: object form {"error":{"type","message"}} and bare-string form {"error":"NOT_FOUND"}, both shown on the official errors page. Field names are literally "type" and "message". (https://airtable.com/developers/web/api/errors)

#### 4.2 Catalog by HTTP status (corrections folded in)
- 400 Bad Request — object form; type/message NOT officially enumerated (context: invalid request encoding / unparseable JSON). Keep draft's INVALID_REQUEST_UNKNOWN guess in open questions.
- 401 Unauthorized — object form; well-attested {"error":{"type":"AUTHENTICATION_REQUIRED","message":"Authentication required"}} (not shown verbatim on official errors page; medium-high confidence).
- 403 Forbidden — object form; INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND (verbatim message as drafted) and INVALID_PERMISSIONS (message varies by operation). CONFIRMED.
- 404 Not Found — BOTH official: {"error":"NOT_FOUND"} (bare) AND {"error":{"type":"NOT_FOUND"}} (object, usually no message). MODEL_ID_NOT_FOUND/TABLE_NOT_FOUND-with-message are third-party-observed variants of an acknowledged-inconsistent 404. CORRECTED.
- 413 Payload Too Large — object form; type/message NOT documented (REQUEST_TOO_LARGE unconfirmed). Keep in open questions.
- 422 Unprocessable Entity — object form; official: INVALID_REQUEST_UNKNOWN ("Invalid request: parameter validation failed...") plus documented cases for invalid request body, invalid multiple-choice/select option, and FAILED_STATE_CHECK ("values and/or parameters in the endpoint path have been mismatched"). Community-attested: INVALID_REQUEST_MISSING_FIELDS, UNKNOWN_FIELD_NAME, INVALID_VALUE_FOR_COLUMN. ADD FAILED_STATE_CHECK (was missing).
- 429 Too Many Requests — object form; {"error":{"type":"RATE_LIMIT_REACHED","message":"Rate limit exceeded. Please try again later"}}. CONFIRMED. Limits: 5 req/s/base AND 50 req/s/token(user); 30s wait after 429. Plan caps: Free 1,000/mo, Team 100,000/mo (then 2 req/s). PUBLIC_API_BILLING_LIMIT_EXCEEDED attested (exact string lower-confidence).
- 500 Internal Server Error — object form; type/message NOT enumerated (INTERNAL_SERVER_ERROR unconfirmed).
- 502 Bad Gateway — ADD THIS (draft omitted it). Object form; no type enumerated; context = servers restarting / unexpected outage.
- 503 Service Unavailable — object form; {"error":{"type":"RETRIABLE_ERROR","message":"Server encountered an error while processing your request, and it is safe to retry the request"}}. MESSAGE CORRECTED.

#### 4.3 Headers
Retry-After may appear on 503 (not documented for 429). All bodies application/json. CONFIRMED.

#### 4.4 Summary table changes
- 404 row: change envelope note to "bare string {\"error\":\"NOT_FOUND\"} OR object {\"error\":{\"type\":\"NOT_FOUND\"}} — both official; MODEL_ID_NOT_FOUND/TABLE_NOT_FOUND object-with-message are third-party-observed."
- 422 row: add FAILED_STATE_CHECK.
- Add a 502 row (object, no enumerated type).
- 503 row message wording fix as above.

### OPEN QUESTIONS (still unconfirmed — do not invent)
- Exact 400 type/message (INVALID_REQUEST_UNKNOWN vs other).
- Exact 413 type/message (REQUEST_TOO_LARGE unconfirmed).
- Exact 500 type/message (INTERNAL_SERVER_ERROR unconfirmed).
- Whether object-form 404 ever includes a "message" by default, or only "type":"NOT_FOUND" (official example shows type only).
- Exact literal of the plan-cap 429 type (PUBLIC_API_BILLING_LIMIT_EXCEEDED attested on troubleshooting/community, not on the rate-limits page).
- Whether 401 ever returns a distinct type for invalid-vs-missing token (support page hints at two cases: missing token vs invalid token) — only one body (AUTHENTICATION_REQUIRED) is attested.


**Sources:** https://airtable.com/developers/web/api/errors · https://support.airtable.com/docs/airtable-api-common-troubleshooting · https://docs.miniextensions.com/en/articles/5282014-404-error-type-model_id_not_found-message-table-not-found · https://github.com/domdomegg/airtable-mcp-server/blob/master/src/enhanceAirtableError.test.ts · https://community.airtable.com/development-apis-11/error-code-422-invalid-request-missing-fields-4535 · https://community.airtable.com/t5/development-apis/api-unknown-field-name-error-422/td-p/27792 · https://community.airtable.com/fid-11/tid-7170 · https://community.airtable.com/development-apis-11/invalid-permissions-or-model-not-found-error-3982 · https://community.airtable.com/t5/development-apis/api-response-quot-not-found-quot/td-p/82528


## 5. Records API — create / update / delete

All write operations share the base path:

```
https://api.airtable.com/v0/{baseId}/{tableIdOrName}
```

`{tableIdOrName}` accepts either the table ID (`tbl…`) or the URL-encoded table name. All write operations require an auth token (PAT or OAuth) with scope `data.records:write` and at least Editor permission on the base. Request bodies for POST/PATCH/PUT require header `Content-Type: application/json`. ([create-records](https://airtable.com/developers/web/api/create-records), [update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records), [troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

### 5.1 Create records — `POST /v0/{baseId}/{tableIdOrName}`

Two body shapes are accepted on the same endpoint. ([create-records](https://airtable.com/developers/web/api/create-records))

**(a) Single record** — top-level `fields` object:

Request:
```json
{
  "fields": {
    "Address": "333 Post St",
    "Name": "Union Square",
    "Visited": true
  }
}
```

Response — `200 OK`, a single record object (NOT wrapped in `records`):
```json
{
  "id": "rec560UJdUtocSouk",
  "createdTime": "2022-09-12T21:03:48.000Z",
  "fields": {
    "Address": "333 Post St",
    "Name": "Union Square",
    "Visited": true
  }
}
```
([create-records](https://airtable.com/developers/web/api/create-records))

**(b) Batch** — top-level `records` array (max 10), with optional `typecast` and `returnFieldsByFieldId` (both default `false`):

Request:
```json
{
  "records": [
    {
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    },
    {
      "fields": {
        "Address": "1 Ferry Building",
        "Name": "Ferry Building"
      }
    }
  ],
  "typecast": false,
  "returnFieldsByFieldId": false
}
```

Response — `200 OK`, a `records` array (record order preserved):
```json
{
  "records": [
    {
      "id": "rec560UJdUtocSouk",
      "createdTime": "2022-09-12T21:03:48.000Z",
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    },
    {
      "id": "rec3lbPRG4aVqkeOQ",
      "createdTime": "2022-09-12T21:03:48.000Z",
      "fields": {
        "Address": "1 Ferry Building",
        "Name": "Ferry Building"
      }
    }
  ]
}
```
([create-records](https://airtable.com/developers/web/api/create-records))

Notes for the twin:
- Response always echoes the server-assigned `id` (`rec…`, 17 chars) and `createdTime` (ISO‑8601 UTC, milliseconds + `Z`, e.g. `2022-09-12T21:03:48.000Z`).
- `typecast: true` lets Airtable coerce/auto-create values (e.g. create new single/multiple-select options, parse strings into numbers/dates). With `typecast: false` (default), a value not matching the field is rejected (see §5.6). ([create-records](https://airtable.com/developers/web/api/create-records); [community on typecast/select options](https://community.airtable.com/development-apis-11/how-can-i-prevent-the-invalid-multiple-choice-options-error-5354))
- `returnFieldsByFieldId: true` keys the returned `fields` object by field ID (`fld…`) instead of field name. ([create-records](https://airtable.com/developers/web/api/create-records))
- Computed fields (formula, rollup, lookup, autonumber, created/last-modified time) cannot be written and must be omitted from `fields`.

### 5.2 Update — partial (PATCH) vs destructive (PUT)

The same two methods, `PATCH` and `PUT`, exist for both the batch and single-record endpoints. The only difference between them: ([update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records), [update-record](https://airtable.com/developers/web/api/update-record))
- **PATCH** — only the fields included in the request are updated; fields not included are left unchanged.
- **PUT** — destructive update: clears every cell value not included in the request (i.e. unspecified writable fields are reset to empty).

### 5.3 Update multiple records (batch) — `PATCH` / `PUT /v0/{baseId}/{tableIdOrName}`

Each element of `records` must carry an `id` plus a `fields` object. Max 10 records. Optional `typecast` / `returnFieldsByFieldId`. ([update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records))

Request:
```json
{
  "records": [
    {
      "id": "rec560UJdUtocSouk",
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    }
  ],
  "typecast": false,
  "returnFieldsByFieldId": false
}
```

Response — `200 OK`:
```json
{
  "records": [
    {
      "id": "rec560UJdUtocSouk",
      "createdTime": "2022-09-12T21:03:48.000Z",
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    }
  ]
}
```
([update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records))

### 5.4 Update single record — `PATCH` / `PUT /v0/{baseId}/{tableIdOrName}/{recordId}`

Body is a top-level `fields` object (no `id` in the body — the record is identified by the path). Optional `typecast` / `returnFieldsByFieldId`. ([update-record](https://airtable.com/developers/web/api/update-record))

Request:
```json
{
  "fields": {
    "Address": "1 Ferry Building",
    "Name": "Ferry Building",
    "Visited": true
  }
}
```

Response — `200 OK`, a single record object:
```json
{
  "id": "rec3lbPRG4aVqkeOQ",
  "createdTime": "2022-09-12T21:03:48.000Z",
  "fields": {
    "Address": "1 Ferry Building",
    "Name": "Ferry Building",
    "Visited": true
  }
}
```
([update-record](https://airtable.com/developers/web/api/update-record))

### 5.5 Upsert (PATCH on the batch endpoint with `performUpsert`)

Upsert is enabled only on the batch update endpoint (`PATCH`/`PUT /v0/{baseId}/{tableIdOrName}`) by adding `performUpsert` with `fieldsToMergeOn`. ([update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records))

- `fieldsToMergeOn`: 1–3 fields used as an external/composite key. They cannot be computed fields (formula, lookup, rollup, etc.).
- Records may be supplied **without** an `id`. For each input record, Airtable matches existing rows where the merge fields equal the supplied values:
  - **0 matches** → a new record is created.
  - **exactly 1 match** → that record is updated.
  - **2+ matches** → the entire request fails (no partial writes).
- If a record DOES include an `id`, it is matched by `id` directly (merge fields ignored for that record).

Request:
```json
{
  "performUpsert": {
    "fieldsToMergeOn": ["Name"]
  },
  "records": [
    {
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    }
  ],
  "typecast": false,
  "returnFieldsByFieldId": false
}
```

Response — `200 OK`. The response adds two arrays of record IDs, `createdRecords` and `updatedRecords`, alongside the full `records` array:
```json
{
  "records": [
    {
      "id": "rec560UJdUtocSouk",
      "createdTime": "2022-09-12T21:03:48.000Z",
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    }
  ],
  "createdRecords": ["rec560UJdUtocSouk"],
  "updatedRecords": []
}
```
- `createdRecords` lists the IDs that were newly created; `updatedRecords` lists the IDs that matched an existing row and were updated. A given ID appears in exactly one of the two arrays.
- On a plain (non-upsert) batch update, `createdRecords` / `updatedRecords` are NOT present — they appear only when `performUpsert` is supplied.

([update-multiple-records](https://airtable.com/developers/web/api/update-multiple-records))

### 5.6 Delete records

**(a) Single** — `DELETE /v0/{baseId}/{tableIdOrName}/{recordId}` (no body, no query params).

Response — `200 OK`:
```json
{
  "deleted": true,
  "id": "rec560UJdUtocSouk"
}
```
([delete-record](https://airtable.com/developers/web/api/delete-record))

**(b) Batch** — `DELETE /v0/{baseId}/{tableIdOrName}?records[]={id}&records[]={id}` (record IDs passed as repeated `records[]` query parameters; max 10).

Example request URL:
```
DELETE https://api.airtable.com/v0/{baseId}/{tableIdOrName}?records[]=rec560UJdUtocSouk&records[]=rec3lbPRG4aVqkeOQ
```

Response — `200 OK`, a `records` array of `{ deleted, id }` objects:
```json
{
  "records": [
    {
      "deleted": true,
      "id": "rec560UJdUtocSouk"
    },
    {
      "deleted": true,
      "id": "rec3lbPRG4aVqkeOQ"
    }
  ]
}
```
([delete-multiple-records](https://airtable.com/developers/web/api/delete-multiple-records))

### 5.7 The 10-record batch cap

For create, batch-update (incl. upsert), and batch-delete, the maximum is **10 records per request**. (Throughput is also bounded by the rate limit of 5 req/base/sec, hence the common "50 records/sec" figure = 5 batches × 10.) ([managing API call limits](https://support.airtable.com/docs/managing-api-call-limits-in-airtable); [community: batch limit is 10](https://community.n8n.io/t/airtable-update-error-you-must-provide-an-array-of-up-to-10-record-objects-each-with-an-id-id-field-and-a-fields-object-for-cell-values/6810))

Exceeding 10 returns **HTTP 422** with an error body of the standard shape `{"error": {"type": "...", "message": "..."}}`:

- **Create** (>10 in `records`): message is verbatim
  `"A maximum of 10 records can be created per request but you have provided 11."` (the count reflects the number actually sent). ([Zapier community relaying the Airtable error](https://community.zapier.com/troubleshooting-99/could-not-create-records-in-airtable-a-maximum-of-10-records-can-be-created-per-request-but-you-have-provided-11-27482))
- **Update** (>10, or malformed elements): error `type` is `INVALID_RECORDS`, message verbatim
  `"You must provide an array of up to 10 record objects, each with an \"id\" ID field and a \"fields\" object for cell values."` ([n8n community relaying the Airtable error](https://community.n8n.io/t/airtable-update-error-you-must-provide-an-array-of-up-to-10-record-objects-each-with-an-id-id-field-and-a-fields-object-for-cell-values/6810); [community: INVALID_RECORDS](https://community.airtable.com/t5/development-apis/invalid-records/td-p/63225))

> Twin note: the create-side error `type` is most consistently reported as `INVALID_RECORDS`, but I could not confirm the exact `type` string for the create cap message from a primary Airtable source (only the message text). See open questions.

### 5.8 Standard error envelope and relevant status codes

All errors use the JSON envelope:
```json
{ "error": { "type": "ERROR_TYPE_STRING", "message": "Human-readable message" } }
```
(401 uses lowercase types, e.g. `{"error": {"type": "authentication_required", "message": "..."}}`.) ([troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

Status codes most relevant to write ops: ([troubleshooting](https://support.airtable.com/docs/airtable-api-common-troubleshooting))

| Status | type | message (verbatim where confirmed) | When |
|---|---|---|---|
| 400 | — | invalid request encoding / malformed JSON | Body is not valid JSON |
| 401 | `authentication_required` | "The access token was not present in the request, or it was passed incorrectly." | Missing/garbled token |
| 401 | (invalid token) | "The access token that was provided is invalid." | Bad token |
| 403 | `INVALID_PERMISSIONS` | "You are not permitted to create records in table TABLE_NAME (TABLE_ID)" | No write permission on table |
| 403 | `INVALID_PERMISSIONS` | "You are not permitted to write cell values in field FIELD_NAME (FIELD_ID)" | No write permission on a field |
| 404 | `MODEL_ID_NOT_FOUND` | "Record not found" | DELETE of a non-existent `recordId` |
| 404 | `NOT_FOUND` | (route/base/table not found) | Unknown base/table or bad route |
| 422 | `INVALID_REQUEST_UNKNOWN` | "Invalid request: parameter validation failed. Check your request data." | Generic body/param validation failure |
| 422 | `INVALID_REQUEST_MISSING_FIELDS` | (missing required `fields`/`id` in body) | Required key absent |
| 422 | `INVALID_RECORDS` | see §5.7 | >10 records or malformed `records` element |
| 422 | `ROW_DOES_NOT_EXIST` | "Record ID {recordId} does not exist in this table" | PATCH/PUT batch update of a non-existent record ID |
| 422 | `INVALID_VALUE_FOR_COLUMN` | (field cannot accept the provided value) | Wrong type / value with `typecast` off |
| 422 | `INVALID_MULTIPLE_CHOICE_OPTIONS` | (select option does not exist) | Unknown single/multi-select option with `typecast` off |
| 429 | `TOO_MANY_REQUESTS` | "Rate limit of 5 requests per base per second exceeded" | >5 req/base/sec (then 30s backoff) |
| 503 | `RETRIABLE_ERROR` | "Server encountered an error while processing your request, and it is safe to retry the request" | Transient server error |

> Asymmetry to replicate exactly: a non-existent record ID returns **404 `MODEL_ID_NOT_FOUND`** on the single-record DELETE path, but **422 `ROW_DOES_NOT_EXIST`** ("Record ID … does not exist in this table") on the batch PATCH/PUT update path. ([404 MODEL_ID_NOT_FOUND on delete](https://community.make.com/t/404-not-found-erorr-airtable-update-module/70705); [422 ROW_DOES_NOT_EXIST on update](https://community.airtable.com/development-apis-11/error-row-does-not-exist-5755))


**Sources:** https://airtable.com/developers/web/api/create-records · https://airtable.com/developers/web/api/update-multiple-records · https://airtable.com/developers/web/api/update-record · https://airtable.com/developers/web/api/delete-multiple-records · https://airtable.com/developers/web/api/delete-record · https://support.airtable.com/docs/airtable-api-common-troubleshooting · https://support.airtable.com/docs/managing-api-call-limits-in-airtable · https://community.zapier.com/troubleshooting-99/could-not-create-records-in-airtable-a-maximum-of-10-records-can-be-created-per-request-but-you-have-provided-11-27482 · https://community.n8n.io/t/airtable-update-error-you-must-provide-an-array-of-up-to-10-record-objects-each-with-an-id-id-field-and-a-fields-object-for-cell-values/6810 · https://community.airtable.com/t5/development-apis/invalid-records/td-p/63225 · https://community.airtable.com/development-apis-11/error-row-does-not-exist-5755 · https://community.make.com/t/404-not-found-erorr-airtable-update-module/70705 · https://community.airtable.com/development-apis-11/how-can-i-prevent-the-invalid-multiple-choice-options-error-5354


## 6. Records API — list & query semantics

### 6.1 Endpoint

```
GET https://api.airtable.com/v0/{baseId}/{tableIdOrName}
```

- `baseId` — base identifier (e.g. `appXXXXXXXXXXXXXX`).
- `tableIdOrName` — either the table ID (`tblXXXXXXXXXXXXXX`) or the URL-encoded table name. ([list-records](https://airtable.com/developers/web/api/list-records))
- Requires `Authorization: Bearer {token}` header and `data.records:read` scope. ([list-records](https://airtable.com/developers/web/api/list-records))

**POST variant for long URLs** — a `POST /v0/{baseId}/{tableIdOrName}/listRecords` exists and accepts the identical parameters in a JSON request body instead of the query string. Airtable enforces a **16,000-character URL length limit**; requests that would exceed it (large `filterByFormula`, long `offset`, many `fields[]`) must use this POST form. The twin should expose both routes and apply identical parameter handling to each. ([list-records](https://airtable.com/developers/web/api/list-records), [URL length limit](https://support.airtable.com/docs/enforcement-of-url-length-limit-for-web-api-requests))

### 6.2 Query parameters

All parameters are optional. Array-shaped params use the repeated `name[]=...` / indexed `name[i][...]=...` query-string convention (or native arrays/objects in the POST body).

| Parameter | Type | Default | Limits / notes | Source |
|---|---|---|---|---|
| `fields[]` | array of strings | (all fields) | Field names, or field IDs when combined with `returnFieldsByFieldId`. Only the listed fields are returned; reduces payload size. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `filterByFormula` | string | (none) | An Airtable formula evaluated per record; the record is returned only when the formula is truthy (non-`0`, non-`""`, non-`false`, non-error). Must be URL-encoded. Evaluated against the chosen `view` if `view` is also set. Invalid formula → `422 INVALID_FILTER_BY_FORMULA`. | [list-records](https://airtable.com/developers/web/api/list-records), [errors](https://airtable.com/developers/web/api/errors) |
| `maxRecords` | integer | (unlimited) | Maximum **total** number of records returned **across all pages**. Pagination stops once this many records have been returned. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `pageSize` | integer | `100` | Number of records per page. **Must be ≤ 100** (also the default). Values > 100 are rejected with `422`. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `sort[i][field]` | string | (none) | Field name (or field ID) to sort by. Multiple sort objects apply in array order (primary, secondary, …). | [list-records](https://airtable.com/developers/web/api/list-records) |
| `sort[i][direction]` | string enum | `"asc"` | One of `"asc"` or `"desc"`. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `view` | string | (none) | View name **or** view ID. Records are returned in that view's order and filtered/sorted by the view's own config. Hidden fields in the view are still returned unless restricted with `fields[]`. `sort`/`filterByFormula` further refine the view's output. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `cellFormat` | string enum | `"json"` | `"json"` (machine-readable cell values) or `"string"` (cells formatted as the user-facing strings shown in the Airtable UI). **`"string"` requires both `timeZone` and `userLocale`.** | [list-records](https://airtable.com/developers/web/api/list-records) |
| `timeZone` | string | (none) | Time-zone identifier (e.g. `America/Los_Angeles`) used to format date/time cells. **Required when `cellFormat="string"`.** | [list-records](https://airtable.com/developers/web/api/list-records) |
| `userLocale` | string | (none) | User-locale identifier (e.g. `en-gb`) used to format dates/numbers. **Required when `cellFormat="string"`.** | [list-records](https://airtable.com/developers/web/api/list-records) |
| `offset` | string | (none) | Opaque pagination cursor. Pass the `offset` returned by the previous response to fetch the next page. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `recordMetadata[]` | array of strings | (none) | Currently the only accepted value is `"commentCount"`; when present, each record gains a `commentCount` integer field. | [list-records](https://airtable.com/developers/web/api/list-records) |
| `returnFieldsByFieldId` | boolean | `false` | When `true`, keys in each record's `fields` object are **field IDs** (`fldXXXXXXXXXXXXXX`) instead of field names. | [list-records](https://airtable.com/developers/web/api/list-records) |

> Note: The live reference also documents `includeDateDependencyMetadata` (boolean) for returning date-dependency objects on linked-record cells. Treat as out-of-scope/optional for the twin unless date-dependency emulation is needed. ([list-records](https://airtable.com/developers/web/api/list-records))

### 6.3 Response shape (200 OK)

```json
{
  "records": [
    {
      "id": "rec560UJdUtocSouk",
      "createdTime": "2022-09-12T21:03:48.000Z",
      "fields": {
        "Address": "333 Post St",
        "Name": "Union Square",
        "Visited": true
      }
    }
  ],
  "offset": "itr4x9Pa1WMc2Wc1J/rec8I9aLDoFQrEAvN"
}
```

- `records` — array of record objects. Each has:
  - `id` (string, `rec…`)
  - `createdTime` (string, ISO 8601 UTC, e.g. `2022-09-12T21:03:48.000Z`)
  - `fields` (object). Cells with empty/blank values are **omitted** from `fields` rather than returned as `null`. Keys are field names by default, field IDs when `returnFieldsByFieldId=true`.
  - `commentCount` (integer) — present only when `recordMetadata[]=commentCount` was passed.
- `offset` — present **only when more records remain**. ([list-records](https://airtable.com/developers/web/api/list-records))

A response with **no top-level `offset` key** means the last page has been reached (end of table, or `maxRecords` total satisfied). The minimal verbatim example from the docs omits `offset` entirely on the final/only page. ([list-records](https://airtable.com/developers/web/api/list-records))

### 6.4 Pagination semantics (twin behavior)

1. First request (no `offset`): return up to `pageSize` records (default 100, hard cap 100).
2. If more records exist **and** the `maxRecords` total has not been reached, include an opaque `offset` cursor in the response.
3. Caller re-issues the same query with `offset` set to that value to get the next page.
4. Stop emitting `offset` when the end of the result set is reached or the cumulative count hits `maxRecords`. ([list-records](https://airtable.com/developers/web/api/list-records))
- The `offset` value is opaque (Airtable's real format looks like `<rowToken>/<recordId>`); the twin may use any stable, self-consistent token but must treat a stale/garbage offset as `422` (see errors). ([list-records](https://airtable.com/developers/web/api/list-records))

### 6.5 Error responses (for invalid requests)

Airtable uses two error-body shapes; the twin must reproduce both. ([errors](https://airtable.com/developers/web/api/errors))

**Structured form** (most validation/permission errors):
```json
{ "error": { "type": "INVALID_REQUEST_UNKNOWN", "message": "Invalid request: parameter validation failed. Check your request data." } }
```

**Bare-string form** (notably some not-found cases):
```json
{ "error": "NOT_FOUND" }
```

| Status | Example `type` / body | Trigger relevant to list-records | Source |
|---|---|---|---|
| `401 Unauthorized` | missing/invalid bearer token | No or invalid `Authorization` header | [errors](https://airtable.com/developers/web/api/errors) |
| `403 Forbidden` | `{"error":{"type":"INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND","message":"..."}}` | Token lacks `data.records:read` / no base access | [errors](https://airtable.com/developers/web/api/errors) |
| `404 Not Found` | `{"error":"NOT_FOUND"}` or `{"error":{"type":"NOT_FOUND"}}` | Unknown base/table | [errors](https://airtable.com/developers/web/api/errors) |
| `422 Unprocessable Entity` | `{"error":{"type":"INVALID_REQUEST_UNKNOWN","message":"Invalid request: parameter validation failed. Check your request data."}}` | Bad parameter (e.g. `pageSize` > 100, malformed `sort`, stale `offset`) | [errors](https://airtable.com/developers/web/api/errors) |
| `422 Unprocessable Entity` | `{"error":{"type":"INVALID_FILTER_BY_FORMULA","message":"The formula for filtering records is invalid: ..."}}` | Malformed/invalid `filterByFormula` | [errors](https://airtable.com/developers/web/api/errors), [Make community](https://community.make.com/t/airtable-error-422-the-formula-for-filtering-records-is-invalid-invalid-formula-please-check-your-formula-text/16998) |


**⚠ Independent verifier (DISAGREES — apply these corrections):**

The draft is mostly correct but has two material errors and one significant omission, so agrees=false.

CORRECTION 1 (important): Draft §6.4/§6.5 claim a stale/garbage `offset` returns `422 INVALID_REQUEST_UNKNOWN`. The correct type is `422 LIST_RECORDS_ITERATOR_NOT_AVAILABLE`. The list-records docs state iteration may time out due to client inactivity or server restarts, returning a 422; the offset is time-windowed, not merely opaque. The twin must emit this specific type for expired/unknown offsets. (https://airtable.com/developers/web/api/list-records ; https://community.airtable.com/development-apis-11/http-error-422-iterator-observation-6533)

CORRECTION 2 (omission): The §6.5 error table omits 429. A high-fidelity twin must reproduce rate limiting: 5 req/sec per base (all plans) and 50 req/sec per user/service-account PAT; exceeding returns HTTP 429 (type RATE_LIMIT_REACHED) and clients must wait 30 seconds. The rate-limits page does NOT document a Retry-After or any rate-limit response header, so do not assume one. (https://airtable.com/developers/web/api/rate-limits ; https://support.airtable.com/docs/managing-api-call-limits-in-airtable ; https://airtable.com/developers/web/api/errors)

CORRECTION 3 (minor): Draft §6.2 lists the filterByFormula falsy set as 0, "", false, error. The documented inclusion rule excludes a record only when the result is 0, false, "", NaN, [], or #Error! — the draft is missing NaN and [] (empty array). (https://airtable.com/developers/web/api/list-records ; https://support.airtable.com/docs/airtable-api-common-troubleshooting)

CONFIRMED CORRECT (independently re-fetched): GET + POST .../listRecords endpoint paths and path params; 16,000-char URL limit; all query params/types/defaults; pageSize default 100 and must be <=100; maxRecords is total across all pages; sort field/direction semantics; view overridden by sort; cellFormat=string requires both timeZone and userLocale; 200 response shape (records[] of {id, createdTime ISO, fields, commentCount?} + optional top-level offset; empty cells omitted from fields); BOTH error-envelope shapes coexist — object {"error":{"type","message"}} and bare string {"error":"NOT_FOUND"}; 403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND; 404 NOT_FOUND (no message); 422 INVALID_REQUEST_UNKNOWN; INVALID_FILTER_BY_FORMULA is 422.

OPEN QUESTIONS (do not invent): exact verbatim message strings for 401 and 429 are not quoted in the public reference (treat the 429 message as approximate); per-route 404 envelope choice (bare string vs object) is not explicitly disambiguated, draft's hedge is acceptable; no Retry-After/rate-limit headers are documented.


**Sources:** https://airtable.com/developers/web/api/list-records · https://airtable.com/developers/web/api/errors · https://support.airtable.com/docs/enforcement-of-url-length-limit-for-web-api-requests · https://support.airtable.com/docs/getting-started-with-airtables-web-api · https://support.airtable.com/docs/timezones-and-locales · https://community.make.com/t/airtable-error-422-the-formula-for-filtering-records-is-invalid-invalid-formula-please-check-your-formula-text/16998


## 7. filterByFormula grammar

`filterByFormula` is a query parameter on **List records** (`GET /v0/{baseId}/{tableIdOrName}`) whose value is a string written in the Airtable formula language. The server evaluates the formula once per record; a record is **included** in the response unless the formula evaluates to one of the falsy values `0`, `false`, `""` (empty string), `NaN`, `[]` (empty array), or `#Error!` — any other result includes the record. ([list-records](https://airtable.com/developers/web/api/list-records); corroborated by [airtable-python-wrapper params](https://airtable-python-wrapper.readthedocs.io/en/master/params.html)). When combined with `view`, only records in that view that also satisfy the formula are returned ([list-records](https://airtable.com/developers/web/api/list-records)).

The formula value **must be URL-encoded** before being placed in the query string. Because encoded formulas can push the request past the **16,000-character URL limit**, the API also supports `POST /v0/{baseId}/{tableIdOrName}/listRecords` with the same parameters in the JSON body ([list-records](https://airtable.com/developers/web/api/list-records)).

This spec implements a faithful **subset** of the formula grammar sufficient for record filtering. The full Airtable formula language is large; the subset below covers field refs, literals, comparison/arithmetic operators, logical functions, and the most common text/number functions. Everything else is explicitly out of scope (see end).

### 7.1 Field reference syntax

- A **single-word** field name may be written bare: `Price` ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).
- A field name containing spaces or special characters **must** be wrapped in curly braces: `{Regular Price}` ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)). In practice, always emitting `{Field Name}` is safe and recommended.
- Fields may be referenced by **field name or field ID** inside the formula ([list-records](https://airtable.com/developers/web/api/list-records)).
- Referencing a name that does not exist produces an invalid-formula error from the API rather than a per-record evaluation (the documented message variant is `Unknown field names: ...`) ([Airtable Community / Make](https://community.make.com/t/airtable-error-422-the-formula-for-filtering-records-is-invalid-invalid-formula-please-check-your-formula-text/16998)).

### 7.2 Literal syntax

- **String literals** use double quotes. A double quote inside a string is escaped with a backslash: `"text"`, `"\"quoted\""`. Single-quoted strings are also widely accepted in `filterByFormula` (e.g. `{Name}='Alice'`) and appear throughout Airtable's own examples; the twin should accept both `'…'` and `"…"`. ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)). Note: Airtable rejects "smart"/curly quotes — only straight quotes are valid ([common-formula-errors](https://support.airtable.com/docs/common-formula-errors-and-how-to-fix-them)).
- **Number literals**: integers and decimals, e.g. `2`, `3.5`, `100` ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).
- **Booleans** are produced by the functions `TRUE()` and `FALSE()`; internally `TRUE()` = 1 and `FALSE()` = 0 ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)). There is no bare `true`/`false` keyword.
- **Blank** is produced by `BLANK()`; an empty value also compares equal to the empty string `''` (the common "is empty" idiom is `{Field}=''` / "is not empty" is `NOT({Field}='')`) ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference); [Airtable Community](https://community.airtable.com/formulas-10/need-to-return-records-with-an-empty-field-33330)).

### 7.3 Operators

**Comparison** (all return a boolean / 1 or 0) ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)):

| Operator | Meaning |
|----------|---------|
| `=`  | equal to |
| `!=` | not equal to |
| `>`  | greater than |
| `<`  | less than |
| `>=` | greater than or equal to |
| `<=` | less than or equal to |

**Arithmetic** ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)):

| Operator | Meaning |
|----------|---------|
| `+` | addition |
| `-` | subtraction |
| `*` | multiplication |
| `/` | division (divide by zero → `Infinity`; `0/0` → `NaN`) ([common-formula-errors](https://support.airtable.com/docs/common-formula-errors-and-how-to-fix-them)) |

**Text concatenation**: the `&` operator joins two values into a string, equivalent to `CONCATENATE()` ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).

Parentheses `( )` group sub-expressions; function arguments are comma-separated.

### 7.4 Logical / conditional functions

([formula-field-reference](https://support.airtable.com/docs/formula-field-reference))

- `AND(expr1, [expr2, ...])` — true only if **all** arguments are true.
- `OR(expr1, [expr2, ...])` — true if **any** argument is true.
- `NOT(expr)` — logical negation.
- `XOR(expr1, [expr2, ...])` — true if an **odd** number of arguments are true.
- `IF(expr, valueIfTrue, valueIfFalse)` — returns `valueIfTrue` when `expr` is truthy, else `valueIfFalse`; may be nested.
- `SWITCH(expr, [pattern, result, ...], [default])` — matches `expr` against each `pattern`, returns the matching `result`, else `default`.
- `TRUE()` → 1, `FALSE()` → 0, `BLANK()` → blank.

### 7.5 Text functions

([formula-field-reference](https://support.airtable.com/docs/formula-field-reference))

| Signature | Behavior |
|-----------|----------|
| `CONCATENATE(text1, [text2, ...])` | join arguments into one string (same as `&`) |
| `FIND(stringToFind, whereToSearch, [startFromPosition])` | 1-based index of first occurrence; **returns `0` if not found** |
| `SEARCH(stringToFind, whereToSearch, [startFromPosition])` | like `FIND` but **returns blank/empty if not found** (and is case-insensitive in usage); 1-based |
| `LOWER(string)` | lowercase |
| `UPPER(string)` | uppercase |
| `LEN(string)` | character count |
| `TRIM(string)` | strip leading/trailing whitespace |
| `LEFT(string, howMany)` | first N characters |
| `RIGHT(string, howMany)` | last N characters |
| `MID(string, whereToStart, count)` | substring starting at 1-based `whereToStart` |
| `SUBSTITUTE(string, oldText, newText, [index])` | replace occurrence(s) of `oldText` |
| `REPLACE(string, startChar, numChars, replacement)` | replace `numChars` chars at 1-based `startChar` |
| `REPT(string, number)` | repeat `string` N times |
| `T(value)` | returns the value if it is text, else blank |
| `VALUE(text)` | parse a numeric string into a number |
| `ARRAYJOIN(array, separator)` | join array elements into a string |

> Note on `FIND` vs `SEARCH`: the key distinguishing behavior is the not-found result — `FIND` → `0`, `SEARCH` → empty/blank. The twin must replicate this difference because it changes truthiness when the result is used directly in `filterByFormula` (e.g. `FIND("x", {Name})` excludes non-matches via `0`, whereas `SEARCH(...)` excludes them via blank `""`).

### 7.6 Number functions

([formula-field-reference](https://support.airtable.com/docs/formula-field-reference))

| Signature | Behavior |
|-----------|----------|
| `ABS(value)` | absolute value |
| `ROUND(value, precision)` | round to `precision` decimals |
| `ROUNDUP(value, precision)` / `ROUNDDOWN(value, precision)` | round away from / toward zero |
| `INT(value)` | greatest integer ≤ value |
| `MOD(value, divisor)` | remainder |
| `CEILING(value, [significance])` / `FLOOR(value, [significance])` | round to nearest multiple |
| `POWER(base, power)` / `SQRT(value)` | exponent / square root |
| `MAX(n1, [n2, ...])` / `MIN(n1, [n2, ...])` | extrema |
| `SUM(n1, [n2, ...])` / `AVERAGE(n1, [n2, ...])` | aggregate |

### 7.7 Error handling

([formula-field-reference](https://support.airtable.com/docs/formula-field-reference))

- `ISERROR(expr)` — true if `expr` evaluates to an error.
- `ERROR()` — produces the error value `#Error!`.
- `BLANK()` — produces a blank value.
- (`IFERROR(value, fallback)` exists in the Airtable function set and may be added if needed; not separately confirmed on the reference page in this research — see open questions.)

### 7.8 Recommended subset to implement

**In scope** (sufficient for the vast majority of `filterByFormula` filters):

1. **Literals**: number, double- and single-quoted strings (with `\"` / `\'` escapes), `TRUE()`, `FALSE()`, `BLANK()`.
2. **Field refs**: `{Field Name}` and bare single-word names; resolve unknown names to the `INVALID_FILTER_BY_FORMULA` error (§7.10).
3. **Operators**: `=`, `!=`, `<`, `>`, `<=`, `>=`, `+`, `-`, `*`, `/`, `&`, and parenthesized grouping.
4. **Logical**: `AND`, `OR`, `NOT`, `XOR`, `IF`, `SWITCH`.
5. **Text**: `CONCATENATE`, `LOWER`, `UPPER`, `LEN`, `TRIM`, `LEFT`, `RIGHT`, `MID`, `FIND`, `SEARCH`, `SUBSTITUTE`, `REPLACE`, `T`, `VALUE`.
6. **Number**: `ABS`, `ROUND`, `ROUNDUP`, `ROUNDDOWN`, `INT`, `MOD`, `CEILING`, `FLOOR`, `POWER`, `SQRT`, `MAX`, `MIN`, `SUM`, `AVERAGE`.
7. **Error**: `ISERROR`, `ERROR`.
8. **Truthiness rule** (§7, the include/exclude semantics): exclude on `0`, `false`/`FALSE()`, `""`, `NaN`, `[]`, `#Error!`; include otherwise.

**Out of scope** (parse-and-reject with `INVALID_FILTER_BY_FORMULA`, or stub as unsupported, rather than silently mis-evaluating):

- All **date/time** functions: `TODAY`, `NOW`, `DATEADD`, `DATETIME_DIFF`, `DATETIME_FORMAT`, `DATETIME_PARSE`, `IS_AFTER`, `IS_BEFORE`, `IS_SAME`, `WEEKDAY`, `WORKDAY`, `SET_TIMEZONE`, `SET_LOCALE`, `CREATED_TIME`, `LAST_MODIFIED_TIME`, etc. ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).
- All **array** functions: `ARRAYJOIN`, `ARRAYCOMPACT`, `ARRAYFLATTEN`, `ARRAYUNIQUE`, `ARRAYSLICE` (linked-record / multi-value semantics) ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).
- All **REGEX** functions: `REGEX_MATCH`, `REGEX_EXTRACT`, `REGEX_REPLACE` ([formula-field-reference](https://support.airtable.com/docs/formula-field-reference)).
- **Record / misc** functions: `RECORD_ID`, `ENCODE_URL_COMPONENT`, `COUNT`, `COUNTA`, `COUNTALL`, `EVEN`, `ODD`, `EXP`, `LOG`.
- Field IDs as references (optional — only name-based refs in the core subset; add ID support if the twin needs it).

### 7.9 Worked examples (verbatim idioms)

- Field equals a value: `{Name}='Alice'` or `{Name}="Alice"`.
- Field is not empty: `NOT({Notes}='')` ([Airtable Community](https://community.airtable.com/formulas-10/need-to-return-records-with-an-empty-field-33330)).
- Substring match (case-sensitive): `FIND("foo", {Title})` (non-matches yield `0` → excluded).
- Combined: `AND({Status}='Done', {Priority}>2)`.

### 7.10 Invalid-formula error response

A syntactically/semantically invalid formula does not filter — it fails the whole request with HTTP **422 Unprocessable Entity**. The error type is `INVALID_FILTER_BY_FORMULA`. The documented message text is "The formula for filtering records is invalid: Invalid formula. Please check your formula text.", and a field-not-found variant reads "Unknown field names: ..." ([Make Community 422](https://community.make.com/t/airtable-error-422-the-formula-for-filtering-records-is-invalid-invalid-formula-please-check-your-formula-text/16998); [Airtable Community](https://community.airtable.com/t5/development-apis/list-records-api-with-filterbyformula/td-p/155045)). The expected JSON shape (corroborated by third-party reports, not verified byte-for-byte against the JS-rendered API page):

```json
{
  "error": {
    "type": "INVALID_FILTER_BY_FORMULA",
    "message": "The formula for filtering records is invalid: Invalid formula. Please check your formula text."
  }
}
```

The twin should return this shape with `422` whenever the parser fails, an unknown field is referenced, or an unsupported (out-of-scope) function is encountered.


**Sources:** https://airtable.com/developers/web/api/list-records · https://support.airtable.com/docs/formula-field-reference · https://support.airtable.com/docs/common-formula-errors-and-how-to-fix-them · https://airtable-python-wrapper.readthedocs.io/en/master/params.html · https://community.airtable.com/formulas-10/need-to-return-records-with-an-empty-field-33330 · https://community.make.com/t/airtable-error-422-the-formula-for-filtering-records-is-invalid-invalid-formula-please-check-your-formula-text/16998 · https://community.airtable.com/t5/development-apis/list-records-api-with-filterbyformula/td-p/155045


## 8. Meta API

The Meta API exposes the authenticated identity and base schema (tables, fields, views), and lets you create/modify bases, tables, and fields. Base URL is `https://api.airtable.com`. All endpoints require `Authorization: Bearer <token>` (personal access token or OAuth access token). [src: https://airtable.com/developers/web/api/get-user-id-scopes]

### 8.1 Common error envelope

All Meta API errors return a JSON body of the shape `{ "error": { "type": "<TYPE>", "message": "<human readable>" } }` (some 4xx auth/encoding errors may use the bare `{ "error": "<TYPE>" }` form). [src: https://airtable.com/developers/web/api/errors]

| HTTP | `error.type` | Notes |
|------|--------------|-------|
| 400 | (request-encoding) | "Request encoding is invalid" — malformed request. |
| 401 | `AUTHENTICATION_REQUIRED` | Missing/invalid token: "Accessing protected resource without authorization". |
| 403 | `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` | "Invalid permissions, or the requested model was not found" (ambiguous perms/not-found). |
| 403 | `INVALID_PERMISSIONS` | Token lacks the required scope / role for the action. |
| 404 | `NOT_FOUND` | Resource not found. |
| 413 | (payload-too-large) | "Request exceeded maximum payload size". |
| 422 | `INVALID_REQUEST_UNKNOWN` | "Invalid request: parameter validation failed" — bad/missing body params. |
| 429 | `RATE_LIMIT_REACHED` | Rate limit exceeded (5 req/sec/base; ~30s cool-off). |
| 500 / 502 | (server) | Unexpected server error. |
| 503 | `RETRIABLE_ERROR` | "Server encountered an error; safe to retry". |

[src: https://airtable.com/developers/web/api/errors] — Exact verbatim messages for 401/404/500 are not published; see open questions.

---

### 8.2 GET /v0/meta/whoami — Get user ID and scopes

Returns the identity for the supplied token. Scope: none required (any valid token). [src: https://airtable.com/developers/web/api/get-user-id-scopes]

**Request**
```
GET https://api.airtable.com/v0/meta/whoami
Authorization: Bearer <token>
```

**Response 200 — fields**
- `id` (string, required) — user id, prefix `usr` (e.g. `usrL2PNC5o3H4lBEi`).
- `email` (string, optional) — present only when the token has the `user.email:read` scope.
- `scopes` (array<string>, optional) — present only for OAuth access tokens; the granted scope strings.

**Example (basic):**
```json
{ "id": "usrL2PNC5o3H4lBEi" }
```
**Example (with email scope):**
```json
{ "email": "foo@bar.com", "id": "usrL2PNC5o3H4lBEi" }
```
**Example (OAuth token, with scopes):**
```json
{ "id": "usrXXXXXXXXXXXXXX", "scopes": ["data.records:read", "schema.bases:read"] }
```
[src: https://airtable.com/developers/web/api/get-user-id-scopes ; scopes-array form confirmed via https://support.airtable.com/docs/getting-started-with-airtables-web-api]

---

### 8.3 GET /v0/meta/bases — List bases

Lists bases the token can access, **1000 bases at a time**. Scope: `schema.bases:read`. [src: https://airtable.com/developers/web/api/list-bases]

**Request**
```
GET https://api.airtable.com/v0/meta/bases
GET https://api.airtable.com/v0/meta/bases?offset=<offset>
```

**Query params**
- `offset` (string, optional) — pagination cursor returned by the previous page.

**Response 200 — fields**
- `bases` (array, required) of:
  - `id` (string, required) — base id, prefix `app`.
  - `name` (string, required).
  - `permissionLevel` (string, required) — enum: `none` | `read` | `comment` | `edit` | `create`.
- `offset` (string, optional) — present only when more pages exist; pass it back as `?offset=`.

**Example:**
```json
{
  "bases": [
    { "id": "appLkNDICXNqxSDhG", "name": "Apartment Hunting", "permissionLevel": "create" },
    { "id": "appSW9R5uCNmRmfl6", "name": "Project Tracker",    "permissionLevel": "edit" }
  ],
  "offset": "itrabc/appSW9R5uCNmRmfl6"
}
```
[src: https://airtable.com/developers/web/api/list-bases] — Exact `offset` token format is not documented; treat it as an opaque string.

---

### 8.4 GET /v0/meta/bases/{baseId}/tables — Get base schema

Returns all tables in a base with their fields and views. Scope: `schema.bases:read`. [src: https://airtable.com/developers/web/api/get-base-schema]

**Request**
```
GET https://api.airtable.com/v0/meta/bases/{baseId}/tables
GET https://api.airtable.com/v0/meta/bases/{baseId}/tables?include[]=visibleFieldIds
```

**Query params**
- `include` (array<"visibleFieldIds">, optional) — when set, adds `visibleFieldIds` to grid `views`.

**Response 200 — shape**
- `tables` (array) of Table:
  - `id` (string) — prefix `tbl`.
  - `name` (string).
  - `description` (string, optional).
  - `primaryFieldId` (string) — id of the table's primary field.
  - `fields` (array of Field — see §8.8).
  - `views` (array of View): `{ id (prefix "viw"), name, type, visibleFieldIds? }`. `view.type` enum: `grid` | `form` | `calendar` | `gallery` | `kanban` | `timeline` | `block`. `visibleFieldIds` appears only for grid views and only when requested via `include`.

**Verbatim example response** (two linked tables; note `multipleRecordLinks` and `multipleAttachments` option shapes):
```json
{
  "tables": [
    {
      "description": "Apartments to track.",
      "fields": [
        { "description": "Name of the apartment", "id": "fld1VnoyuotSTyxW1", "name": "Name", "type": "singleLineText" },
        { "id": "fldoaIqdn5szURHpw", "name": "Pictures", "options": { "isReversed": false }, "type": "multipleAttachments" },
        { "id": "fldumZe00w09RYTW6", "name": "District",
          "options": { "inverseLinkFieldId": "fldWnCJlo2z6ttT8Y", "isReversed": false, "linkedTableId": "tblK6MZHez0ZvBChZ", "prefersSingleRecordLink": true },
          "type": "multipleRecordLinks" }
      ],
      "id": "tbltp8DGLhqbUmjK1",
      "name": "Apartments",
      "primaryFieldId": "fld1VnoyuotSTyxW1",
      "views": [ { "id": "viwQpsuEDqHFqegkp", "name": "Grid view", "type": "grid" } ]
    },
    {
      "fields": [
        { "id": "fldEVzvQOoULO38yl", "name": "Name", "type": "singleLineText" },
        { "description": "Apartments that belong to this district", "id": "fldWnCJlo2z6ttT8Y", "name": "Apartments",
          "options": { "inverseLinkFieldId": "fldumZe00w09RYTW6", "isReversed": false, "linkedTableId": "tbltp8DGLhqbUmjK1", "prefersSingleRecordLink": false },
          "type": "multipleRecordLinks" }
      ],
      "id": "tblK6MZHez0ZvBChZ",
      "name": "Districts",
      "primaryFieldId": "fldEVzvQOoULO38yl",
      "views": [ { "id": "viwi3KXvrKug2mIBS", "name": "Grid view", "type": "grid" } ]
    }
  ]
}
```
[src: https://airtable.com/developers/web/api/get-base-schema]

---

### 8.5 POST /v0/meta/bases — Create base

Creates a base in a workspace with one or more tables. Scope: `schema.bases:write`. [src: https://airtable.com/developers/web/api/create-base]

**Request body**
- `name` (string, required).
- `workspaceId` (string, required) — prefix `wsp`.
- `tables` (array, required) of table configs (≥1 table, each with ≥1 field; first field must be a valid primary-field type):
  - `name` (string, required), `description` (string, optional), `fields` (array, required) of `{ name, type, description?, options? }`.

**Verbatim example request:**
```json
{
  "name": "Apartment Hunting",
  "tables": [
    {
      "description": "A to-do list of places to visit",
      "fields": [
        { "description": "Name of the apartment", "name": "Name", "type": "singleLineText" },
        { "name": "Address", "type": "singleLineText" },
        { "name": "Visited", "options": { "color": "greenBright", "icon": "check" }, "type": "checkbox" }
      ],
      "name": "Apartments"
    }
  ],
  "workspaceId": "wspmhESAta6clCCwF"
}
```

**Response 200 — shape**: `{ id (string, base id prefix "app"), tables (array of full Table models with generated field/table/view ids + auto-created default grid view) }`.

**Verbatim example response:**
```json
{
  "id": "appLkNDICXNqxSDhG",
  "tables": [
    {
      "description": "A to-do list of places to visit",
      "fields": [
        { "description": "Name of the apartment", "id": "fld1VnoyuotSTyxW1", "name": "Name", "type": "singleLineText" },
        { "id": "fldoi0c3GaRQJ3xnI", "name": "Address", "type": "singleLineText" },
        { "id": "fldumZe00w09RYTW6", "name": "Visited", "options": { "color": "redBright", "icon": "star" }, "type": "checkbox" }
      ],
      "id": "tbltp8DGLhqbUmjK1",
      "name": "Apartments",
      "primaryFieldId": "fld1VnoyuotSTyxW1",
      "views": [ { "id": "viwQpsuEDqHFqegkp", "name": "Grid view", "type": "grid" } ]
    }
  ]
}
```
Note: the response echoes server-normalized option values (the request's checkbox `greenBright`/`check` comes back as `redBright`/`star` in Airtable's published example — the twin should be permissive about what it stores vs. returns here, or simply echo the request faithfully). [src: https://airtable.com/developers/web/api/create-base]

---

### 8.6 Create / Update Table

**POST /v0/meta/bases/{baseId}/tables — Create table.** Scope: `schema.bases:write`. [src: https://airtable.com/developers/web/api/create-table]

Request body: `{ name (required), description? (≤20000 chars), fields[] (required) }` where each field is `{ name, type, description?, options? }`.

Response 200: a full Table model `{ id, name, description?, primaryFieldId, fields[], views[] }` with generated ids and an auto-created default grid view. (`dateDependencySettings` may also appear.)

Verbatim example request:
```json
{
  "description": "A to-do list of places to visit",
  "fields": [
    { "description": "Name of the apartment", "name": "Name", "type": "singleLineText" },
    { "name": "Address", "type": "singleLineText" },
    { "name": "Visited", "options": { "color": "greenBright", "icon": "check" }, "type": "checkbox" }
  ],
  "name": "Apartments"
}
```
Verbatim example response:
```json
{
  "description": "A to-do list of places to visit",
  "fields": [
    { "description": "Name of the apartment", "id": "fld1VnoyuotSTyxW1", "name": "Name", "type": "singleLineText" },
    { "id": "fldoi0c3GaRQJ3xnI", "name": "Address", "type": "singleLineText" },
    { "id": "fldumZe00w09RYTW6", "name": "Visited", "options": { "color": "redBright", "icon": "star" }, "type": "checkbox" }
  ],
  "id": "tbltp8DGLhqbUmjK1",
  "name": "Apartments",
  "primaryFieldId": "fld1VnoyuotSTyxW1",
  "views": [ { "id": "viwQpsuEDqHFqegkp", "name": "Grid view", "type": "grid" } ]
}
```

**PATCH /v0/meta/bases/{baseId}/tables/{tableIdOrName} — Update table.** Scope: `schema.bases:write`. Patchable body fields: `name?`, `description?` (≤20000 chars), `dateDependencySettings?`. Returns the full updated Table model (same shape as create — includes `fields` and `views`). [src: https://airtable.com/developers/web/api/update-table]

Verbatim example request:
```json
{ "description": "I was changed!", "name": "Apartments (revised)" }
```
Response: the full Table model with `name`/`description` updated and the unchanged `fields`/`views`/`primaryFieldId` echoed (e.g. `"id": "tbltp8DGLhqbUmjK1"`, `"name": "Apartments (revised)"`).

---

### 8.7 Create / Update Field

**POST /v0/meta/bases/{baseId}/tables/{tableId}/fields — Create field.** Scope: `schema.bases:write`. [src: https://airtable.com/developers/web/api/create-field]

Request body: `{ name (required), type (required), description? (≤20000 chars), options? (required-or-optional depending on type) }`. The endpoint has 34 type-specific request variants. Response 200: `{ id (prefix "fld"), name, type, description?, options? }`.

Verbatim example (checkbox):
```json
// request
{ "name": "Visited", "type": "checkbox", "description": "Whether I have visited this apartment yet.",
  "options": { "color": "greenBright", "icon": "check" } }
// response 200
{ "id": "fldumZe00w09RYTW6", "name": "Visited", "type": "checkbox",
  "description": "Whether I have visited this apartment yet.",
  "options": { "color": "redBright", "icon": "star" } }
```

**PATCH /v0/meta/bases/{baseId}/tables/{tableId}/fields/{columnId} — Update field.** Scope: `schema.bases:write`. Updatable: `name?`, `description?` (≤20000 chars), and type-specific `options?` (e.g. `options.formula` for formula fields). Returns `{ id, name, type, description?, options? }`. [src: https://airtable.com/developers/web/api/update-field]

Verbatim example:
```json
// request
{ "description": "I was changed!", "name": "Name (revised)" }
// response 200
{ "description": "I was changed!", "id": "fldoi0c3GaRQJ3xnI", "name": "Name (revised)", "type": "singleLineText" }
```
Note: field **type cannot be changed** via PATCH (only name/description/options). [src: https://airtable.com/developers/web/api/update-field]

---

### 8.8 Field type catalog & `options` shapes

`type` is one of the strings below; `options` is `null`/absent when "(none)". All from the field model reference. [src: https://airtable.com/developers/web/api/field-model]

| `type` | `options` shape |
|--------|-----------------|
| `singleLineText` | (none) |
| `multilineText` | (none) |
| `richText` | (none) |
| `email` | (none) |
| `url` | (none) |
| `phoneNumber` | (none) |
| `number` | `{ "precision": <int 0–8> }` |
| `currency` | `{ "precision": <int>, "symbol": "<string>" }` |
| `percent` | `{ "precision": <int> }` |
| `duration` | `{ "durationFormat": "h:mm" \| "h:mm:ss" \| "h:mm:ss.S" \| "h:mm:ss.SS" \| "h:mm:ss.SSS" }` |
| `rating` | `{ "icon": "star"\|"heart"\|"thumbsUp"\|"flag"\|"dot", "color": <bright color>, "max": <int 1–10> }` |
| `checkbox` | `{ "icon": "check"\|"xCheckbox"\|"star"\|"heart"\|"thumbsUp"\|"flag"\|"dot", "color": <bright color> }` |
| `singleSelect` | `{ "choices": [ { "id": "<string>", "name": "<string>", "color"?: <select color> } ] }` |
| `multipleSelects` | `{ "choices": [ { "id"?: "<string>", "name": "<string>", "color"?: <select color> } ] }` |
| `singleCollaborator` | `{}` (optional) |
| `multipleCollaborators` | `{}` |
| `date` | `{ "dateFormat": { "name": "local"\|"friendly"\|"us"\|"european"\|"iso", "format"?: <token> } }` |
| `dateTime` | `{ "timeZone": "<Timezone>", "dateFormat": { "name", "format"? }, "timeFormat": { "name": "12hour"\|"24hour", "format"?: "h:mma"\|"HH:mm" } }` |
| `multipleAttachments` | `{ "isReversed": <bool> }` |
| `multipleRecordLinks` | `{ "linkedTableId": "<tbl…>", "isReversed": <bool>, "prefersSingleRecordLink": <bool>, "inverseLinkFieldId"?: "<fld…>", "viewIdForRecordSelection"?: "<viw…>" }` |
| `multipleLookupValues` (Lookup) | `{ "recordLinkFieldId": "<fld…>", "fieldIdInLinkedTable": "<fld…>", "isValid": <bool>, "result": <Field-config or null> }` |
| `rollup` | `{ "recordLinkFieldId"?: "<fld…>", "fieldIdInLinkedTable"?: "<fld…>", "referencedFieldIds"?: [<fld…>], "isValid"?: <bool>, "result"?: <Field-config or null> }` |
| `count` | `{ "isValid": <bool>, "recordLinkFieldId"?: "<fld…>" }` |
| `formula` | `{ "formula": "<string>", "isValid": <bool>, "referencedFieldIds": [<fld…> or null], "result": <Field-config or null> }` |
| `autoNumber` | (none, read-only) |
| `barcode` | (none) |
| `button` | (none, read-only) |
| `createdTime` | `{ "result"?: <date or dateTime Field-config> }` (read-only) |
| `lastModifiedTime` | `{ "isValid": <bool>, "referencedFieldIds": [<fld…> or null], "result"?: <date or dateTime Field-config> }` (read-only) |
| `createdBy` | (none, read-only) |
| `lastModifiedBy` | (none, read-only) |
| `aiText` | `{ "prompt"?: [...], "referencedFieldIds"?: [<fld…>] }` (read-only) |
| `externalSyncSource` (Sync source) | `{ "choices": [ { "id": "<string>", "name": "<string>", "color"?: <select color> } ] }` |

**Select-choice color enum** (`color` for `singleSelect`/`multipleSelects`/`externalSyncSource`) — 40 values, pattern `{hue}{Light2|Light1|Bright|Dark1}` over hues `blue, cyan, teal, green, yellow, orange, red, pink, purple, gray`:
```
blueLight2  cyanLight2  tealLight2  greenLight2  yellowLight2  orangeLight2  redLight2  pinkLight2  purpleLight2  grayLight2
blueLight1  cyanLight1  tealLight1  greenLight1  yellowLight1  orangeLight1  redLight1  pinkLight1  purpleLight1  grayLight1
blueBright  cyanBright  tealBright  greenBright  yellowBright  orangeBright  redBright  pinkBright  purpleBright  grayBright
blueDark1   cyanDark1   tealDark1   greenDark1   yellowDark1   orangeDark1   redDark1   pinkDark1   purpleDark1   grayDark1
```
**Bright color enum** (used by `checkbox.color` and `rating.color`): the `*Bright` subset only — `greenBright, tealBright, cyanBright, blueBright, purpleBright, pinkBright, redBright, orangeBright, yellowBright, grayBright`.

**Date format tokens** (`dateFormat.format` by `name`): `local`→`l`, `friendly`→`LL`, `us`→`M/D/YYYY`, `european`→`D/M/YYYY`, `iso`→`YYYY-MM-DD`. **Time format**: `12hour`→`h:mma`, `24hour`→`HH:mm`.

[src for entire §8.8: https://airtable.com/developers/web/api/field-model]


**Sources:** https://airtable.com/developers/web/api/get-user-id-scopes · https://airtable.com/developers/web/api/list-bases · https://airtable.com/developers/web/api/get-base-schema · https://airtable.com/developers/web/api/create-base · https://airtable.com/developers/web/api/create-table · https://airtable.com/developers/web/api/update-table · https://airtable.com/developers/web/api/create-field · https://airtable.com/developers/web/api/update-field · https://airtable.com/developers/web/api/field-model · https://airtable.com/developers/web/api/errors · https://support.airtable.com/docs/getting-started-with-airtables-web-api


## 9. Comments API

Record comments live under a record path and share one base URL:

```
https://api.airtable.com/v0/{baseId}/{tableIdOrName}/{recordId}/comments
```

`{tableIdOrName}` accepts either the table ID (`tblXXXXXXXXXXXXXX`) or the table name; `{recordId}` is a `recXXXXXXXXXXXXXX` ID. All requests require `Authorization: Bearer <token>`. [Source: https://airtable.com/developers/web/api/list-comments]

**Required scopes / roles**
- List: scope `data.recordComments:read`, minimum role *Base read-only*. [Source: https://airtable.com/developers/web/api/list-comments]
- Create / Update / Delete: scope `data.recordComments:write`, minimum role *Base commenter*. [Source: https://airtable.com/developers/web/api/create-comment, https://airtable.com/developers/web/api/update-comment, https://airtable.com/developers/web/api/delete-comment]
- Update and Delete are restricted to the comment's own author for non-admin users; Enterprise Admins may delete others' comments. [Source: https://airtable.com/developers/web/api/update-comment, https://airtable.com/developers/web/api/delete-comment]

### 9.1 The comment object

Returned by create, update, and inside the `comments` array of list:

```json
{
  "id": "comXXXXXXXXXXXXXX",
  "author": {
    "id": "usrXXXXXXXXXXXXXX",
    "email": "collaborator@example.com",
    "name": "Alex Smith"
  },
  "text": "Hello, @[usrL2PNC5o3H4lBEi]!",
  "createdTime": "2021-03-01T09:00:00.000Z",
  "lastUpdatedTime": null,
  "parentCommentId": "comXXXXXXXXXXXXXX",
  "mentioned": {
    "usrL2PNC5o3H4lBEi": {
      "id": "usrL2PNC5o3H4lBEi",
      "email": "mentioned@example.com",
      "displayName": "Jordan Lee",
      "type": "user"
    }
  },
  "reactions": [],
  "attachments": []
}
```

Field notes:
- `id` — string, comment ID, `com`-prefixed (delete example returns `"comB5z37Mg9zaEPw6"`). Required. [Source: https://airtable.com/developers/web/api/delete-comment]
- `author` — object, **required**, with `id` (string), `email` (string), and optional `name` (string). [Source: https://airtable.com/developers/web/api/list-comments]
- `text` — string, **required**, the comment body; may embed user mentions. [Source: https://airtable.com/developers/web/api/create-comment]
- `createdTime` — string, **required**, ISO 8601 (e.g. `"2021-03-01T09:00:00.000Z"`). [Source: https://airtable.com/developers/web/api/create-comment]
- `lastUpdatedTime` — string or `null`, **required**; `null` until the comment is edited, then the ISO timestamp of the last edit (e.g. `"2021-04-01T09:00:00.000Z"`). [Source: https://airtable.com/developers/web/api/update-comment]
- `parentCommentId` — string, optional; present on threaded replies, references the parent comment's ID. [Source: https://airtable.com/developers/web/api/list-comments]
- `mentioned` — object, optional; map keyed by mentioned user ID. Each value is `{ id, email, displayName, type }` where `type` is `"user"`. Confirmed by pyAirtable's `Comment.mentioned` model (`display_name`, `email`, `id`, `type`). [Source: https://airtable.com/developers/web/api/create-comment, https://pyairtable.readthedocs.io/en/stable/tables.html]
- `reactions` — array, optional; emoji reactions, each with `emoji` and reacting-user data. [Source: https://airtable.com/developers/web/api/list-comments]
- `attachments` — array, optional; each with `id`, `filename`, `url`, `type`, and dimensions. [Source: https://airtable.com/developers/web/api/list-comments]

**Mention syntax:** inside `text`, mentions are written `@[userId]`, e.g. `@[usrL2PNC5o3H4lBEi]`, with a matching entry in `mentioned`. [Source: https://airtable.com/developers/web/api/create-comment]

### 9.2 List comments

`GET /v0/{baseId}/{tableIdOrName}/{recordId}/comments`

Query parameters:

| Parameter | Type | Default | Constraint |
|-----------|--------|---------|------------|
| `pageSize` | integer | `100` | must be ≤ `100` |
| `offset` | string | — | pagination pointer from the previous page |

[Source: https://airtable.com/developers/web/api/list-comments]

Response `200`:

```json
{
  "comments": [
    {
      "id": "comXXXXXXXXXXXXXX",
      "author": {
        "id": "usrXXXXXXXXXXXXXX",
        "email": "collaborator@example.com",
        "name": "Alex Smith"
      },
      "text": "This is a comment.",
      "createdTime": "2021-03-01T09:00:00.000Z",
      "lastUpdatedTime": null
    }
  ],
  "offset": "abc123"
}
```

Top-level fields: `comments` (array of comment objects) and `offset` (string or `null`). Pagination follows Airtable's standard offset model: when the response includes an `offset`, pass it back as the `offset` query param to fetch the next page; when `offset` is absent/`null`, the last page has been reached. [Source: https://airtable.com/developers/web/api/list-comments, https://community.airtable.com/automations-8/acessing-record-comments-via-script-sync-or-api-46452]

### 9.3 Create comment

`POST /v0/{baseId}/{tableIdOrName}/{recordId}/comments`

Request body:

```json
{
  "text": "Hello, world!",
  "parentCommentId": "comXXXXXXXXXXXXXX"
}
```

- `text` — string, **required**.
- `parentCommentId` — string, optional; set to reply within a thread.

[Source: https://airtable.com/developers/web/api/create-comment]

Response `200` is the full comment object (§9.1), with `lastUpdatedTime: null` and any resolved mentions populated in `mentioned`. [Source: https://airtable.com/developers/web/api/create-comment]

### 9.4 Update comment

`PATCH /v0/{baseId}/{tableIdOrName}/{recordId}/comments/{rowCommentId}`

Request body:

```json
{
  "text": "Update, world!"
}
```

- `text` — string, **required** (the only updatable field).

Response `200` is the full comment object with `text` updated and `lastUpdatedTime` set to the edit time, e.g. `"text": "Update, world!"`, `"lastUpdatedTime": "2021-04-01T09:00:00.000Z"`. Non-admin users can only update their own comments. [Source: https://airtable.com/developers/web/api/update-comment]

### 9.5 Delete comment

`DELETE /v0/{baseId}/{tableIdOrName}/{recordId}/comments/{rowCommentId}`

Response `200`:

```json
{
  "id": "comB5z37Mg9zaEPw6",
  "deleted": true
}
```

- `id` — string, **required**, the deleted comment's ID.
- `deleted` — boolean, **required**, always `true` on success.

Non-admin users can only delete their own comments; Enterprise Admins can delete others'. [Source: https://airtable.com/developers/web/api/delete-comment]

### 9.6 Error behavior (for the twin)

Airtable's standard Web API error envelope applies across these endpoints:

```json
{ "error": { "type": "ERROR_TYPE", "message": "..." } }
```

- Missing/invalid token → `401 UNAUTHORIZED`.
- Token/user lacks the comment scope or role, or the base/table/record ID is wrong → `403` with type `INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND` and message *"Invalid permissions, or the requested model was not found. Check that both your user and your token have the required permissions, and that the model names and/or ids are correct."* [Source: https://support.airtable.com/docs/airtable-api-common-troubleshooting]
- `pageSize` > 100 → `422` (standard Airtable validation error for out-of-range query params). *(Exact type/message for comments not verbatim-confirmed — see open questions.)*


**Sources:** https://airtable.com/developers/web/api/list-comments · https://airtable.com/developers/web/api/create-comment · https://airtable.com/developers/web/api/update-comment · https://airtable.com/developers/web/api/delete-comment · https://pyairtable.readthedocs.io/en/stable/tables.html · https://support.airtable.com/docs/airtable-api-common-troubleshooting · https://community.airtable.com/automations-8/acessing-record-comments-via-script-sync-or-api-46452


## 10. Webhooks API

The Webhooks API notifies a consumer in real time about changes in a base. The flow is two-phase: (1) Airtable POSTs a tiny **ping** to your `notificationUrl` saying "something changed"; (2) you then call **List webhook payloads** to pull the actual change data, advancing a per-webhook cursor. For the local twin, the payloads endpoint is the "generated events" stream and the ping is the out-of-band notification. ([overview](https://airtable.com/developers/web/api/webhooks-overview), [support overview](https://support.airtable.com/docs/airtable-webhooks-api-overview))

All endpoints are rooted at `https://api.airtable.com/v0/bases/{baseId}/webhooks`. Authentication is `Authorization: Bearer YOUR_TOKEN` (personal access token or OAuth). Management endpoints require the `webhook:manage` scope; reading payloads additionally requires scopes matching the subscribed `dataTypes` (`data.records:read` for `tableData`, `schema.bases:read` for `tableFields`/`tableMetadata`). Creating/refreshing/deleting/enabling requires **Creator**-level access to the base. ([create](https://airtable.com/developers/web/api/create-a-webhook), [list payloads](https://airtable.com/developers/web/api/list-webhook-payloads), [overview](https://airtable.com/developers/web/api/webhooks-overview))

Webhook IDs are prefixed `ach` (e.g. `ach00000000000000`). ([create](https://airtable.com/developers/web/api/create-a-webhook))

### 10.1 Create a webhook

`POST /v0/bases/{baseId}/webhooks` ([create](https://airtable.com/developers/web/api/create-a-webhook))

Request body:
- `notificationUrl` (string, optional) — URL Airtable pings. If omitted, no pings are sent and you must poll payloads.
- `specification.options.filters` (required):
  - `dataTypes` (array, **required**) — one or more of `"tableData"` (record/cell changes), `"tableFields"` (field/schema changes), `"tableMetadata"` (table name/description changes).
  - `recordChangeScope` (string, optional) — a `tblXXX` or `viwXXX` to scope notifications to one table/view. Form view and List view are not supported.
  - `changeTypes` (array, optional) — subset of `"add" | "remove" | "update"`.
  - `fromSources` (array, optional) — subset of `"client" | "publicApi" | "formSubmission" | "formPageSubmission" | "automation" | "system" | "sync" | "anonymousUser" | "unknown"`.
  - `watchDataInFieldIds` (array of `fldXXX`, optional) — only emit when these fields' data changes.
  - `watchSchemasOfFieldIds` (array of `fldXXX`, optional) — only emit on schema changes to these fields.
  - `sourceOptions` (object, optional) — `formSubmission.viewId` or `formPageSubmission.pageId` for source-specific filtering.
- `specification.options.includes` (object, optional):
  - `includePreviousCellValues` (boolean) — include `previous` cell values in record-change payloads.
  - `includePreviousFieldDefinitions` (boolean) — include `previous` field definitions in field-change payloads.

([create](https://airtable.com/developers/web/api/create-a-webhook), [specification model](https://airtable.com/developers/web/api/model/webhooks-specification))

Example request:
```json
{
  "notificationUrl": "https://foo.com/receive-ping",
  "specification": {
    "options": {
      "filters": {
        "dataTypes": ["tableData"],
        "recordChangeScope": "tbltp8DGLhqbUmjK1"
      }
    }
  }
}
```

Example response (`200`):
```json
{
  "id": "ach00000000000000",
  "macSecretBase64": "someBase64MacSecret",
  "expirationTime": "2023-01-20T00:00:00.000Z"
}
```
- `macSecretBase64` — base64 secret used to verify ping signatures. **Returned only on creation; cannot be retrieved later.** The twin must generate and remember one per webhook.
- `expirationTime` — ISO 8601; `null` when using a (legacy) user API key. Webhooks created with PATs/OAuth expire **7 days** after creation. ([create](https://airtable.com/developers/web/api/create-a-webhook), [overview](https://airtable.com/developers/web/api/webhooks-overview))

Invalid filter specs are rejected at create time; the same `INVALID_FILTERS` condition can also surface later as an error payload (see 10.5). ([payload model](https://airtable.com/developers/web/api/model/webhooks-payload))

### 10.2 List webhooks

`GET /v0/bases/{baseId}/webhooks` — scope `webhook:manage`. ([list](https://airtable.com/developers/web/api/list-webhooks))

Example response (`200`):
```json
{
  "webhooks": [
    {
      "id": "ach00000000000000",
      "specification": {
        "options": {
          "filters": {
            "dataTypes": ["tableData"],
            "recordChangeScope": "tbltp8DGLhqbUmjK1"
          }
        }
      },
      "notificationUrl": "https://foo.com/receive-ping",
      "cursorForNextPayload": 1,
      "isHookEnabled": true,
      "areNotificationsEnabled": true,
      "expirationTime": "2023-01-20T00:00:00.000Z",
      "lastSuccessfulNotificationTime": "2022-02-01T21:25:05.663Z",
      "lastNotificationResult": {
        "success": true,
        "completionTimestamp": "2022-02-01T21:25:05.663Z",
        "durationMs": 2.603,
        "retryNumber": 0
      }
    }
  ]
}
```
Per-webhook fields: `id`, `specification`, `notificationUrl` (string|null), `cursorForNextPayload` (number; next cursor to read), `isHookEnabled` (bool), `areNotificationsEnabled` (bool), `expirationTime` (string|null, optional), `lastSuccessfulNotificationTime` (string|null), `lastNotificationResult` (object|null, see 10.7). ([list](https://airtable.com/developers/web/api/list-webhooks), [notification model](https://airtable.com/developers/web/api/model/webhooks-notification))

### 10.3 Delete a webhook

`DELETE /v0/bases/{baseId}/webhooks/{webhookId}` — scope `webhook:manage`, Creator role. Notifications stop immediately. ([delete](https://airtable.com/developers/web/api/delete-a-webhook))

> **Open question:** the docs say it "returns object" but do not show the exact success status/body. Conventionally `200 {}` (Airtable's other delete-style endpoints return a small JSON body rather than `204`). Treat the exact shape as unconfirmed.

### 10.4 Refresh a webhook

`POST /v0/bases/{baseId}/webhooks/{webhookId}/refresh` — scope `webhook:manage`, Creator role. No request body. Extends the life of an active, expiring webhook by another 7 days. Only applies to webhooks that have an `expirationTime`. ([refresh](https://airtable.com/developers/web/api/refresh-a-webhook), [overview](https://airtable.com/developers/web/api/webhooks-overview))

Example response (`200`):
```json
{
  "expirationTime": "2023-01-30T00:00:00.000Z"
}
```
`expirationTime` is `string | null`. Note: successfully calling **List webhook payloads** also extends expiration by 7 days. ([refresh](https://airtable.com/developers/web/api/refresh-a-webhook), [overview](https://airtable.com/developers/web/api/webhooks-overview))

### 10.5 List webhook payloads (the generated-events stream)

`GET /v0/bases/{baseId}/webhooks/{webhookId}/payloads` — scope depends on subscribed `dataTypes`; Base read access is sufficient. ([list payloads](https://airtable.com/developers/web/api/list-webhook-payloads))

Query parameters:
- `cursor` (number, optional, default `1`) — transaction number to start from. Use the previous response's `cursor` to page forward.
- `limit` (number, optional) — max payloads per response; **capped at 50**.

Response envelope:
- `payloads` (array) — payload objects, oldest-first.
- `cursor` (number) — the transaction number that would immediately follow the last returned payload; pass it back as `cursor` next time.
- `mightHaveMore` (boolean) — `true` if more payloads may be available immediately (keep paging with the new `cursor`).

([list payloads](https://airtable.com/developers/web/api/list-webhook-payloads), [payload model](https://airtable.com/developers/web/api/model/webhooks-payload))

Minimal example response (`200`):
```json
{
  "payloads": [
    {
      "timestamp": "2022-02-01T21:25:05.663Z",
      "baseTransactionNumber": 4,
      "payloadFormat": "v0",
      "actionMetadata": {
        "source": "client",
        "sourceMetadata": {
          "user": {
            "id": "usr00000000000000",
            "email": "foo@bar.com",
            "permissionLevel": "create"
          }
        }
      }
    }
  ],
  "cursor": 5,
  "mightHaveMore": false
}
```

### 10.6 Payload object shape (record created / updated / destroyed)

Each payload object: ([payload model](https://airtable.com/developers/web/api/model/webhooks-payload), [table-changed model](https://airtable.com/developers/web/api/model/webhooks-table-changed))
- `timestamp` (string, ISO 8601) — when the change happened.
- `baseTransactionNumber` (number) — base-wide, sequentially increasing transaction number; scoped to the webhook and strictly increasing, so consumers can de-dupe/order.
- `payloadFormat` (string) — currently `"v0"`.
- `actionMetadata` (object, required) — `source` + `sourceMetadata`. `source` is one of the `fromSources` values (e.g. `client`, `publicApi`, `automation`, `formSubmission`, `sync`, `anonymousUser`, `system`, `unknown`); for `client` source, `sourceMetadata.user` carries `{ id, email, permissionLevel }`. Airtable notes it may add sources/metadata without it being a breaking change.
- `changedTablesById` (object, optional) — keyed by `tblXXX`; value is a **table-changed** object (see below). This carries record create/update/destroy and field/metadata changes.
- `createdTablesById` (object, optional) — keyed by `tblXXX`; newly created tables.
- `destroyedTableIds` (array of `tblXXX`, optional) — deleted tables.

Error payloads (appear in the stream instead of a change payload):
- `error` (boolean, `true`).
- `code` (string) — one of `"INVALID_FILTERS" | "INVALID_HOOK" | "INTERNAL_ERROR"`.

([payload model](https://airtable.com/developers/web/api/model/webhooks-payload))

**Table-changed object** (the value inside `changedTablesById[tableId]`) — all keys optional, present only when relevant and permitted by the spec/`includes`: ([table-changed model](https://airtable.com/developers/web/api/model/webhooks-table-changed))
- `createdRecordsById` — `{ "<recordId>": { "createdTime": "<ISO>", "cellValuesByFieldId": { "<fieldId>": <value> } } }`
- `changedRecordsById` — `{ "<recordId>": { "current": { "cellValuesByFieldId": { "<fieldId>": <value> } }, "previous": { "cellValuesByFieldId": { "<fieldId>": <value> } }, "unchanged": { "cellValuesByFieldId": { "<fieldId>": <value> } } } }`. `previous` is present only when `includePreviousCellValues` was set.
- `destroyedRecordIds` — array of `recXXX`.
- `createdFieldsById` — `{ "<fieldId>": { "name": <string>, "type": <fieldType> } }`
- `changedFieldsById` — `{ "<fieldId>": { "current": { "name", "type" }, "previous": { "name", "type" } } }` (`previous` gated by `includePreviousFieldDefinitions`).
- `destroyedFieldIds` — array of `fldXXX`.
- `changedMetadata` — `{ "current": { "name": <string>, "description": <string|null> }, "previous": { "name": <string>, "description": <string|null> } }` (table name/description changes).
- `changedViewsById` — `{ "<viewId>": { "createdRecordsById": {...}, "changedRecordsById": {...}, "destroyedRecordIds": [...] } }` (view-scoped record changes).

Illustrative full payload covering create + update + destroy (field/cell IDs are placeholders; assemble from the field shapes above):
```json
{
  "payloads": [
    {
      "timestamp": "2023-09-15T18:30:00.000Z",
      "baseTransactionNumber": 7,
      "payloadFormat": "v0",
      "actionMetadata": {
        "source": "client",
        "sourceMetadata": {
          "user": { "id": "usr00000000000000", "email": "foo@bar.com", "permissionLevel": "create" }
        }
      },
      "changedTablesById": {
        "tbltp8DGLhqbUmjK1": {
          "createdRecordsById": {
            "rec00000000000001": {
              "createdTime": "2023-09-15T18:30:00.000Z",
              "cellValuesByFieldId": { "fld0000000000000A": "New value" }
            }
          },
          "changedRecordsById": {
            "rec00000000000002": {
              "current": { "cellValuesByFieldId": { "fld0000000000000A": "Updated value" } },
              "previous": { "cellValuesByFieldId": { "fld0000000000000A": "Old value" } }
            }
          },
          "destroyedRecordIds": ["rec00000000000003"]
        }
      }
    }
  ],
  "cursor": 8,
  "mightHaveMore": false
}
```
*(Sources: [payload model](https://airtable.com/developers/web/api/model/webhooks-payload), [table-changed model](https://airtable.com/developers/web/api/model/webhooks-table-changed). The combined example is assembled from the documented field shapes; the `previous` block appears only when `includePreviousCellValues` is enabled.)*

> **Open question:** the exact JSON encoding of `<value>` inside `cellValuesByFieldId` per field type (e.g. linked records, attachments, collaborators) is not spelled out on the webhook pages — it follows the base's normal cell-value JSON, but verify against the field-types model when implementing.

### 10.7 The ping notification (POST to `notificationUrl`)

When a change matches the spec, Airtable POSTs a small envelope to `notificationUrl`. Your endpoint should respond `200`/`204` with an empty body. The ping contains **no change data** — it only tells you to go fetch payloads. ([overview](https://airtable.com/developers/web/api/webhooks-overview), [support overview](https://support.airtable.com/docs/airtable-webhooks-api-overview))

Ping body:
```json
{
  "base": { "id": "app00000000000000" },
  "webhook": { "id": "ach00000000000000" },
  "timestamp": "2022-02-01T21:25:05.663Z"
}
```

**Signature:** each ping carries an `X-Airtable-Content-MAC` header for verification. Compute `HMAC-SHA256` over the **raw request body** using the **base64-decoded** `macSecretBase64` (decoded to bytes) as the key, hex-encode the digest, and prefix with `hmac-sha256=`. The header value equals `"hmac-sha256=" + hex(hmac_sha256(decode_base64(macSecret), rawBody))`. ([overview](https://airtable.com/developers/web/api/webhooks-overview), corroborated [community thread](https://community.airtable.com/development-apis-11/not-able-to-match-x-airtable-content-mac-header-from-webhook-request-4316))

**Notification result object** (`lastNotificationResult` and entries surfaced via list): ([notification model](https://airtable.com/developers/web/api/model/webhooks-notification))
- `success` (boolean)
- `completionTimestamp` (string) — time of the most recent notification attempt
- `durationMs` (number) — round-trip duration of the network call
- `retryNumber` (number) — retry count (0 = first try)
- When `success: false`: `error` (object, `{ "message": <string> }`) and `willBeRetried` (boolean).

Example failure result:
```json
{
  "success": false,
  "completionTimestamp": "2022-02-01T21:25:05.663Z",
  "durationMs": 2.603,
  "retryNumber": 1,
  "error": { "message": "..." },
  "willBeRetried": true
}
```

**Retry/disable behavior:** failed pings retry up to ~13 times with exponential backoff over roughly a day; after exhausting retries, notifications are auto-disabled (`areNotificationsEnabled: false`) but payload generation continues, so payloads remain pullable. ([overview](https://airtable.com/developers/web/api/webhooks-overview))

> **Open question:** the docs describe `error` as `{ message }` only and do **not** publish named error codes (e.g. `CANNOT_DELIVER`/`HOOK_EXPIRED`); do not assume specific codes for the twin's failure results.

### 10.8 Enable/disable webhook notifications

`POST /v0/bases/{baseId}/webhooks/{webhookId}/enableNotifications` — scope `webhook:manage`, Creator role. Toggles whether Airtable sends pings (does not stop payload generation). ([enable/disable](https://airtable.com/developers/web/api/enable-disable-webhook-notifications))

Request body (field **required**):
```json
{ "enable": true }
```

> **Open question:** docs say it "returns object"; the exact success status/body isn't shown (likely `200 {}`). Toggling sets `areNotificationsEnabled` accordingly (observable via List webhooks).

### 10.9 Lifecycle / expiration summary for the twin

- Created with a PAT/OAuth → `expirationTime` = creation + **7 days**; with a legacy user key → `null` (no expiry). ([create](https://airtable.com/developers/web/api/create-a-webhook), [overview](https://airtable.com/developers/web/api/webhooks-overview))
- Refresh **or** a successful List-payloads call extends expiry by 7 days. ([refresh](https://airtable.com/developers/web/api/refresh-a-webhook), [overview](https://airtable.com/developers/web/api/webhooks-overview))
- After expiration, the webhook's metadata and already-generated payloads remain accessible for **7 additional days** before being purged. ([overview](https://airtable.com/developers/web/api/webhooks-overview))
- `cursorForNextPayload` (from List webhooks) and the per-response `cursor` (from List payloads) are the same monotonically increasing pointer; `baseTransactionNumber` inside payloads strictly increases for ordering/de-dup. ([list](https://airtable.com/developers/web/api/list-webhooks), [list payloads](https://airtable.com/developers/web/api/list-webhook-payloads))


**Sources:** https://airtable.com/developers/web/api/webhooks-overview · https://airtable.com/developers/web/api/create-a-webhook · https://airtable.com/developers/web/api/list-webhooks · https://airtable.com/developers/web/api/list-webhook-payloads · https://airtable.com/developers/web/api/refresh-a-webhook · https://airtable.com/developers/web/api/delete-a-webhook · https://airtable.com/developers/web/api/enable-disable-webhook-notifications · https://airtable.com/developers/web/api/model/webhooks-payload · https://airtable.com/developers/web/api/model/webhooks-table-changed · https://airtable.com/developers/web/api/model/webhooks-specification · https://airtable.com/developers/web/api/model/webhooks-notification · https://support.airtable.com/docs/airtable-webhooks-api-overview · https://community.airtable.com/development-apis-11/not-able-to-match-x-airtable-content-mac-header-from-webhook-request-4316 · https://pyairtable.readthedocs.io/en/stable/webhooks.html


## 11. Rate limits

The twin must enforce two independent per-second limits and reply to violations with a `429` status, a fixed JSON error body, and a 30-second cooldown. The monthly per-plan call caps are a separate (billing-level) limit and are described at the end for completeness.

### 11.1 Documented limits

| Scope | Limit | Source |
|---|---|---|
| Per **base** | **5 requests / second / base** (applies to all pricing tiers) | [rate-limits](https://airtable.com/developers/web/api/rate-limits) |
| Per **personal access token / service account** | **50 requests / second** across all traffic for that user or service account | [rate-limits](https://airtable.com/developers/web/api/rate-limits) |

Both limits are enforced simultaneously. Exceeding *either* one produces the same `429` response described below. ([rate-limits](https://airtable.com/developers/web/api/rate-limits))

There is **no separately documented per-second limit for the metadata/meta API** — meta-API calls count against the same 5 req/s/base and 50 req/s/token ceilings. (No distinct meta-API rate limit appears in the official docs; see [Managing API call limits](https://support.airtable.com/docs/managing-api-call-limits-in-airtable). Treat as an open question if a stricter twin is required.)

### 11.2 Exceed behavior (429 + cooldown)

> "If you exceed [the] rate, you will receive a 429 status code and will need to wait 30 seconds before subsequent requests will succeed." — [rate-limits](https://airtable.com/developers/web/api/rate-limits)

- **HTTP status:** `429`
- **Cooldown / penalty:** the client must wait **30 seconds** before subsequent requests succeed. This is a *fixed* documented wait, not a value derived from a header. ([rate-limits](https://airtable.com/developers/web/api/rate-limits)) The official JavaScript client handles this automatically with back-off and retry logic. ([rate-limits](https://airtable.com/developers/web/api/rate-limits))

Twin implementation note: model the cooldown as a fixed 30-second window keyed by base (and/or token) after the offending request, during which every request to that base returns the `429` body below — regardless of whether the incoming rate has dropped back under the threshold.

### 11.3 Exact 429 response body

The verbatim JSON body returned on a rate-limit `429` is:

```json
{"errors":[{"error":"RATE_LIMIT_REACHED","message":"Rate limit exceeded. Please try again later"}]}
```

- `error` code string: `RATE_LIMIT_REACHED`
- `message` string: `Rate limit exceeded. Please try again later` (**no trailing period**)
- Note the envelope shape here is `errors` (plural array of `{error, message}` objects), which differs from the singular `{"error": {"type": ..., "message": ...}}` envelope used by 4xx errors elsewhere in the API. The twin must emit this plural-array shape specifically for the rate-limit case.

Confirmed across two independent sources reproducing the live response: [miniExtensions](https://docs.miniextensions.com/en/articles/7977226-429-errors-error-rate_limit_reached-message-rate-limit-exceeded-please-try-again-later) and [WebSearch corroboration]. The official [rate-limits](https://airtable.com/developers/web/api/rate-limits) page itself does not print the JSON body.

### 11.4 Response headers

- `Content-Type: application/json` (standard for all Airtable API responses).
- **`Retry-After`: not documented / unconfirmed.** Neither the official [rate-limits](https://airtable.com/developers/web/api/rate-limits) page nor [Managing API call limits](https://support.airtable.com/docs/managing-api-call-limits-in-airtable) mentions a `Retry-After` header, and the documented contract is the fixed 30-second wait instead. Some third-party summaries say a `Retry-After` header "may be provided," but this could not be traced to a primary Airtable source. **Recommendation for the twin:** do not emit `Retry-After` by default (match the documented fixed-30s contract); see open questions before relying on it.

### 11.5 Monthly per-plan call caps (separate billing limit — not per-second rate limiting)

Distinct from the per-second rate limits, plans have monthly API call quotas. Exceeding these also surfaces as a `429`, but it is a billing limit rather than the per-second throttle:

| Plan | Monthly API calls |
|---|---|
| Free | 1,000 / month |
| Team | 100,000 / month |
| Business / Enterprise Scale | No monthly cap |

Source: [Managing API call limits in Airtable](https://support.airtable.com/docs/managing-api-call-limits-in-airtable). For a request-replay twin these monthly caps are usually out of scope (they depend on workspace billing state), but a `429` seen in the wild may originate from this limit rather than the 5 req/s throttle.


**⚠ Independent verifier (DISAGREES — apply these corrections):**

I re-fetched the official docs independently. The draft is correct on the limits, the `429` status, the 30-second wait, the `RATE_LIMIT_REACHED` type, and the exact message string — but it is WRONG on the single most load-bearing point for a twin: the JSON error-envelope shape. The draft instructs the twin to emit a plural `{"errors":[{"error":...,"message":...}]}` array. Airtable's raw API actually returns the SINGULAR envelope. This must be fixed.

=== CRITICAL CORRECTION: 429 body is the singular envelope, NOT a plural array ===

The official Airtable Web API errors reference documents the 429 like every other error — as `{"error":{"type":"...","message":"..."}}`:

```json
{"error":{"type":"RATE_LIMIT_REACHED","message":"Rate limit exceeded. Please try again later"}}
```

Source: https://airtable.com/developers/web/api/errors (lists `429 → RATE_LIMIT_REACHED`, singular `error` object with `type` + `message`, same shape as `403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND`, `422 INVALID_REQUEST_UNKNOWN`, `503 RETRIABLE_ERROR`).

Corroboration that the envelope is singular (`error.type` / `error.message`), not a plural `errors` array:
- Official airtable.js error parser reads `error.type` / `error.message`: https://airtable.com/developers/web/api/errors and the client at https://github.com/Airtable/airtable.js
- Third-party Java client parses `error.type` and `error.message` (singular object), with a string fallback `{"error":"NOT_FOUND"}`: https://github.com/fuxingloh/airtable/blob/master/api/src/main/java/dev/fuxing/airtable/exceptions/AirtableApiException.java
- Official troubleshooting page shows the same singular shape for 403/422/503: https://support.airtable.com/docs/airtable-api-common-troubleshooting

Where the draft's plural `{"errors":[...]}` came from: the only source for it is miniExtensions (https://docs.miniextensions.com/en/articles/7977226-...), which is a third-party tool/proxy that reshapes the upstream body into an array. That is NOT the raw api.airtable.com response. The draft's claim that "the envelope here is `errors` (plural array)... which differs from the singular `{"error":{"type",...}}` envelope used elsewhere" is backwards: rate-limit responses use the SAME singular envelope as the rest of the API. The twin MUST emit the singular form. Do NOT special-case a plural array.

Note the field naming inside the singular envelope: the key is `type` (value `RATE_LIMIT_REACHED`), not `error` (the draft's plural objects used a `{"error":"RATE_LIMIT_REACHED","message":...}` inner shape — also wrong for the raw API).

Confirmed-correct in the draft (keep as-is):
- 5 requests/second/base, all pricing tiers — verbatim on https://airtable.com/developers/web/api/rate-limits
- 50 requests/second per personal access token from a given user or service account — verbatim, same page
- Both limits enforced simultaneously; exceeding either yields 429 — same page
- HTTP 429 + "wait 30 seconds before subsequent requests will succeed" — verbatim, same page
- `message` = `Rate limit exceeded. Please try again later` with NO trailing period — confirmed (errors reference + multiple sources)
- No separate documented per-second meta-API limit — correct; leave as open question

Retry-After header (draft hedges; refine):
- The draft recommends NOT emitting Retry-After by default. That is a DEFENSIBLE twin choice, but note the official errors reference does list a `Retry-After` header as one that "may be provided" on retriable/429 responses (https://airtable.com/developers/web/api/errors). No specific value is documented anywhere I could confirm. Critically, the official airtable.js client does NOT read Retry-After — it ignores it and uses exponential backoff with full jitter instead (https://github.com/Airtable/airtable.js, src/exponential_backoff_with_jitter.ts). So a twin omitting Retry-After will not break the official SDK. Recommend: keep it as an open question; emitting `Retry-After: 30` would be a reasonable optional toggle but is unconfirmed against the wire.

Cooldown / back-off precision (augment 11.2):
- The documented client contract is a fixed 30s wait, but the official SDK's actual retry timing is exponential backoff with full jitter, base delay `INITIAL_RETRY_DELAY_IF_RATE_LIMITED = 5000` ms and cap `MAX_RETRY_DELAY_IF_RATE_LIMITED = 600000` ms (src/internal_config.json in https://github.com/Airtable/airtable.js): delay = random(0, min(600000, 5000 * 2^attempt)). This does not change the twin's server-side behavior (a twin can keep the fixed 30s cooldown window), but it explains real-world retry timing and is worth a one-line note.

Monthly caps (11.5) — one omission:
- Free: 1,000/month; Team: 100,000/month; Business/Enterprise Scale: no monthly cap — confirmed (https://support.airtable.com/docs/managing-api-call-limits-in-airtable).
- ADD the Team-plan overage behavior the draft omits: when the Team monthly cap is hit, "API calls will slow down to 2 requests per second until the month resets" (same support page). Free plan: a one-time 30-day grace period, then calls are blocked. These are billing-level and reasonably out of scope for a request-replay twin, as the draft says.

Net: set agrees=false. The limits/status/cooldown are right, but 11.3 must be rewritten to the singular `{"error":{"type":"RATE_LIMIT_REACHED","message":"Rate limit exceeded. Please try again later"}}` body, and the draft's "emit the plural-array shape" instruction must be removed — it would make the twin diverge from the real api.airtable.com on every rate-limit response.


**Sources:** https://airtable.com/developers/web/api/rate-limits · https://support.airtable.com/docs/managing-api-call-limits-in-airtable · https://docs.miniextensions.com/en/articles/7977226-429-errors-error-rate_limit_reached-message-rate-limit-exceeded-please-try-again-later · https://support.airtable.com/docs/airtable-api-common-troubleshooting · https://community.airtable.com/development-apis-11/how-does-the-api-rate-limit-work-3325


---

## Open questions & low-confidence items (resolve during build / S24 audit)


**ids** (confidence: high):
- Whether Airtable guarantees a fixed alphabet/excluded characters for the 14-char suffix (e.g. no ambiguous chars). Observed examples are mixed-case [0-9A-Za-z], but Airtable does not publish a formal charset guarantee, so a twin's generator can safely emit [0-9A-Za-z] but a validator should be lenient on which specific chars appear.
- Whether base IDs are always exactly 17 chars in practice. Some third-party tooling has reported longer base IDs (e.g. enterprise/newer bases); the official docs example is 17, but this is not contractually documented. For a strict-rejection twin, consider accepting app + 14+ rather than hard-failing on length > 17.
- Whether comment and webhook IDs are contractually fixed at 17 chars — the official docs show 17-char comment examples and use zero-padded placeholders for webhooks, but Airtable does not publish an explicit length guarantee for these two object types.

**auth** (confidence: medium):
- EXACT verbatim message for the 401 case: the official errors page does not print a 401 JSON body. The body {type:"AUTHENTICATION_REQUIRED", message:"Authentication required"} is confirmed from an Airtable-MCP test fixture and community reports, not from an official Airtable example block. Worth confirming against a live API capture.
- Whether a missing header vs a malformed token vs an unknown-but-well-formed token ever differ (e.g. a distinct type for expired OAuth tokens, or a WWW-Authenticate header). All evidence shows an identical 401 AUTHENTICATION_REQUIRED body, but this was not verified against the live API for every variant.
- Exact response headers Airtable returns on auth failures (Content-Type assumed application/json; presence/absence of WWW-Authenticate, X-RateLimit-*, request-id headers) — not documented.
- Whether requesting a base/table that does not exist with a fully-authorized token returns 403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND or 404 NOT_FOUND. Docs list both a 403 (permissions-or-model-not-found) and a 404 NOT_FOUND (route/resource not found); the exact boundary between them per endpoint is unconfirmed.
- Whether scope-insufficient vs resource-not-granted vs user-permission-insufficient ever produce different 403 types (e.g. INVALID_PERMISSIONS vs INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND). Both type strings are documented but the precise trigger conditions for each are not fully pinned down.
- The precise PAT secret length/charset and the OAuth token character set are community-reported only (PAT ~82 chars, 14-char Token ID); Airtable does not officially document a fixed length.

**errors** (confidence: medium):
- Exact trigger boundary between the bare-string 404 ({"error":"NOT_FOUND"}) and object-form 404s (MODEL_ID_NOT_FOUND / TABLE_NOT_FOUND): the official page documents only the bare string, but real responses show object-form 404s for deleted/missing models. Need to confirm which endpoints/conditions produce which (likely: unknown URL path/base => bare string; resolvable path with a deleted/inaccessible sub-model => object form).
- The exact 401 behavior for an invalid-but-present token vs a missing token: docs describe both conditions but only AUTHENTICATION_REQUIRED is attested. Is there a distinct type/message for an invalid token vs an absent one?
- Official type/message strings for 400, 413, and 500 are not enumerated on the errors page. The shapes given (INVALID_REQUEST_UNKNOWN / REQUEST_TOO_LARGE / INTERNAL_SERVER_ERROR) are inferred and need verification against live responses.
- Whether 429 responses include a Retry-After header. Official docs only mention Retry-After for 503; many clients assume it on 429 but this is unconfirmed.
- Whether 502 Bad Gateway is ever returned with a JSON body or is a bare gateway response (some sources list 502 'Airtable servers restarting'). Not in the official enumeration.
- Exact verbatim messages for INVALID_PERMISSIONS (403), INVALID_REQUEST_UNKNOWN (422), and the 401 body straight from a live capture — current messages are reconstructed from community/3rd-party sources and may differ in punctuation/wording from the real API.

**records_write** (confidence: high):
- Exact error `type` string for the CREATE batch-cap (>10) message is unconfirmed from a primary Airtable source. The message text ('A maximum of 10 records can be created per request but you have provided N.') is confirmed via Zapier relaying Airtable; community reports the type as `INVALID_RECORDS`, but this should be verified against a live API response.
- Verbatim `message` strings for `INVALID_REQUEST_MISSING_FIELDS`, `INVALID_VALUE_FOR_COLUMN`, and `INVALID_MULTIPLE_CHOICE_OPTIONS` were not captured exactly (only their `type` and the triggering condition). The precise wording and whether they interpolate field name/ID should be confirmed against live responses.
- Whether batch operations are atomic on validation failure (e.g. if record #3 of 5 has a bad value, are records #1–2 rolled back?). Airtable behavior appears all-or-nothing for validation/permission errors, but this was not confirmed from the official docs.
- Exact `createdTime` precision/format guarantee (always milliseconds `.000Z`?) — examples consistently show `2022-09-12T21:03:48.000Z`, but the docs don't state the format contract explicitly.
- For PUT destructive update, confirm whether fields the token lacks write permission to are also cleared or left untouched (permission interaction with destructive clear).

**records_list** (confidence: high):
- Exact verbatim 401 body for a missing/invalid bearer token on list-records is not shown on the official errors page (it documents AUTHENTICATION_REQUIRED conceptually but no JSON example was captured). The precise type string and message need confirmation against a live response.
- The exact opaque format of the `offset` cursor is undocumented (observed in the wild as `<rowToken>/<recId>`); treat as implementation-defined.
- Whether `pageSize` > 100 returns 422 vs. is silently clamped to 100 is not explicitly stated in the docs (docs only say 'must be <= 100'); needs a live check to lock the exact behavior for the twin.
- The precise `type` string Airtable returns for a stale/invalid `offset` (vs generic INVALID_REQUEST_UNKNOWN) was not confirmed from an official example.
- Behavior precedence when both `view` and `sort`/`filterByFormula` are supplied is described qualitatively but not with a verbatim spec; confirm ordering rules against live API if exactness matters.

**formula** (confidence: medium):
- Exact verbatim JSON body and HTTP status for INVALID_FILTER_BY_FORMULA could not be confirmed against the official JS-rendered list-records page; the {error:{type,message}} shape and 422 status come from corroborating third-party sources (Make/Airtable community) and Airtable's general error conventions. Verify against a live API call.
- Whether single-quoted string literals are officially supported or merely tolerated: Airtable examples use both, but the formula-field-reference page documents double quotes explicitly. The twin accepts both; confirm the real parser does too.
- Exact case-sensitivity semantics: community usage treats SEARCH as case-insensitive and FIND as case-sensitive, but the reference page documents only the not-found return-value difference (FIND->0, SEARCH->blank). Confirm case behavior on a live base.
- IFERROR(value, fallback) is part of Airtable's function set but was not surfaced on the formula-field-reference page during this research; confirm its exact signature before including it.
- Exact equality/coercion rules when comparing a number field to a string literal, or a blank/BLANK() to '' vs 0 (e.g. does {Num}='' match an empty number cell?). The '' idiom is well-attested for emptiness but full coercion table is unconfirmed.
- Whether referencing a field by field ID (fldXXXXXXXX) is accepted inside filterByFormula in addition to names — the list-records doc says fields may be referenced by name or ID, but exact ID syntax (bare vs braced) is unconfirmed.

**meta** (confidence: high):
- Exact verbatim error.message strings and whether the bare {"error":"TYPE"} vs nested {"error":{"type","message"}} form is used per status code for Meta endpoints specifically (the errors page mixes both; needs live capture).
- Exact `offset` token format for GET /v0/meta/bases (treated as opaque; not documented).
- Full enumerated list of valid `dateTime.options.timeZone` values (docs reference a `Timezone` type without enumerating it; likely 'utc', 'client', and IANA names like 'America/Los_Angeles').
- Checkbox icon enum: field-model page lists `xCheckbox` whereas some secondary sources say `xCheck` — `xCheckbox` taken as authoritative from the field-model reference but worth a live check.
- Whether create-base/create-table responses always normalize submitted option values (e.g. Airtable's published example returns redBright/star for a submitted greenBright/check checkbox) or whether that is just an inconsistent doc example; affects whether the twin should echo vs. rewrite option values.
- `include[]=visibleFieldIds` exact query-string encoding (array bracket syntax) and whether visibleFieldIds is returned for non-grid view types.
- Response HTTP status code for successful create/update (docs show example bodies labeled 200; not explicitly confirmed it is 200 vs 201 for POST create-base/create-table/create-field — examples imply 200).

**comments** (confidence: medium):
- The docs site is a JS app; WebFetch returned a reconstructed schema rather than the page's verbatim rendered example. The exact literal example values in the official List Comments 200 response (the precise sample id/email/text/offset strings) were not captured verbatim — the §9.2 example uses representative values consistent with the documented field set, not a copy of Airtable's exact sample.
- Exact ordering of the comments array is not stated verbatim on the official page. Airtable community sources indicate newest-first; could not confirm whether list returns newest-first or oldest-first from the official reference.
- Precise success HTTP status code for create (200 vs 201) and for update/delete is not explicitly stated on the official pages; assumed 200 based on the response-body examples shown. Needs live verification.
- Exact error type/message and status for pageSize > 100 (e.g. whether it is 422 INVALID_REQUEST_UNKNOWN / a specific validation type) on the comments endpoint was not verbatim-confirmed.
- Whether create/update accept mentions via @[email] in addition to @[userId] is ambiguous: the official create-comment page shows @[userId] syntax, while community/third-party sources claim @[userId] from SDK contexts won't resolve and recommend @[email]. The authoritative input format for the API needs live verification.
- Full verbatim shape of nested 'attachments' and 'reactions' objects (exact subfield names) was described but not shown as a verbatim official JSON example.
- Behavior when deleting/updating a comment that does not exist or is not owned by the caller (exact status/type — likely 403 INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND or 404 NOT_FOUND) was not verbatim-confirmed.

**webhooks** (confidence: high):
- Delete a webhook and Enable/disable notifications endpoints: docs say 'returns object' but do not show the exact success status code or response body. Assumed 200 with a small/empty JSON body; not verified.
- Exact JSON encoding of cell <value> inside cellValuesByFieldId for complex field types (linked records, attachments, collaborators, etc.) is not documented on the webhook pages; must be cross-referenced with the field-types/record model.
- The notification result 'error' is documented only as {message}; Airtable does not publish named error codes (e.g. CANNOT_DELIVER, HOOK_EXPIRED), so the twin should not emit specific codes there.
- Precise retry count/backoff schedule (overview states ~13 retries over ~a day) is described qualitatively and rendered inconsistently across sources; exact timing not authoritatively confirmed.
- Whether 'previous' in changedRecordsById is omitted entirely vs present-but-empty when includePreviousCellValues is false was inferred (omitted) and not explicitly stated.
- WebFetch could not render the JS-app dev docs fully for some model pages; enum lists for fromSources/changeTypes and the table-changed shape were obtained but a live API capture would raise certainty further.

**ratelimit** (confidence: medium):
- Does Airtable actually send a `Retry-After` header on the 429? The official rate-limits page and support docs do not mention one (they document only a fixed 30s wait); third-party 'may be provided' phrasing could not be traced to a primary Airtable source. Needs a live capture of a real 429 response's raw headers to confirm presence/absence and value.
- Exact non-error response headers on a 429 (e.g. presence of `X-RateLimit-*` headers, request-id header name/format) are not documented and were not captured. Needs a live response dump.
- Is the 30-second cooldown keyed per-base, per-token, or per-IP? Docs state the wait but not the keying granularity. The 5/s limit is per-base and the 50/s is per-token, but which key drives the 30s penalty window is unconfirmed.
- Whether the metadata/meta API enforces any limit distinct from the 5 req/s/base and 50 req/s/token caps — no separate meta-API limit is documented, but this was not positively confirmed by Airtable.
- Whether the monthly-cap 429 (Free/Team plans) returns the same `RATE_LIMIT_REACHED` body or a different error code/message than the per-second throttle 429 — the two limits share the 429 status but the body for the monthly-cap case was not separately verified.