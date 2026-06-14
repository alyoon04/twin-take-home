# SaaS Twin Take-Home

Thanks for taking the time to do this. The goal of this exercise is to build a
service twin: a local, fake version of a real SaaS API that another app could
use during development or testing instead of talking to the real provider.

You may use LLMs, docs, SDKs, code generation, snippets, or any other normal
developer tools. We care about the final product, your judgment, and whether you
can explain the tradeoffs you made.

This assignment is Python-only. Use Python for the service, tests, scripts, and
supporting code. Use `uv` for Python package management. This starter uses
FastAPI, but you may switch to another Python web framework if you prefer.

You can choose any SaaS you want. Once you choose it, you are expected to build
the full twin for that SaaS API, not a narrow mock or a hand-picked subset.

Pick accordingly. A smaller SaaS with a compact API is completely fine. A huge
provider with hundreds of endpoints is also fine, but then we will expect broad
coverage across that provider.

## The Assignment

Pick any SaaS provider and build a Dockerized Python HTTP service that emulates
its public API.

Good choices include APIs like Slack, Stripe, Linear, Notion, GitHub, HubSpot,
Discord, Jira, Airtable, Twilio, Shopify, Zendesk, or similar. Some of these are
large, so picking something more manageable is completely acceptable. You can
choose something else if it has enough API behavior to be interesting.

## How Arga Will Validate This

Your submission should be a fork of this repo or a standalone repo. Arga's validation system will treat
it as a black-box service: build the Docker image, start the container, wait for
the health endpoint, reset deterministic state, then send provider-shaped API
requests against it.

The `twin-contract.yaml` file is the small handoff document that tells the
validator and reviewer how to build, run, authenticate, reset, and sample your
twin. The control endpoints make repeated validation runs deterministic.

## Required Runtime Contract

Your submission must run as a Docker container.

It should listen on `0.0.0.0:8080` inside the container unless there is specific reason not to.

We should be able to run it like this:

```bash
docker build -t candidate-twin .
docker run --rm -p 8080:8080 candidate-twin
```

If your build or run command is different, document the exact commands in your
README.

The service must not require real provider credentials or make real external API
calls. Use fake/dev credentials and local state.

## Control Endpoints

Include these endpoints regardless of which provider you choose:

| Method | Path                 | Purpose                                                                                                    |
| ------ | -------------------- | ---------------------------------------------------------------------------------------------------------- |
| `GET`  | `/_arga/healthz`     | Health check. Should return a successful response when the service is ready.                               |
| `GET`  | `/_arga/admin/state` | Debug snapshot of the twin's current local state.                                                          |
| `POST` | `/_arga/admin/reset` | Reset state to a "default" or normal state.                                                               |
| `GET`  | `/openapi.json`      | OpenAPI schema, if your framework supports it. If it does not make sense for your choice, you may skip it. |

`/_arga/admin/reset` should make repeated test runs deterministic. After reset,
the same sequence of API calls should produce the same results.

## Provider API Requirements

Implement provider-shaped API behavior, not just arbitrary endpoints.

Your twin should include:

- The full documented API surface for the SaaS you chose, or the full public API
  for a clearly named product within that SaaS if the company exposes multiple
  separate products.
- Every major API family needed for that provider to feel complete.
- Fake auth that resembles the provider's auth style, including auth success
  and auth failure behavior.
- Provider-shaped error responses for common failures.

The twin should also include, where those concepts exist in the provider:

- Create, read/list, update, and delete/archive/cancel-style lifecycle behavior
  where those concepts make sense for the provider.
- Pagination, filtering, search, or sorting for at least one list endpoint.
- Realistic state transition(s), for example:
  - checkout session completion
  - payment status changes
  - issue workflow transitions
  - message threads and reactions
  - file upload lifecycle
  - generated events
  - archived/deleted resource behavior

The SaaS choice is up to you. The scope after that choice is not meant to be a
small selected slice. If the provider has documented endpoints, include them or
explicitly call out the small number of exceptions with a good reason.

## State and Data

Use deterministic local state. In-memory state is fine.

Seed the service with enough default data that it is easy to try:

