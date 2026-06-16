"""Store: deterministic reset, seed shape, and stable seed IDs/timestamps."""

from twin import store


def test_reset_is_byte_identical() -> None:
    store.reset_state()
    snap1 = store.snapshot()
    store.reset_state()
    snap2 = store.snapshot()
    assert snap1 == snap2


def test_seed_shape_and_counts() -> None:
    store.reset_state()
    counts = store.snapshot()["counts"]
    assert counts["bases"] == 1
    assert counts["tables"] == 1
    assert counts["records"] == 3
    assert counts["users"] == 1


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


def test_example_resources_preserved_until_s9() -> None:
    store.reset_state()
    assert store.state["example_resources"] == [
        {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
    ]
