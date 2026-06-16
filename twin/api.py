"""FastAPI application factory.

Builds the app, mounts the routers, and installs the Airtable-shaped exception
handlers. Kept thin: behavior lives in the per-family routers and the shared
modules (store, auth, errors, ...).
"""

from fastapi import FastAPI

from twin import errors
from twin.routers import control, example


def create_app() -> FastAPI:
    app = FastAPI(
        title="Airtable Web API Twin",
        version="0.1.0",
        description="Local fake of the Airtable Web API for development and testing (Arga SaaS twin).",
    )
    app.include_router(control.router)
    app.include_router(example.router)
    errors.register_handlers(app)
    return app


app = create_app()
