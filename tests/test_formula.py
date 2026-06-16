"""filterByFormula subset: evaluator unit tests + list integration (SPEC section 7)."""

from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from app import app
from twin import config, formula, store

FIELDS = {"Name", "Active", "Priority", "Company", "Due"}
ID2NAME: dict = {}


def _m(text: str, record: dict) -> bool:
    return formula.matches(formula.compile_formula(text, FIELDS, ID2NAME), record)


def test_string_equality() -> None:
    assert _m("{Name}='Ada'", {"Name": "Ada"})
    assert not _m("{Name}='Ada'", {"Name": "Alan"})


def test_bare_field_and_true() -> None:
    assert _m("Active=TRUE()", {"Active": True})
    assert not _m("Active=TRUE()", {"Active": False})


def test_numeric_comparison() -> None:
    assert _m("{Priority}>2", {"Priority": 3})
    assert not _m("{Priority}>2", {"Priority": 1})
    assert _m("{Priority}>=2", {"Priority": 2})


def test_and_or_not_xor() -> None:
    assert _m("AND({Priority}>1, {Active}=TRUE())", {"Priority": 2, "Active": True})
    assert not _m("AND({Priority}>1, {Active}=TRUE())", {"Priority": 2, "Active": False})
    assert _m("OR({Priority}=1, {Priority}=3)", {"Priority": 3})
    assert _m("NOT({Active}=TRUE())", {"Active": False})
    assert _m("XOR({Priority}=1, {Active}=TRUE())", {"Priority": 1, "Active": False})


def test_text_functions() -> None:
    assert _m("FIND('ada', LOWER({Name}))", {"Name": "Ada Lovelace"})
    assert not _m("FIND('xyz', {Name})", {"Name": "Ada"})
    assert _m("LEN({Name})>3", {"Name": "Grace"})


def test_arithmetic_and_concat() -> None:
    assert _m("{Priority}+1=3", {"Priority": 2})
    assert _m("({Name} & '!')='Ada!'", {"Name": "Ada"})


def test_is_empty_idiom() -> None:
    assert _m("{Company}=''", {})
    assert not _m("{Company}=''", {"Company": "NASA"})


def test_unknown_field_is_formula_error() -> None:
    with pytest.raises(formula.FormulaError):
        formula.compile_formula("{Nonexistent}=1", FIELDS, ID2NAME)


def test_malformed_is_formula_error() -> None:
    for bad in ("{Name}=", "AND({Name}='x'", "{Name} == 'x'", "FOO({Name})", ""):
        with pytest.raises(formula.FormulaError):
            formula.compile_formula(bad, FIELDS, ID2NAME)


# --- integration through the list endpoint ---

client = TestClient(app)
H = {"Authorization": f"Bearer {config.VALID_PAT}"}


def _crm_base() -> str:
    store.reset_state()
    return next(b for b in store.state["bases"].values() if b["name"] == "CRM")["id"]


def test_filter_by_formula_filters_records() -> None:
    base = _crm_base()
    url = f"/v0/{base}/Contacts?filterByFormula=" + quote("{Company}='NASA'")
    r = client.get(url, headers=H).json()
    assert len(r["records"]) == 1
    assert r["records"][0]["fields"]["Name"] == "Katherine Johnson"


def test_filter_by_formula_invalid_is_422() -> None:
    base = _crm_base()
    url = f"/v0/{base}/Contacts?filterByFormula=" + quote("{Name}=")
    r = client.get(url, headers=H)
    assert r.status_code == 422
    assert r.json()["error"]["type"] == "INVALID_FILTER_BY_FORMULA"
