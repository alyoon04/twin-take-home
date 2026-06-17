"""Meta API — read (AIRTABLE_SPEC.md section 8).

whoami, list bases, and base schema (tables -> typed fields -> views). Mounted
under /v0/meta and MUST be registered before the records router so these paths
are not swallowed by the generic /v0/{baseId}/{table} routes.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from twin import auth, config, errors, ids, store

router = APIRouter(prefix="/v0/meta", tags=["meta"])

SchemaRead = Annotated[dict, Depends(auth.require_scope(config.SCOPE_SCHEMA_READ))]


@router.get("/whoami")
def whoami(token: Annotated[dict, Depends(auth.get_token)]) -> dict:
    # Any valid token; no scope required. PAT-style tokens return just {id}
    # (Airtable includes `scopes` only for OAuth access tokens).
    return {"id": token["userId"]}


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
        # Verified live: the meta API treats a missing base as a missing *model* →
        # 403 (existence-hiding), unlike the data API where a missing base is a bare 404.
        raise errors.invalid_permissions_or_model_not_found()
    include = request.query_params.getlist("include[]") or request.query_params.getlist("include")
    include_visible = "visibleFieldIds" in include
    return {"tables": [_table_schema(t, include_visible) for t in base["tables"].values()]}


# --- writes (S16) ---------------------------------------------------------

SchemaWrite = Annotated[dict, Depends(auth.require_scope(config.SCOPE_SCHEMA_WRITE))]


def _meta_table(base_id: str, table_id_or_name: str) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found()
    table = base["tables"].get(table_id_or_name) or next(
        (t for t in base["tables"].values() if t["name"] == table_id_or_name), None
    )
    if table is None:
        raise errors.not_found()
    return table


def _normalize_options(ftype: str, options):
    if ftype in ("singleSelect", "multipleSelects") and isinstance(options, dict) and isinstance(options.get("choices"), list):
        choices = []
        for c in options["choices"]:
            choice = dict(c) if isinstance(c, dict) else {"name": c}
            choice.setdefault("id", ids.select_id())
            choices.append(choice)
        return {**options, "choices": choices}
    return options


def _build_field(cfg) -> dict:
    if not isinstance(cfg, dict) or not isinstance(cfg.get("name"), str) or not isinstance(cfg.get("type"), str):
        raise errors.invalid_request()
    field = {"id": ids.field_id(), "name": cfg["name"], "type": cfg["type"]}
    if "options" in cfg:
        field["options"] = _normalize_options(cfg["type"], cfg["options"])
    if cfg.get("description"):
        field["description"] = cfg["description"]
    return field


def _build_table(cfg) -> dict:
    if not isinstance(cfg, dict) or not isinstance(cfg.get("name"), str):
        raise errors.invalid_request()
    field_cfgs = cfg.get("fields")
    if not isinstance(field_cfgs, list) or not field_cfgs:
        raise errors.invalid_request()
    fields = [_build_field(fc) for fc in field_cfgs]
    table = {
        "id": ids.table_id(),
        "name": cfg["name"],
        "primaryFieldId": fields[0]["id"],
        "fields": fields,
        "views": [{"id": ids.view_id(), "name": "Grid view", "type": "grid"}],
        "records": {},
    }
    if cfg.get("description"):
        table["description"] = cfg["description"]
    return table


@router.post("/bases")
def create_base(_: SchemaWrite, body: Annotated[dict, Body()]) -> dict:
    if (not isinstance(body.get("name"), str) or not isinstance(body.get("workspaceId"), str)
            or not isinstance(body.get("tables"), list) or not body["tables"]):
        raise errors.invalid_request()
    base_id = ids.base_id()
    tables = [_build_table(tc) for tc in body["tables"]]
    store.state["bases"][base_id] = {
        "id": base_id,
        "name": body["name"],
        "permissionLevel": "create",
        "tables": {t["id"]: t for t in tables},
    }
    return {"id": base_id, "tables": [_table_schema(t, False) for t in tables]}


@router.post("/bases/{base_id}/tables")
def create_table(base_id: str, _: SchemaWrite, body: Annotated[dict, Body()]) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found()
    table = _build_table(body)
    base["tables"][table["id"]] = table
    return _table_schema(table, False)


@router.patch("/bases/{base_id}/tables/{table_id_or_name}")
def update_table(base_id: str, table_id_or_name: str, _: SchemaWrite, body: Annotated[dict, Body()]) -> dict:
    table = _meta_table(base_id, table_id_or_name)
    if "name" in body:
        if not isinstance(body["name"], str):
            raise errors.invalid_request()
        table["name"] = body["name"]
    if "description" in body:
        table["description"] = body["description"]
    return _table_schema(table, False)


@router.post("/bases/{base_id}/tables/{table_id}/fields")
def create_field(base_id: str, table_id: str, _: SchemaWrite, body: Annotated[dict, Body()]) -> dict:
    table = _meta_table(base_id, table_id)
    field = _build_field(body)
    table["fields"].append(field)
    return _field_schema(field)


@router.patch("/bases/{base_id}/tables/{table_id}/fields/{field_id}")
def update_field(base_id: str, table_id: str, field_id: str, _: SchemaWrite, body: Annotated[dict, Body()]) -> dict:
    table = _meta_table(base_id, table_id)
    field = next((f for f in table["fields"] if f["id"] == field_id), None)
    if field is None:
        raise errors.not_found()
    if "type" in body:  # field type cannot be changed via PATCH
        raise errors.invalid_request("Field type cannot be changed.")
    if "name" in body:
        field["name"] = body["name"]
    if "description" in body:
        field["description"] = body["description"]
    if "options" in body:
        field["options"] = _normalize_options(field["type"], body["options"])
    return _field_schema(field)
