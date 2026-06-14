from copy import deepcopy
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from pydantic import BaseModel, Field


VALID_AUTH_HEADER = "Bearer sk_test_twin_123"

DEFAULT_STATE = {
    "provider": "TODO",
    "example_resources": [
        {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
    ],
}

state = deepcopy(DEFAULT_STATE)

app = FastAPI(
    title="Candidate SaaS Twin",
    version="0.1.0",
    description="Python starter shell for the Arga SaaS twin take-home.",
)


class ExampleResourceCreate(BaseModel):
    name: str = Field(min_length=1)


def reset_state() -> None:
    state.clear()
    state.update(deepcopy(DEFAULT_STATE))


def provider_error(status_code: int, error_type: str, message: str) -> HTTPException:
    # TODO: replace this generic shape with the chosen provider's real error shape.
    return HTTPException(
        status_code=status_code,
        detail={"error": {"type": error_type, "message": message}},
    )


def require_auth(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    # TODO: make auth look like the chosen provider, including missing vs invalid cases.
    if authorization != VALID_AUTH_HEADER:
        raise provider_error(
            status.HTTP_401_UNAUTHORIZED,
            "authentication_error",
            "Invalid or missing API key.",
        )


@app.get("/_arga/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/_arga/admin/state")
def admin_state() -> dict:
    return deepcopy(state)


@app.post("/_arga/admin/reset")
def admin_reset() -> dict[str, str]:
    reset_state()
    return {"status": "reset"}


@app.get("/v1/example-resources")
def list_example_resources(
    _: Annotated[None, Depends(require_auth)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    # TODO: replace this with list behavior from the chosen provider.
    resources = state["example_resources"][:limit]
    return {"object": "list", "data": resources, "has_more": False}


@app.post("/v1/example-resources", status_code=status.HTTP_201_CREATED)
def create_example_resource(
    payload: ExampleResourceCreate,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    # TODO: replace this ID format, object shape, and validation with provider behavior.
    next_id = len(state["example_resources"]) + 1
    resource = {
        "id": f"res_twin_{next_id:03d}",
        "object": "example_resource",
        "name": payload.name,
    }
    state["example_resources"].append(resource)
    return resource


@app.get("/v1/example-resources/{resource_id}")
def get_example_resource(
    resource_id: str,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    # TODO: replace this with provider-specific lookup and not-found behavior.
    for resource in state["example_resources"]:
        if resource["id"] == resource_id:
            return resource

    raise provider_error(
        status.HTTP_404_NOT_FOUND,
        "not_found",
        f"No such resource: {resource_id}",
    )


# TODO: add provider-shaped update, delete/archive/cancel, pagination, search,
# transitions, event generation, and realistic error cases.
