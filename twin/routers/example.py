"""TEMPORARY placeholder resource family carried over from the starter.

Removed in S9 when the real Airtable Records API lands. It exists only so the
starter's control/auth tests stay green through the S3 restructure.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from twin import store
from twin.auth import require_auth
from twin.errors import provider_error

router = APIRouter(tags=["example (temporary)"])


class ExampleResourceCreate(BaseModel):
    name: str = Field(min_length=1)


@router.get("/v1/example-resources")
def list_example_resources(
    _: Annotated[None, Depends(require_auth)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    resources = store.state["example_resources"][:limit]
    return {"object": "list", "data": resources, "has_more": False}


@router.post("/v1/example-resources", status_code=status.HTTP_201_CREATED)
def create_example_resource(
    payload: ExampleResourceCreate,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    next_id = len(store.state["example_resources"]) + 1
    resource = {
        "id": f"res_twin_{next_id:03d}",
        "object": "example_resource",
        "name": payload.name,
    }
    store.state["example_resources"].append(resource)
    return resource


@router.get("/v1/example-resources/{resource_id}")
def get_example_resource(
    resource_id: str,
    _: Annotated[None, Depends(require_auth)],
) -> dict:
    for resource in store.state["example_resources"]:
        if resource["id"] == resource_id:
            return resource

    raise provider_error(
        status.HTTP_404_NOT_FOUND,
        "not_found",
        f"No such resource: {resource_id}",
    )