- fake users/accounts
- fake resources
- fake credentials
- IDs that are stable enough for examples
- enough relationships to exercise the workflow

Do not add a database unless you really need one. If you use one, the Docker
setup should still be easy to run.

## Auth

Implement fake auth that resembles the provider.

Examples:

- `Authorization: Bearer sk_test_...`
- raw personal API key
- provider-specific version or workspace headers
- OAuth-looking access tokens without doing a real OAuth flow

Document at least one valid fake credential and at least one invalid-auth
example.

## Errors

Errors should look like the provider where practical.

Include realistic behavior for cases such as:

- missing auth
- invalid auth
- resource not found
- invalid request body
- unsupported operation
- duplicate resource
- invalid state transition
- rate limit or provider-style throttling, if relevant

Errors should be as similar to the real API as possible.

## Deliverables

Submit a repo containing:

- Source code.
- `Dockerfile`.
- `pyproject.toml` and `uv.lock`.
- Applicant README with:
  - provider chosen
  - documented API surface and what is implemented
  - fake credentials
  - run commands
  - example API calls
  - test commands
  - any known gaps and why they remain
- Python tests or a Python verification script, see below.
- A `twin-contract.yaml` file, described below.

## Starter Repo

This repo includes a small FastAPI shell:

- [app.py](app.py) has the required Arga control endpoints, fake auth helpers,
  and a placeholder resource family.
- [Dockerfile](Dockerfile) runs the service on port `8080`.
- [pyproject.toml](pyproject.toml) and [uv.lock](uv.lock) define the Python
  environment with `uv`.
- [tests/test_control.py](tests/test_control.py) verifies the starter control
  endpoints and fake auth behavior.
- [twin-contract.yaml](twin-contract.yaml) is a template that you should update
  for your chosen provider.

Replace the placeholder `/v1/example-resources` routes with provider-shaped
routes for the SaaS you choose.

## `twin-contract.yaml`

Include a small `twin-contract.yaml` file at the repo root so we can quickly run
and inspect your twin.

Example:

```yaml
provider: stripe
name: Candidate Stripe Twin
base_url: http://localhost:8080

run:
  build: docker build -t candidate-twin .
  start: docker run --rm -p 8080:8080 candidate-twin

auth:
  valid:
    header: Authorization
    value: Bearer sk_test_twin_123
  invalid:
    header: Authorization
    value: Bearer invalid

control:
  health: GET /_arga/healthz
  state: GET /_arga/admin/state
  reset: POST /_arga/admin/reset
  openapi: GET /openapi.json

examples:
  - name: List customers
    method: GET
    path: /v1/customers
  - name: Create checkout session
    method: POST
    path: /v1/checkout/sessions
    body:
      customer: cus_twin_001
      mode: payment
```

Use the shape above as a guide. Adjust paths and examples for your provider.

## Tests

Include Python tests and/or a Python verification script that we can run locally.

Good coverage includes, where applicable:

- health check
- reset behavior
- valid auth
- invalid auth
- list/read seeded resources
- create a resource
- update or transition that resource
- delete/archive/cancel behavior
- pagination/filtering/search
- provider-shaped error response

Document the command, for example:

```bash
uv run pytest
```

For local development, the starter can be run with:

```bash
uv sync
uv run uvicorn app:app --reload --port 8080
```

## What We Will Evaluate

We will run your Docker image and interact with it as a black-box service.

We will evaluate code quality and README clarity, but most importantly we will
evaluate how similar your twin is to the real production SaaS, specifically how
its endpoints respond for both valid and invalid inputs.

## Things You Do Not Need To Do

You do not need to:

- Deploy to a cloud provider.
- Use real SaaS credentials.
- Build a beautiful frontend.
  - Some Arga twins have frontends, but the main evaluation will be on the
    backend API, not the frontend.
- Persist data across container restarts.

## Tips

Pick a provider you already understand or can learn quickly.

Start from the provider's API docs and make an endpoint inventory early. A
smaller SaaS implemented completely is better than a large SaaS with scattered
partial coverage.

Use the real provider docs to copy names, paths, request shapes, response
shapes, auth behavior, pagination, and error style.
