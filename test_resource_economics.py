"""
test_resource_economics.py — tests for RBE-OPS v0.1 (Q-RBE-01).

Three things are under test, in order of how badly they fail if wrong:

1. The unit registry keeps its own rules — no registered unit without an
   instrument, no unit in an undeclared dimension, no unit without a falsifier,
   and no default conversion between dimensions.
2. The ledger refuses rather than guesses: unknown units, sourceless events,
   unpriced claims, self-declared capacity on the constraint unit, prices with
   too small an n, events after close, and any edit to a prior line.
3. The queue reshape is DORMANT. `from_constants()` must return the incumbent
   formula while QUEUE_SCORING_MODE carries molt_id null — the code must not be
   able to flip its own gate.

Run: python3 -m pytest test_resource_economics.py -q
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent
UNITS_PATH = ROOT / "RESOURCE_UNITS.yaml"
sys.path.insert(0, str(ROOT))

from priority_queue_engine import (  # noqa: E402
    MODE_IMPACT,
    MODE_RESOURCE,
    PriorityQueueEngine,
    QueueItem,
)


def _load(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


census = _load("resource_census_v0_1", "tools/resource_census_v0_1.py")
ledger = _load("resource_ledger_v0_1", "tools/resource_ledger_v0_1.py")


@pytest.fixture(scope="module")
def units() -> dict:
    return yaml.safe_load(UNITS_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- registry
class TestUnitRegistry:
    def test_registry_parses_and_declares_itself_candidate(self, units):
        assert units["status"] == "CANDIDATE"
        assert units["ratification_hash"] is None, "a Z1 proposal must not carry a hash"

    def test_every_registered_unit_has_an_instrument(self, units):
        for u in units["units"]:
            if u["status"] != "REGISTERED":
                continue
            primary = (u.get("instrument") or {}).get("primary")
            assert primary, f"{u['symbol']} is REGISTERED with no instrument"

    def test_candidate_units_state_their_blocker(self, units):
        cands = [u for u in units["units"] if u["status"] == "CANDIDATE"]
        assert cands, "the registry should show its gaps, not hide them"
        for u in cands:
            assert u.get("blocker"), f"{u['symbol']} is CANDIDATE with no stated blocker"

    def test_every_unit_has_a_falsifier(self, units):
        for u in units["units"]:
            assert u.get("falsifier"), f"{u['symbol']} cannot be wrong, so it cannot be a unit"

    def test_dimensions_are_declared_and_non_commensurable(self, units):
        declared = set(units["dimensions"])
        for u in units["units"]:
            assert u["dimension"] in declared, f"{u['symbol']} is in an undeclared dimension"
        for name, d in units["dimensions"].items():
            assert d["commensurable_with"] == [], f"{name} declares a default conversion"

    def test_no_default_conversion_policy(self, units):
        assert units["policy"]["conversion"] == "none_by_default"
        assert units["policy"]["shadow_price_min_n"] >= 2

    def test_constraint_designation_is_falsifiable(self, units):
        c = units["constraint"]
        assert c["unit"] in {u["symbol"] for u in units["units"]}
        assert c.get("falsifier")

    def test_liability_units_are_negative_signed(self, units):
        by = {u["symbol"]: u for u in units["units"]}
        for sym in ("OBL-open", "GAP-row", "STALE-day"):
            assert by[sym]["sign"] == "negative", f"{sym} must be a liability"

    def test_demand_priors_are_labelled_low_confidence(self, units):
        priors = units["demand_priors"]
        assert priors["confidence"] == "low"
        assert priors.get("falsifier")
        for cls, row in priors["classes"].items():
            assert row["rat_min"] > 0 and row.get("basis"), cls

    def test_registry_stays_small_enough_to_reason_about(self, units):
        # Unit inflation is a named failure mode: a registry nobody can hold in
        # their head produces numbers nobody checks.
        assert len(units["units"]) <= 20


# ---------------------------------------------------------------- census
class TestCensus:
    def test_smoke_test_passes(self):
        assert census.run_smoke_test() == 0

    def test_utilization_is_undefined_without_a_declared_capacity(self, units, tmp_path):
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["constraint"]["utilization"] is None
        assert c["constraint"]["capacity_basis"] == "UNMEASURED"
        assert c["clearance_sensitivity_weeks"], "a what-if table is still owed"

    def test_debt_is_labelled_prior_not_measured(self, units, tmp_path):
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["obligations"]["debt_basis"] == "PRIOR"
        for row in c["obligations"]["by_class"].values():
            assert row["price_basis"] in ("PRIOR", "UNPRICED")

    def test_yield_density_is_unmeasured_until_a_spend_lands(self, units, tmp_path):
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["yield_density"]["value"] is None
        assert c["yield_density"]["basis"] == "UNMEASURED"

    def test_every_class_carries_a_named_source(self, units, tmp_path):
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        for name, row in c["obligations"]["by_class"].items():
            assert row["source"], f"{name} has no source"
            assert row["basis"] == "MEASURED"

    def test_live_tree_census_is_runnable_and_self_consistent(self, units):
        c = census.run_census(ROOT, units, capacity=None, today=date.today())
        by = c["obligations"]["by_class"]
        assert c["obligations"]["open_items"] == sum(r["count"] for r in by.values())
        assert c["obligations"]["debt_rat_min"] == sum(
            r["load_rat_min"] for r in by.values() if r["load_rat_min"] is not None)
        assert not c["obligations"]["unpriced_classes"], "every obligation class needs a prior"

    def test_this_proposals_own_constants_are_counted_against_the_constraint(self, units):
        # The proposal is not exempt from its own accounting: four new
        # unratified constants are four new obligations.
        c = census.run_census(ROOT, units, capacity=None, today=date.today())
        assert c["obligations"]["by_class"]["constant_ratification"]["count"] >= 4


# ---------------------------------------------------------------- ledger
def run_ledger(argv: list[str]) -> int:
    """Invoke the ledger CLI in-process; a non-zero return is a refusal.

    Refusals exit with a message string rather than a code (`sys.exit("REFUSED: …")`),
    which SystemExit carries verbatim — anything that is not 0 or None is a failure.
    """
    try:
        return ledger.main(argv) or 0
    except SystemExit as e:
        if e.code is None:
            return 0
        return e.code if isinstance(e.code, int) else 1


@pytest.fixture()
def led(tmp_path) -> str:
    path = str(tmp_path / "L.jsonl")
    assert run_ledger(["init", path]) == 0
    return path


class TestLedgerRefusals:
    def test_smoke_test_passes(self):
        assert ledger.run_smoke_test() == 0

    def test_genesis_pins_the_units_registry_hash(self, led):
        first = json.loads(Path(led).read_text(encoding="utf-8").splitlines()[0])
        assert first["type"] == "OPEN"
        assert len(first["units_registry_sha256"]) == 64
        assert first["units_ratification_hash"] is None

    def test_unknown_unit_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "NOPE=1"]) != 0

    def test_candidate_unit_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=1,TRUST-pt=1"]) != 0

    def test_claim_without_the_constraint_unit_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "Z1-ktok=10"]) != 0

    def test_spend_without_source_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        assert run_ledger(["spend", led, "Q-1", "RAT-min", "5", "--by", "Z2"]) != 0

    def test_non_positive_quantity_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        assert run_ledger(["spend", led, "Q-1", "RAT-min", "0", "--by", "Z2", "--source", "s"]) != 0

    def test_spending_an_output_unit_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        assert run_ledger(["spend", led, "Q-1", "EVID-row", "1", "--by", "Z3", "--source", "s"]) != 0

    def test_yielding_an_input_unit_is_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        assert run_ledger(["yield", led, "Q-1", "RAT-min", "1", "--by", "Z3", "--source", "s"]) != 0

    def test_waste_only_takes_liability_units(self, led):
        assert run_ledger(["waste", led, "GAP-row", "1", "--by", "Z1", "--source", "recon"]) == 0
        assert run_ledger(["waste", led, "EVID-row", "1", "--by", "Z1", "--source", "s"]) != 0

    def test_constraint_capacity_needs_a_z2_hash(self, led):
        assert run_ledger(["cap", led, "RAT-min", "120", "--by", "Z1", "--source", "guess"]) != 0
        assert run_ledger(["cap", led, "RAT-min", "120", "--by", "Z2", "--hash", "abc",
                           "--source", "decl"]) == 0

    def test_non_constraint_capacity_does_not_need_a_hash(self, led):
        assert run_ledger(["cap", led, "Z1-ktok", "100", "--by", "Z1", "--source",
                           "behavior_spec.json"]) == 0

    def test_price_below_min_n_is_refused(self, led):
        assert run_ledger(["price", led, "Z3-hr", "Z1-ktok", "25", "--n", "3", "--window", "w",
                           "--constraint", "RAT-min", "--source", "s"]) != 0

    def test_price_without_window_or_constraint_is_refused(self, led):
        assert run_ledger(["price", led, "Z3-hr", "Z1-ktok", "25", "--n", "12",
                           "--constraint", "RAT-min", "--source", "s"]) != 0
        assert run_ledger(["price", led, "Z3-hr", "Z1-ktok", "25", "--n", "12", "--window", "w",
                           "--source", "s"]) != 0

    def test_a_complete_price_is_accepted_and_carries_its_provenance(self, led):
        assert run_ledger(["price", led, "Z3-hr", "Z1-ktok", "25", "--n", "12",
                           "--window", "2026-W37", "--constraint", "RAT-min",
                           "--source", "sha:abc"]) == 0
        ev = json.loads(Path(led).read_text(encoding="utf-8").splitlines()[-1])
        assert ev["type"] == "PRICE" and ev["n"] == 12 and ev["window"] and ev["source"]
        assert ev["from_dimension"] != ev["to_dimension"], "a same-dimension price is not the point"

    def test_order_closes_once_and_takes_no_events_after(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        assert run_ledger(["spend", led, "Q-1", "RAT-min", "6", "--by", "Z2", "--source", "s"]) == 0
        assert run_ledger(["close", led, "Q-1", "--by", "Z1", "--source", "s"]) == 0
        assert run_ledger(["close", led, "Q-1", "--by", "Z1", "--source", "s"]) != 0
        assert run_ledger(["spend", led, "Q-1", "RAT-min", "1", "--by", "Z2", "--source", "s"]) != 0

    def test_tampering_breaks_the_chain(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        lines = Path(led).read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[-1])
        obj["budget"]["RAT-min"] = 1
        lines[-1] = json.dumps(obj, sort_keys=True)
        Path(led).write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert run_ledger(["verify", led]) != 0

    def test_yield_density_is_yield_over_constraint_spend(self, led):
        run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"])
        run_ledger(["spend", led, "Q-1", "RAT-min", "8", "--by", "Z2", "--source", "s"])
        run_ledger(["yield", led, "Q-1", "EVID-row", "4", "--by", "Z3", "--source", "s"])
        run_ledger(["close", led, "Q-1", "--by", "Z1", "--source", "s"])
        evs = ledger.read(led)
        state = ledger.project(evs)
        assert ledger.density(state["orders"]["Q-1"], "RAT-min") == 0.5

    def test_live_ledger_chain_is_intact(self):
        live = ROOT / "ledgers" / "RESOURCE_LEDGER.jsonl"
        if not live.exists():
            pytest.skip("no live resource ledger")
        assert ledger.verify(ledger.read(str(live))) is None


# ---------------------------------------------------------------- queue
def _queue(mode):
    q = PriorityQueueEngine(mode=mode)
    q.add_item(QueueItem(molt_id="FREE-HI", status="READY", impact=9, cost={"RAT-min": 0}))
    q.add_item(QueueItem(molt_id="CHEAP", status="READY", impact=5, cost={"RAT-min": 10}))
    q.add_item(QueueItem(molt_id="DEAR", status="READY", impact=6, cost={"RAT-min": 60}))
    q.add_item(QueueItem(molt_id="UNPRICED", status="READY", impact=8))
    return q


class TestQueueReshape:
    def test_incumbent_formula_is_untouched(self):
        q = PriorityQueueEngine()
        assert q.mode == MODE_IMPACT
        a = QueueItem(molt_id="A", status="READY", impact=10, blocks=["B"])
        b = QueueItem(molt_id="B", status="BLOCKED", impact=5, blocked_by=["A"])
        q.add_item(a)
        q.add_item(b)
        assert a.calculate_score(q.items) == 15

    def test_impact_mode_ignores_cost_entirely(self):
        q = _queue(MODE_IMPACT)
        assert q.get_next_ready()["molt_id"] == "FREE-HI"   # highest impact, 9
        gate = q.apply_ready_gate()
        assert gate["ready_items"] == 4, "impact mode must not refuse an unpriced row"

    def test_unpriced_row_is_refused_in_resource_mode(self):
        gate = _queue(MODE_RESOURCE).apply_ready_gate()
        refused = [d for d in gate["blocked"] if d["molt_id"] == "UNPRICED"]
        assert refused and "UNPRICED" in refused[0]["reason"]

    def test_zero_cost_is_priced_and_missing_cost_is_not(self):
        free = QueueItem(molt_id="F", status="READY", impact=1, cost={"RAT-min": 0})
        blank = QueueItem(molt_id="B", status="READY", impact=1)
        assert free.is_priced() and free.band() == "A"
        assert not blank.is_priced() and blank.band() == "UNPRICED"

    def test_band_a_outranks_band_b_even_at_lower_impact(self):
        q = PriorityQueueEngine(mode=MODE_RESOURCE)
        q.add_item(QueueItem(molt_id="FREE-LO", status="READY", impact=1, cost={"RAT-min": 0}))
        q.add_item(QueueItem(molt_id="PAID-HI", status="READY", impact=99, cost={"RAT-min": 1}))
        assert q.get_next_ready()["molt_id"] == "FREE-LO"

    def test_band_b_orders_by_density_not_impact(self):
        q = _queue(MODE_RESOURCE)
        order = [r["molt_id"] for r in q.report_queue()["queue"]]
        assert order.index("CHEAP") < order.index("DEAR"), "0.5/min must beat 0.1/min"
        assert q.items["CHEAP"].density(q.items) == 0.5
        assert q.items["DEAR"].density(q.items) == 0.1

    def test_density_is_undefined_for_band_a_and_unpriced(self):
        q = _queue(MODE_RESOURCE)
        assert q.items["FREE-HI"].density(q.items) is None
        assert q.items["UNPRICED"].density(q.items) is None

    def test_constraint_demand_excludes_unpriced_rows(self):
        report = _queue(MODE_RESOURCE).report_queue()
        assert report["constraint_demand"] == 70      # 0 + 10 + 60
        assert report["unpriced_count"] == 1

    def test_unknown_mode_is_rejected(self):
        with pytest.raises(ValueError):
            PriorityQueueEngine(mode="vibes")


class TestModeIsGoverned:
    def test_resource_mode_is_dormant_while_the_constant_is_unratified(self):
        q = PriorityQueueEngine.from_constants(str(ROOT / "constants.json"))
        assert q.mode == MODE_IMPACT, "an unratified constant must not change behaviour"
        assert q.mode_molt_id is None

    def test_the_live_constant_is_present_and_unratified(self):
        consts = json.loads((ROOT / "constants.json").read_text(encoding="utf-8"))["constants"]
        row = next(c for c in consts if c["name"] == "QUEUE_SCORING_MODE")
        assert row["molt_id"] is None
        assert row["current_value"] == "impact"
        assert row.get("falsifier") and row.get("revert_rule")

    def test_a_ratified_constant_activates_resource_mode(self, tmp_path):
        path = tmp_path / "constants.json"
        path.write_text(json.dumps({"constants": [
            {"name": "QUEUE_SCORING_MODE", "current_value": "resource", "molt_id": "M-TEST-01"},
            {"name": "CONSTRAINT_UNIT", "current_value": "RAT-min", "molt_id": "M-TEST-02"},
        ]}), encoding="utf-8")
        q = PriorityQueueEngine.from_constants(str(path))
        assert q.mode == MODE_RESOURCE and q.mode_molt_id == "M-TEST-01"

    def test_resource_value_without_a_molt_id_does_not_activate(self, tmp_path):
        path = tmp_path / "constants.json"
        path.write_text(json.dumps({"constants": [
            {"name": "QUEUE_SCORING_MODE", "current_value": "resource", "molt_id": None},
        ]}), encoding="utf-8")
        assert PriorityQueueEngine.from_constants(str(path)).mode == MODE_IMPACT

    def test_missing_constants_file_falls_back_to_the_incumbent(self, tmp_path):
        assert PriorityQueueEngine.from_constants(str(tmp_path / "nope.json")).mode == MODE_IMPACT
