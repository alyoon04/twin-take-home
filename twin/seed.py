"""Deterministic seed data.

S5: a minimal-but-real seed (one base, one table, typed fields, a few records,
a user) that exercises the deterministic id/clock path so reset + replay is
byte-identical. S8 expands this into the full graph (CRM + Project Tracker, all
field types, linked records, comments, a webhook). Everything is built via
``ids``/``clock`` from their reset baseline, so every reset reproduces identical
IDs and timestamps.
"""

from twin import clock, ids

# Stable example id carried over from the starter. The temporary example router
# and the starter tests depend on it; removed in S9.
_EXAMPLE_RESOURCES = [
    {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
]

_DEFAULT_SCOPES = [
    "data.records:read",
    "data.records:write",
    "schema.bases:read",
    "schema.bases:write",
    "webhook:manage",
]


def build() -> dict:
    """Construct the default state. Consumes ids/clock from their reset baseline."""
    uid = ids.user_id()
    users = {
        uid: {
            "id": uid,
            "email": "dev@twin.example",
            "name": "Twin Dev",
            "scopes": list(_DEFAULT_SCOPES),
        }
    }

    crm = _build_crm_base()

    return {
        "provider": "airtable",
        "users": users,
        "bases": {crm["id"]: crm},
        "webhooks": {},
        "example_resources": [dict(r) for r in _EXAMPLE_RESOURCES],
    }


def _build_crm_base() -> dict:
    base_id = ids.base_id()
    contacts = _build_contacts_table()
    return {
        "id": base_id,
        "name": "CRM",
        "permissionLevel": "create",
        "tables": {contacts["id"]: contacts},
    }


def _build_contacts_table() -> dict:
    table_id = ids.table_id()
    name_field = {"id": ids.field_id(), "name": "Name", "type": "singleLineText"}
    email_field = {"id": ids.field_id(), "name": "Email", "type": "email"}
    company_field = {"id": ids.field_id(), "name": "Company", "type": "singleLineText"}
    active_field = {"id": ids.field_id(), "name": "Active", "type": "checkbox"}
    fields = [name_field, email_field, company_field, active_field]
    view = {"id": ids.view_id(), "name": "Grid view", "type": "grid"}

    rows = [
        {"Name": "Ada Lovelace", "Email": "ada@example.com", "Company": "Analytical Engines", "Active": True},
        {"Name": "Alan Turing", "Email": "alan@example.com", "Company": "Bletchley Park", "Active": True},
        {"Name": "Grace Hopper", "Email": "grace@example.com", "Company": "US Navy", "Active": False},
    ]
    records = {}
    for row in rows:
        rid = ids.record_id()
        records[rid] = {"id": rid, "createdTime": clock.stamp(), "fields": dict(row)}

    return {
        "id": table_id,
        "name": "Contacts",
        "primaryFieldId": name_field["id"],
        "fields": fields,
        "views": [view],
        "records": records,
    }
