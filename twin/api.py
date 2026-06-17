"""FastAPI application factory.

Builds the app, mounts the routers, installs the Airtable-shaped exception
handlers, and adds the (opt-in, deterministic) per-base rate-limit middleware.

Router order matters: more specific prefixes (`/v0/meta/*`, `/v0/bases/*`,
record-scoped sub-paths) are registered BEFORE the generic
`/v0/{baseId}/{table}` records router.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from twin import errors, store
from twin.routers import comments, control, meta, records, webhooks


def _base_id_from_path(path: str):
    """The base id a request targets (for per-base rate limiting), or None."""
    parts = path.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "v0":
        return None
    if parts[1] == "bases" and len(parts) >= 3:  # /v0/bases/{baseId}/webhooks...
        return parts[2]
    if parts[1] == "meta":  # /v0/meta/bases/{baseId}/tables ; else not base-scoped
        return parts[3] if len(parts) >= 4 and parts[2] == "bases" else None
    return parts[1]  # /v0/{baseId}/{table}...


def create_app() -> FastAPI:
    app = FastAPI(
        title="Airtable Web API Twin",
        version="0.1.0",
        description="Local fake of the Airtable Web API for development and testing (Arga SaaS twin).",
    )

    @app.middleware("http")
    async def _rate_limit(request: Request, call_next):
        rl = store.state.get("rateLimit")
        if rl and rl.get("enabled"):
            base_id = _base_id_from_path(request.url.path)
            if base_id:
                counts = rl["counts"]
                counts[base_id] = counts.get(base_id, 0) + 1
                if counts[base_id] > rl["perBase"]:
                    err = errors.rate_limit_reached()
                    return JSONResponse(status_code=err.status_code, content=err.body)
        return await call_next(request)

    app.include_router(control.router)
    app.include_router(meta.router)
    app.include_router(comments.router)
    app.include_router(webhooks.router)
    app.include_router(records.router)
    errors.register_handlers(app)
    return app


app = create_app()
