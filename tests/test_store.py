"""Store: deterministic reset, seed shape/counts, and linked-record integrity."""

from twin import store


def _table(base_name: str, table_name: str) -> dict:
    base = next(b for b in store.state["bases"].values() if b["name"] == base_name)
    return next(t for t in base["tables"].values() if t["name"] == table_name)


def test_reset_is_byte_identical() -> None:
    store.reset_state()
    snap1 = store.snapshot()
    store.reset_state()
    snap2 = store.snapshot()
    assert snap1 == snap2


def test_seed_shape_and_counts() -> None:
    store.reset_state()
    counts = store.snapshot()["counts"]
    assert counts["bases"] == 2
    assert counts["tables"] == 3
    assert counts["records"] == 13
    assert counts["users"] == 1
    assert counts["tokens"] == 2


def test_seed_ids_and_timestamps_are_stable_across_reset() -> None:
    store.reset_state()
    table = next(iter(next(iter(store.state["bases"].values()))["tables"].values()))
    first = next(iter(table["records"].values()))
    rid, created = first["id"], first["createdTime"]
    assert rid.startswith("rec")
    assert created == "2024-01-01T00:00:00.000Z"

    store.reset_state()
    table2 = next(iter(next(iter(store.state["bases"].values()))["tables"].values()))
    first2 = next(iter(table2["records"].values()))
    assert first2["id"] == rid
    assert first2["createdTime"] == created


def test_linked_records_are_bidirectional() -> None:
    store.reset_state()
    tasks = _table("Project Tracker", "Tasks")
    projects = _table("Project Tracker", "Projects")
    task = next(iter(tasks["records"].values()))
    assert isinstance(task["fields"]["Project"], list)
    proj_id = task["fields"]["Project"][0]
    assert proj_id in projects["records"]
    assert task["id"] in projects["records"][proj_id]["fields"]["Tasks"]


def test_single_select_choices_have_sel_ids() -> None:
    store.reset_state()
    tasks = _table("Project Tracker", "Tasks")
    status = next(f for f in tasks["fields"] if f["name"] == "Status")
    assert status["type"] == "singleSelect"
    assert all(c["id"].startswith("sel") for c in status["options"]["choices"])


def test_empty_and_false_cells_are_omitted() -> None:
    store.reset_state()
    contacts = _table("CRM", "Contacts")
    grace = next(r for r in contacts["records"].values() if r["fields"]["Name"] == "Grace Hopper")
    assert "Active" not in grace["fields"]  # checkbox False -> omitted, per Airtable


def test_example_resources_preserved_until_s9() -> None:
    store.reset_state()
    assert store.state["example_resources"] == [
        {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
    ]
