"""Webhook payload generation — the 'generated events' stream (SPEC section 10).

Record mutations call ``emit_change``; each subscribing webhook in the table's
base gets a payload appended to its log, retrievable via list-webhook-payloads.
Pure aside from reading/writing the store; takes no scope concerns.
"""

from twin import clock, store


def _base_of(table: dict):
    for base in store.state["bases"].values():
        if table["id"] in base["tables"]:
            return base
    return None


def _cell_values_by_field_id(table: dict, fields: dict) -> dict:
    name_to_id = {f["name"]: f["id"] for f in table["fields"]}
    return {name_to_id.get(k, k): v for k, v in fields.items()}


def emit_change(table: dict, *, created=None, changed=None, destroyed=None) -> None:
    base = _base_of(table)
    if base is None:
        return
    webhooks = [
        w for w in base.get("webhooks", {}).values()
        if "tableData" in w["specification"].get("options", {}).get("filters", {}).get("dataTypes", [])
    ]
    if not webhooks:
        return

    base["transactionNumber"] = base.get("transactionNumber", 0) + 1
    table_change: dict = {}
    if created:
        table_change["createdRecordsById"] = {
            r["id"]: {
                "createdTime": r["createdTime"],
                "cellValuesByFieldId": _cell_values_by_field_id(table, r["fields"]),
            }
            for r in created
        }
    if changed:
        table_change["changedRecordsById"] = {
            r["id"]: {"current": {"cellValuesByFieldId": _cell_values_by_field_id(table, r["fields"])}}
            for r in changed
        }
    if destroyed:
        table_change["destroyedRecordIds"] = list(destroyed)

    payload = {
        "timestamp": clock.stamp(),
        "baseTransactionNumber": base["transactionNumber"],
        "payloadFormat": "v0",
        "actionMetadata": {"source": "publicApi"},
        "changedTablesById": {table["id"]: table_change},
    }
    for w in webhooks:
        w["payloads"].append(payload)
        w["cursorForNextPayload"] = base["transactionNumber"] + 1
