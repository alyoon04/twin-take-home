"""Record comments — CRUD (AIRTABLE_SPEC.md section 9).

Comments live under a record at /v0/{baseId}/{tableIdOrName}/{recordId}/comments,
stored on the record as record["comments"] (ordered by id). Registered before the
records router (defensive — these 4+ segment paths are more specific).
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request

from twin import auth, clock, config, errors, ids, store

router = APIRouter(tags=["comments"])

ReadToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_READ))]
WriteToken = Annotated[dict, Depends(auth.require_scope(config.SCOPE_RECORDS_WRITE))]


def _resolve_record(base_id: str, table_id_or_name: str, record_id: str) -> dict:
    base = store.state["bases"].get(base_id)
    if base is None:
        raise errors.not_found(bare=True)
    table = base["tables"].get(table_id_or_name) or next(
        (t for t in base["tables"].values() if t["name"] == table_id_or_name), None
    )
    if table is None:
        raise errors.not_found(bare=True)
    record = table["records"].get(record_id)
    if record is None:
        raise errors.not_found(bare=True)
    return record


def _author(token: dict) -> dict:
    user = store.state["users"].get(token["userId"], {})
    return {"id": token["userId"], "email": user.get("email", ""), "name": user.get("name", "")}


def _parse_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise errors.invalid_request()


@router.get("/v0/{base_id}/{table_id_or_name}/{record_id}/comments")
def list_comments(base_id: str, table_id_or_name: str, record_id: str, request: Request, _: ReadToken) -> dict:
    record = _resolve_record(base_id, table_id_or_name, record_id)
    comments = list(record.get("comments", {}).values())
    qp = request.query_params
    page_size = _parse_int(qp.get("pageSize"), 100)
    if not (1 <= page_size <= 100):
        raise errors.invalid_request()
    offset = qp.get("offset")
    start = 0
    if offset is not None:
        if not offset.isdigit() or int(offset) >= len(comments):
            raise errors.invalid_request()
        start = int(offset)
    page = comments[start:start + page_size]
    out = {"comments": page}
    if start + len(page) < len(comments):
        out["offset"] = str(start + len(page))
    return out


@router.post("/v0/{base_id}/{table_id_or_name}/{record_id}/comments")
def create_comment(base_id: str, table_id_or_name: str, record_id: str, token: WriteToken, body: Annotated[dict, Body()]) -> dict:
    record = _resolve_record(base_id, table_id_or_name, record_id)
    text = body.get("text")
    if not isinstance(text, str) or not text:
        raise errors.invalid_request()
    cid = ids.comment_id()
    comment = {
        "id": cid,
        "author": _author(token),
        "text": text,
        "createdTime": clock.stamp(),
        "lastUpdatedTime": None,
    }
    if isinstance(body.get("parentCommentId"), str):
        comment["parentCommentId"] = body["parentCommentId"]
    record.setdefault("comments", {})[cid] = comment
    return comment


@router.patch("/v0/{base_id}/{table_id_or_name}/{record_id}/comments/{comment_id}")
def update_comment(base_id: str, table_id_or_name: str, record_id: str, comment_id: str, _: WriteToken, body: Annotated[dict, Body()]) -> dict:
    record = _resolve_record(base_id, table_id_or_name, record_id)
    comment = record.get("comments", {}).get(comment_id)
    if comment is None:
        raise errors.not_found(bare=True)
    text = body.get("text")
    if not isinstance(text, str) or not text:
        raise errors.invalid_request()
    comment["text"] = text
    comment["lastUpdatedTime"] = clock.stamp()
    return comment


@router.delete("/v0/{base_id}/{table_id_or_name}/{record_id}/comments/{comment_id}")
def delete_comment(base_id: str, table_id_or_name: str, record_id: str, comment_id: str, _: WriteToken) -> dict:
    record = _resolve_record(base_id, table_id_or_name, record_id)
    comments = record.get("comments", {})
    if comment_id not in comments:
        raise errors.not_found(bare=True)
    del comments[comment_id]
    return {"id": comment_id, "deleted": True}
