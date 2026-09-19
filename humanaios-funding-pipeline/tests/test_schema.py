"""
tests/test_schema.py — HumanAIOS Funding Pipeline
Unit tests for schema, loader, and report generation.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from humanaios_funding.schema import Opportunity, Category, Status
from humanaios_funding.loader import (
    load_csv, load_json, save_csv, save_json, load_any, summarise
)


# ─── Fixtures ──────────────────────────────────────────────────────────────

def make_opp(**kwargs) -> Opportunity:
    defaults = dict(
        name="Test Grant",
        category=Category.ai_safety,
        sponsor="Test Org",
        url="https://example.org",
    )
    defaults.update(kwargs)
    return Opportunity(**defaults)


# ─── Schema tests ──────────────────────────────────────────────────────────

def test_valid_url():
    o = make_opp(url="https://example.org/path")
    assert o.url == "https://example.org/path"


def test_invalid_url_raises():
    with pytest.raises(Exception):
        make_opp(url="not-a-url")


def test_defaults():
    o = make_opp()
    assert o.native_eligible    is False
    assert o.ai_safety_relevant is False
    assert o.status             == Status.active
    assert o.eligibility_tags   == []
    assert o.trl_fit            == "any"


def test_deadline_not_soon():
    o = make_opp(deadline="2099-12-31")
    assert o.is_deadline_soon(30) is False


def test_deadline_soon():
    soon = (date.today() + timedelta(days=10)).isoformat()
    o = make_opp(deadline=soon)
    assert o.is_deadline_soon(30) is True


def test_deadline_past():
    o = make_opp(deadline="2000-01-01")
    assert o.is_deadline_soon(30) is False


def test_deadline_unparseable():
    o = make_opp(deadline="rolling")
    assert o.is_deadline_soon(30) is False


def test_priority_score_both_flags():
    both = make_opp(native_eligible=True, ai_safety_relevant=True,
                    category=Category.ai_safety)
    one  = make_opp(native_eligible=False, ai_safety_relevant=True,
                    category=Category.ai_safety)
    assert both.priority_score() <= one.priority_score()


def test_category_enum():
    o = make_opp(category="native")
    assert o.category == Category.native


def test_status_enum():
    o = make_opp(status="rolling")
    assert o.status == Status.rolling


# ─── Loader round-trip: JSON ───────────────────────────────────────────────

def test_json_round_trip():
    items = [
        make_opp(name="Grant A", eligibility_tags=["native", "llc"]),
        make_opp(name="Grant B", category=Category.contest,
                 award_size="$5,000", native_eligible=True),
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        path = f.name
    try:
        save_json(items, path)
        loaded = load_json(path)
        assert len(loaded) == 2
        assert loaded[0].name == "Grant A"
        assert loaded[0].eligibility_tags == ["native", "llc"]
        assert loaded[1].native_eligible is True
    finally:
        os.unlink(path)


# ─── Loader round-trip: CSV ────────────────────────────────────────────────

def test_csv_round_trip():
    items = [
        make_opp(
            name="CSV Grant",
            category=Category.native,
            sponsor="CN",
            url="https://cherokee.org",
            eligibility_tags=["cherokee", "llc"],
            native_eligible=True,
            notes="Test note",
        ),
    ]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    try:
        save_csv(items, path)
        loaded = load_csv(path)
        assert len(loaded) == 1
        assert loaded[0].name == "CSV Grant"
        assert loaded[0].native_eligible is True
        assert "cherokee" in loaded[0].eligibility_tags
    finally:
        os.unlink(path)


# ─── load_any dispatch ─────────────────────────────────────────────────────

def test_load_any_json(tmp_path):
    items = [make_opp(name="A"), make_opp(name="B")]
    p = tmp_path / "test.json"
    save_json(items, p)
    loaded = load_any(p)
    assert {i.name for i in loaded} == {"A", "B"}


def test_load_any_csv(tmp_path):
    items = [make_opp(name="X")]
    p = tmp_path / "test.csv"
    save_csv(items, p)
    loaded = load_any(p)
    assert loaded[0].name == "X"


# ─── Summarise ─────────────────────────────────────────────────────────────

def test_summarise():
    items = [
        make_opp(native_eligible=True,  ai_safety_relevant=True,
                 category=Category.native, status=Status.active),
        make_opp(native_eligible=False, ai_safety_relevant=True,
                 category=Category.ai_safety, status=Status.rolling),
        make_opp(native_eligible=True,  ai_safety_relevant=False,
                 category=Category.compute_credit, status=Status.active),
    ]
    s = summarise(items)
    assert s.total             == 3
    assert s.native_eligible   == 2
    assert s.ai_safety_relevant== 2
    assert s.both_flags        == 1
    assert s.active_rolling    == 3
    assert s.by_category["native"] == 1


# ─── Edge cases ────────────────────────────────────────────────────────────

def test_empty_tags():
    o = make_opp()
    assert o.eligibility_tags == []


def test_notes_none():
    o = make_opp()
    assert o.notes is None


def test_url_ok_none():
    o = make_opp()
    assert o.url_ok is None
