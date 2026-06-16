"""Deterministic seed data — the full default graph.

Two bases built entirely through ``ids``/``clock`` from their reset baseline so
every reset reproduces identical IDs and timestamps:

  - **CRM** → Contacts (singleLineText, email, checkbox).
  - **Project Tracker** → Projects + Tasks, with a bidirectional
    ``multipleRecordLinks`` relationship, plus singleSelect / number / date.

Record ``fields`` hold only non-empty cells (``_clean``) — matching Airtable,
which omits empty/false cells from records.
"""

from twin import clock, config, ids

_EXAMPLE_RESOURCES = [
    {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
]

_ISO_DATE = {"dateFormat": {"name": "iso", "format": "YYYY-MM-DD"}}
_CHECKBOX = {"icon": "check", "color": "greenBright"}


def build() -> dict:
    """Construct the default state. Consumes ids/clock from their reset baseline."""
    uid = ids.user_id()
    users = {
        uid: {
            "id": uid,
            "email": "dev@twin.example",
            "name": "Twin Dev",
            "scopes": list(config.ALL_SCOPES),
        }
    }
    tokens = {
        config.VALID_PAT: {"userId": uid, "scopes": list(config.ALL_SCOPES)},
        config.READONLY_PAT: {
            "userId": uid,
            "scopes": [config.SCOPE_RECORDS_READ, config.SCOPE_SCHEMA_READ],
        },
    }

    crm = _build_crm_base()
    tracker = _build_project_tracker_base()

    return {
        "provider": "airtable",
        "users": users,
        "tokens": tokens,
        "bases": {crm["id"]: crm, tracker["id"]: tracker},
        "webhooks": {},
        "example_resources": [dict(r) for r in _EXAMPLE_RESOURCES],
    }


# --- helpers --------------------------------------------------------------

def _clean(fields: dict) -> dict:
    """Drop empty cells (None / "" / False / []) the way Airtable does on read."""
    return {
        k: v
        for k, v in fields.items()
        if v is not None and v is not False and v != "" and v != []
    }


def _record(fields: dict) -> tuple[str, dict]:
    rid = ids.record_id()
    return rid, {"id": rid, "createdTime": clock.stamp(), "fields": _clean(dict(fields))}


def _choices(pairs: list[tuple[str, str]]) -> list[dict]:
    return [{"id": ids.select_id(), "name": name, "color": color} for name, color in pairs]


def _grid_view() -> dict:
    return {"id": ids.view_id(), "name": "Grid view", "type": "grid"}


# --- CRM base -------------------------------------------------------------

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
    active_field = {"id": ids.field_id(), "name": "Active", "type": "checkbox", "options": dict(_CHECKBOX)}
    view = _grid_view()

    rows = [
        {"Name": "Ada Lovelace", "Email": "ada@example.com", "Company": "Analytical Engines", "Active": True},
        {"Name": "Alan Turing", "Email": "alan@example.com", "Company": "Bletchley Park", "Active": True},
        {"Name": "Grace Hopper", "Email": "grace@example.com", "Company": "US Navy", "Active": False},
        {"Name": "Katherine Johnson", "Email": "katherine@example.com", "Company": "NASA", "Active": True},
        {"Name": "Margaret Hamilton", "Email": "margaret@example.com", "Company": "MIT", "Active": True},
    ]
    records = {}
    for row in rows:
        rid, rec = _record(row)
        records[rid] = rec

    return {
        "id": table_id,
        "name": "Contacts",
        "primaryFieldId": name_field["id"],
        "fields": [name_field, email_field, company_field, active_field],
        "views": [view],
        "records": records,
    }


# --- Project Tracker base (linked records) --------------------------------

def _build_project_tracker_base() -> dict:
    base_id = ids.base_id()

    # Structural IDs up front so the two link fields can cross-reference.
    projects_tid = ids.table_id()
    tasks_tid = ids.table_id()
    projects_view = _grid_view()
    tasks_view = _grid_view()

    p_name = ids.field_id()
    p_status = ids.field_id()
    p_start = ids.field_id()
    p_tasks_link = ids.field_id()

    t_name = ids.field_id()
    t_status = ids.field_id()
    t_priority = ids.field_id()
    t_due = ids.field_id()
    t_project_link = ids.field_id()
    t_done = ids.field_id()

    p_status_choices = _choices([("Active", "greenBright"), ("On Hold", "yellowBright"), ("Complete", "blueBright")])
    t_status_choices = _choices([("Todo", "grayBright"), ("In Progress", "yellowBright"), ("Done", "greenBright")])

    projects_fields = [
        {"id": p_name, "name": "Name", "type": "singleLineText"},
        {"id": p_status, "name": "Status", "type": "singleSelect", "options": {"choices": p_status_choices}},
        {"id": p_start, "name": "Start", "type": "date", "options": dict(_ISO_DATE)},
        {"id": p_tasks_link, "name": "Tasks", "type": "multipleRecordLinks",
         "options": {"linkedTableId": tasks_tid, "isReversed": False,
                     "prefersSingleRecordLink": False, "inverseLinkFieldId": t_project_link}},
    ]
    tasks_fields = [
        {"id": t_name, "name": "Name", "type": "singleLineText"},
        {"id": t_status, "name": "Status", "type": "singleSelect", "options": {"choices": t_status_choices}},
        {"id": t_priority, "name": "Priority", "type": "number", "options": {"precision": 0}},
        {"id": t_due, "name": "Due", "type": "date", "options": dict(_ISO_DATE)},
        {"id": t_project_link, "name": "Project", "type": "multipleRecordLinks",
         "options": {"linkedTableId": projects_tid, "isReversed": False,
                     "prefersSingleRecordLink": True, "inverseLinkFieldId": p_tasks_link}},
        {"id": t_done, "name": "Done", "type": "checkbox", "options": dict(_CHECKBOX)},
    ]

    # Project records first, so tasks can link to them by id.
    projects = {}
    proj_id_by_name = {}
    for row in [
        {"Name": "Website Redesign", "Status": "Active", "Start": "2024-01-02"},
        {"Name": "Mobile App", "Status": "On Hold", "Start": "2024-02-01"},
        {"Name": "Data Migration", "Status": "Complete", "Start": "2023-11-15"},
    ]:
        rid, rec = _record(row)
        projects[rid] = rec
        proj_id_by_name[row["Name"]] = rid

    # Task records linking to a project; collect the inverse mapping.
    tasks = {}
    tasks_by_project: dict[str, list[str]] = {}
    for row in [
        {"Name": "Design mockups", "Status": "Done", "Priority": 1, "Due": "2024-01-10", "Project": "Website Redesign", "Done": True},
        {"Name": "Build homepage", "Status": "In Progress", "Priority": 2, "Due": "2024-01-20", "Project": "Website Redesign"},
        {"Name": "User testing", "Status": "Todo", "Priority": 3, "Due": "2024-02-15", "Project": "Website Redesign"},
        {"Name": "Wireframes", "Status": "Todo", "Priority": 2, "Due": "2024-03-01", "Project": "Mobile App"},
        {"Name": "Export legacy data", "Status": "Done", "Priority": 1, "Due": "2023-12-01", "Project": "Data Migration", "Done": True},
    ]:
        proj_id = proj_id_by_name[row.pop("Project")]
        fields = dict(row)
        fields["Project"] = [proj_id]
        rid, rec = _record(fields)
        tasks[rid] = rec
        tasks_by_project.setdefault(proj_id, []).append(rid)

    # Back-fill the inverse link on each project record.
    for proj_id, task_ids in tasks_by_project.items():
        projects[proj_id]["fields"]["Tasks"] = list(task_ids)

    projects_table = {
        "id": projects_tid, "name": "Projects", "primaryFieldId": p_name,
        "fields": projects_fields, "views": [projects_view], "records": projects,
    }
    tasks_table = {
        "id": tasks_tid, "name": "Tasks", "primaryFieldId": t_name,
        "fields": tasks_fields, "views": [tasks_view], "records": tasks,
    }
    return {
        "id": base_id,
        "name": "Project Tracker",
        "permissionLevel": "create",
        "tables": {projects_tid: projects_table, tasks_tid: tasks_table},
    }
