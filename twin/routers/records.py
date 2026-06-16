"""Records API — read + query (AIRTABLE_SPEC.md sections 5-6).

GET list (pagination / projection / sort), the POST /listRecords variant, and
GET one. Tables are addressable by id or name. Data-API not-found uses the
bare-string envelope ``{"error": "NOT_FOUND"}``.

Deferred (documented gaps): ``filterByFormula`` (S11), ``view``, and
``cellFormat=string`` / ``timeZone`` / ``userLocale``.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from twin import auth, config, errors, store

router = APIRouter(tags=["records"])

ReadToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_READ))]


# --- resolution -----------------------------------------------------------

def _resolve_table(base_id: str, table_id_or_name: str) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found(bare=True)
    tables = base["tables"]
    table = tables.get(table_id_or_name) or next(
        (t for t in tables.values() if t["name"] == table_id_or_name), None
    )
    if table is None:
        raise errors.not_found(bare=True)
    return table


# --- query helpers --------------------------------------------------------

def _sort_key(value):
    return (value is None, value if value is not None else "")


def _apply_sort(records: list, sorts: list, id_to_name: dict) -> list:
    result = list(records)
    for field_ref, direction in reversed(sorts):
        name = id_to_name.get(field_ref, field_ref)
        result.sort(key=lambda r: _sort_key(r["fields"].get(name)), reverse=(direction == "desc"))
    return result


def _format_fields(fields: dict, projection, by_id: bool, name_to_id: dict) -> dict:
    out = dict(fields)
    if by_id:
        out = {name_to_id.get(k, k): v for k, v in out.items()}
    if projection:
        out = {k: v for k, v in out.items() if k in projection}
    return out


def _encode_offset(index: int, ordered: list) -> str:
    return f"itr{index}/{ordered[index]['id']}"


def _decode_offset(offset, total: int) -> int:
    if offset is None:
        return 0
    head = offset[3:].split("/", 1)[0] if offset.startswith("itr") and "/" in offset else None
    if head is None or not head.isdigit():
        raise errors.list_records_iterator_not_available()
    index = int(head)
    if index < 0 or index >= total:
        raise errors.list_records_iterator_not_available()
    return index


def _query_records(table, *, fields, page_size, max_records, offset, sorts, by_id) -> dict:
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise errors.invalid_request()
    if max_records is not None and (not isinstance(max_records, int) or max_records < 1):
        raise errors.invalid_request()

    id_to_name = {f["id"]: f["name"] for f in table["fields"]}
    name_to_id = {f["name"]: f["id"] for f in table["fields"]}

    ordered = _apply_sort(list(table["records"].values()), sorts, id_to_name)
    total = len(ordered) if max_records is None else min(len(ordered), max_records)
    start = _decode_offset(offset, total)
    page = ordered[start:min(start + page_size, total)]

    out = {
        "records": [
            {
                "id": r["id"],
                "createdTime": r["createdTime"],
                "fields": _format_fields(r["fields"], fields, by_id, name_to_id),
            }
            for r in page
        ]
    }
    next_index = start + len(page)
    if next_index < total:
        out["offset"] = _encode_offset(next_index, ordered)
    return out


# --- param extraction -----------------------------------------------------

def _parse_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise errors.invalid_request()


def _sorts_from_query(qp) -> list:
    sorts = []
    i = 0
    while (field := qp.get(f"sort[{i}][field]")) is not None:
        direction = qp.get(f"sort[{i}][direction]", "asc")
        if direction not in ("asc", "desc"):
            raise errors.invalid_request()
        sorts.append((field, direction))
        i += 1
    return sorts


def _sorts_from_body(raw) -> list:
    sorts = []
    for item in raw or []:
        if not isinstance(item, dict) or "field" not in item:
            raise errors.invalid_request()
        direction = item.get("direction", "asc")
        if direction not in ("asc", "desc"):
            raise errors.invalid_request()
        sorts.append((item["field"], direction))
    return sorts


# --- routes ---------------------------------------------------------------

@router.get("/v0/{base_id}/{table_id_or_name}")
def list_records(base_id: str, table_id_or_name: str, request: Request, _: ReadToken) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    qp = request.query_params
    return _query_records(
        table,
        fields=qp.getlist("fields[]") or qp.getlist("fields") or None,
        page_size=_parse_int(qp.get("pageSize"), 100),
        max_records=_parse_int(qp.get("maxRecords"), None),
        offset=qp.get("offset"),
        sorts=_sorts_from_query(qp),
        by_id=qp.get("returnFieldsByFieldId") == "true",
    )


@router.post("/v0/{base_id}/{table_id_or_name}/listRecords")
def list_records_post(
    base_id: str,
    table_id_or_name: str,
    _: ReadToken,
    body: Annotated[dict | None, Body()] = None,
) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    body = body or {}
    return _query_records(
        table,
        fields=body.get("fields") or None,
        page_size=body.get("pageSize", 100),
        max_records=body.get("maxRecords"),
        offset=body.get("offset"),
        sorts=_sorts_from_body(body.get("sort")),
        by_id=bool(body.get("returnFieldsByFieldId", False)),
    )


@router.get("/v0/{base_id}/{table_id_or_name}/{record_id}")
def get_record(base_id: str, table_id_or_name: str, record_id: str, _: ReadToken) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    record = table["records"].get(record_id)
    if record is None:
        raise errors.not_found(bare=True)
    return {"id": record["id"], "createdTime": record["createdTime"], "fields": dict(record["fields"])}
