"""Records API — read + query (AIRTABLE_SPEC.md sections 5-6).

GET list (pagination / projection / sort), the POST /listRecords variant, and
GET one. Tables are addressable by id or name. Data-API not-found uses the
bare-string envelope ``{"error": "NOT_FOUND"}``.

Deferred (documented gaps): ``filterByFormula`` (S11), ``view``, and
``cellFormat=string`` / ``timeZone`` / ``userLocale``.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from twin import auth, clock, config, errors, formula, ids, recordutil, store

router = APIRouter(tags=["records"])

ReadToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_READ))]
WriteToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_WRITE))]


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


def _query_records(table, *, fields, page_size, max_records, offset, sorts, by_id, formula_text=None) -> dict:
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise errors.invalid_request()
    if max_records is not None and (not isinstance(max_records, int) or max_records < 1):
        raise errors.invalid_request()

    id_to_name = {f["id"]: f["name"] for f in table["fields"]}
    name_to_id = {f["name"]: f["id"] for f in table["fields"]}

    records = list(table["records"].values())
    if formula_text:
        try:
            node = formula.compile_formula(formula_text, set(name_to_id), id_to_name)
        except formula.FormulaError:
            raise errors.invalid_filter_by_formula()
        records = [r for r in records if formula.matches(node, r["fields"])]

    ordered = _apply_sort(records, sorts, id_to_name)
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
        formula_text=qp.get("filterByFormula"),
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
        formula_text=body.get("filterByFormula"),
    )


@router.get("/v0/{base_id}/{table_id_or_name}/{record_id}")
def get_record(base_id: str, table_id_or_name: str, record_id: str, _: ReadToken) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    record = table["records"].get(record_id)
    if record is None:
        raise errors.not_found(bare=True)
    return {"id": record["id"], "createdTime": record["createdTime"], "fields": dict(record["fields"])}


# --- create (S12) ---------------------------------------------------------

def _present(record: dict, by_id: bool, name_to_id: dict) -> dict:
    return {
        "id": record["id"],
        "createdTime": record["createdTime"],
        "fields": _format_fields(record["fields"], None, by_id, name_to_id),
    }


def _coerce_value(field: dict, value, typecast: bool):
    # Strict for singleSelect (the documented typecast case); lenient for other
    # types (documented partial — deep type validation lives in the S24 audit list).
    if field["type"] == "singleSelect" and value is not None:
        choices = field.setdefault("options", {}).setdefault("choices", [])
        if value not in {c["name"] for c in choices}:
            if not typecast:
                raise errors.invalid_value_for_column(
                    f'Field {field["name"]} can not accept value "{value}"'
                )
            choices.append({"id": ids.select_id(), "name": value, "color": "blueLight2"})
    return value


def _build_record(table: dict, item, typecast: bool) -> dict:
    if not isinstance(item, dict) or not isinstance(item.get("fields"), dict):
        raise errors.invalid_request_missing_fields()
    by_name = {f["name"]: f for f in table["fields"]}
    validated = {}
    for key, value in item["fields"].items():
        field = by_name.get(key)
        if field is None:
            raise errors.unknown_field_name(key)
        validated[key] = _coerce_value(field, value, typecast)
    return {
        "id": ids.record_id(),
        "createdTime": clock.stamp(),
        "fields": recordutil.clean_fields(validated),
    }


@router.post("/v0/{base_id}/{table_id_or_name}")
def create_records(base_id: str, table_id_or_name: str, _: WriteToken, body: Annotated[dict, Body()]) -> dict:
    table = _resolve_table(base_id, table_id_or_name)
    typecast = bool(body.get("typecast", False))
    by_id = bool(body.get("returnFieldsByFieldId", False))
    name_to_id = {f["name"]: f["id"] for f in table["fields"]}

    if "records" in body:
        items = body["records"]
        if not isinstance(items, list):
            raise errors.invalid_request()
        if len(items) > 10:
            raise errors.invalid_request("Too many records; the maximum is 10 per request.")
        built = [_build_record(table, item, typecast) for item in items]  # validate all before commit
        for record in built:
            table["records"][record["id"]] = record
        return {"records": [_present(r, by_id, name_to_id) for r in built]}

    if "fields" in body:
        record = _build_record(table, body, typecast)
        table["records"][record["id"]] = record
        return _present(record, by_id, name_to_id)

    raise errors.invalid_request_missing_fields()
