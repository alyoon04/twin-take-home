"""Meta API — read (AIRTABLE_SPEC.md section 8).

whoami, list bases, and base schema (tables -> typed fields -> views). Mounted
under /v0/meta and MUST be registered before the records router so these paths
are not swallowed by the generic /v0/{baseId}/{table} routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from twin import auth, config, errors, store

router = APIRouter(prefix="/v0/meta", tags=["meta"])

SchemaRead = Annotated[dict, Depends(auth.require_scope(config.SCOPE_SCHEMA_READ))]


@router.get("/whoami")
def whoami(token: Annotated[dict, Depends(auth.get_token)]) -> dict:
    # Any valid token; no scope required.
    return {"id": token["userId"], "scopes": list(token.get("scopes", []))}


@router.get("/bases")
def list_bases(_: SchemaRead) -> dict:
    return {
        "bases": [
            {"id": b["id"], "name": b["name"], "permissionLevel": b.get("permissionLevel", "create")}
            for b in store.state["bases"].values()
        ]
    }


def _field_schema(field: dict) -> dict:
    out = {"id": field["id"], "name": field["name"], "type": field["type"]}
    if "options" in field:
        out["options"] = field["options"]
    if field.get("description"):
        out["description"] = field["description"]
    return out


def _table_schema(table: dict, include_visible: bool) -> dict:
    views = []
    for v in table["views"]:
        view = {"id": v["id"], "name": v["name"], "type": v["type"]}
        if include_visible and v["type"] == "grid":
            view["visibleFieldIds"] = [f["id"] for f in table["fields"]]
        views.append(view)
    out = {
        "id": table["id"],
        "name": table["name"],
        "primaryFieldId": table["primaryFieldId"],
        "fields": [_field_schema(f) for f in table["fields"]],
        "views": views,
    }
    if table.get("description"):
        out["description"] = table["description"]
    return out


@router.get("/bases/{base_id}/tables")
def base_schema(base_id: str, request: Request, _: SchemaRead) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found()  # meta API uses the object-form 404
    include = request.query_params.getlist("include[]") or request.query_params.getlist("include")
    include_visible = "visibleFieldIds" in include
    return {"tables": [_table_schema(t, include_visible) for t in base["tables"].values()]}
