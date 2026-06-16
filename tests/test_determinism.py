"""Determinism guarantees: IDs, clock, and a no-entropy guard over twin/."""

import re
from pathlib import Path

from twin import clock, ids
from twin.config import ID_TOTAL_LEN

ID_RE = re.compile(r"^(app|tbl|fld|viw|rec|usr|com|ach)[0-9A-Za-z]{14}$")


def test_id_format_is_17_char_prefixed() -> None:
    rid = ids.make_id("rec", 1)
    assert len(rid) == ID_TOTAL_LEN == 17
    assert ID_RE.match(rid)


def test_make_id_is_pure() -> None:
    assert ids.make_id("rec", 5) == ids.make_id("rec", 5)
    assert ids.make_id("rec", 5) != ids.make_id("rec", 6)


def test_make_id_depends_on_prefix() -> None:
    assert ids.make_id("rec", 1)[3:] != ids.make_id("tbl", 1)[3:]


def test_next_id_sequence_is_deterministic_across_reset() -> None:
    ids.reset_counters()
    first = [ids.next_id("rec") for _ in range(5)]
    ids.reset_counters()
    second = [ids.next_id("rec") for _ in range(5)]
    assert first == second
    assert len(set(first)) == 5  # unique within a run


def test_named_helpers_use_correct_prefixes() -> None:
    ids.reset_counters()
    assert ids.base_id().startswith("app")
    assert ids.table_id().startswith("tbl")
    assert ids.record_id().startswith("rec")
    assert ids.webhook_id().startswith("ach")


def test_is_well_formed() -> None:
    ids.reset_counters()
    assert ids.is_well_formed(ids.record_id())
    assert not ids.is_well_formed("rec123")          # too short
    assert not ids.is_well_formed("zzz" + "a" * 14)  # unknown prefix


def test_clock_is_deterministic_and_advances() -> None:
    clock.reset()
    t0 = clock.stamp()
    t1 = clock.stamp()
    assert t0 == "2024-01-01T00:00:00.000Z"
    assert t1 == "2024-01-01T00:00:01.000Z"
    assert t1 > t0
    clock.reset()
    assert clock.stamp() == t0  # identical after reset


def test_twin_package_has_no_entropy_sources() -> None:
    forbidden = ["uuid", "random", "datetime.now", "utcnow",
                 "time.time", "perf_counter", "monotonic"]
    pkg = Path(__file__).resolve().parent.parent / "twin"
    offenders = []
    for py in sorted(pkg.rglob("*.py")):
        text = py.read_text()
        for bad in forbidden:
            if bad in text:
                offenders.append(f"{py.relative_to(pkg)}: contains {bad!r}")
    assert not offenders, offenders
