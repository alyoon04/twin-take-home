"""Records API — read (AIRTABLE_SPEC.md sections 5-6).

GET list + GET one. Tables are addressable by id **or** by name. Query params
(pagination, filter, sort, projection) arrive in S10. Data-API not-found uses the
bare-string envelope ``{"error": "NOT_FOUND"}`` per spec.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from twin import auth, config, errors, store

router = APIRouter(tags=["records"])

ReadToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_READ))]


def _resolve_table(base_id: str, table_id_or_name: str) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found(bare=True)
    tables = base["tables"]
    table = tables.get(table_id_or_name)
    if table is None:
        table = next((t for t in tables.values() if t["name"] == table_id_or_name), None)
    if table is None:
        raise errors.not_found(bare=True)
    return table


def _public(record: dict) -> dict:
    return {"id": record["id"], "createdTime": record["createdTime"], "fields": dict(record["fields"])}


@router.get("/v0/{base_id}/{table_id_or_name}")
def list_records(base_id: str, table_id_or_name: str, _: ReadToken) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    return {"records": [_public(r) for r in table["records"].values()]}


@router.get("/v0/{base_id}/{table_id_or_name}/{record_id}")
def get_record(base_id: str, table_id_or_name: str, record_id: str, _: ReadToken) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    record = table["records"].get(record_id)
    if record is None:
        raise errors.not_found(bare=True)
    return _public(record)
