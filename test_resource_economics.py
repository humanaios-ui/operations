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
import re
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
    POLICY_ALLOWED,
    POLICY_REFUSED,
    POLICY_WARNED,
    PriorityQueueEngine,
    QueueItem,
)

# Resource mode is unreachable without naming the molt that authorised it.
# Tests that exercise the mode name a test molt; they are not a way around the gate.
TEST_MOLT = "M-TEST-RBE-01"

# Artifacts whose ratification_hash was minted before `ratify.py --artifact`
# existed, and therefore verifies against nothing.
#
# This list lives in CODE, reviewed like any other change, for the same reason
# `UNRATIFIED_ZONE_CLAIMS` does in .tool-control/validate.py: an exemption that
# an artifact could grant itself by setting a field is not an exemption, it is a
# bypass. A registry ratified from here on must carry a verifiable signature.
#
# RESOURCE_UNITS.yaml leaves this list the moment Z2 runs:
#     python3 .z1-control/ratify.py --artifact RESOURCE_UNITS.yaml \
#         --decision ACCEPT --by Night --apply
# and the test above FAILS if it is still listed once it verifies, so the
# exemption cannot outlive its cause.
UNVERIFIED_ARTIFACT_RATIFICATIONS = frozenset({"RESOURCE_UNITS.yaml"})


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
    def test_registry_is_ratified_and_says_who_and_when(self, units):
        assert units["status"] == "RATIFIED"
        assert units["ratification_decision"] == "ACCEPT"
        assert units["ratified_by"], "a ratification is somebody's act"
        assert units["ratified_at"]
        assert units["ratification_hash"], "a ratified registry must carry a hash"

    def test_ratification_hash_is_a_sha256_and_not_a_slug(self, units):
        """The weakest property the hash must have, and the one it had lost.

        The three rulings of 2026-09-08 carry hand-written slugs, and
        `ratify.py --verify` reports them as "content not pinned" rather than
        pretending otherwise. A slug in this field would leave the registry
        ratified by a value that pins nothing.
        """
        assert re.fullmatch(r"[0-9a-f]{64}", str(units["ratification_hash"])), \
            "ratification_hash must be a sha256, not a slug"

    def test_ratification_hash_verifies_against_the_content(self, units):
        """The strong property: recompute the signature and compare.

        This is what `assert ratification_hash is not None` could never do. The
        digest covers the registry's content with the ratification fields
        excluded, so editing a unit, a policy or a prior breaks it while fixing
        a comment does not.

        UNVERIFIED_ARTIFACT_RATIFICATIONS below is an explicit, reviewed record
        of hashes minted before `ratify.py` could sign an artifact — not a way
        for a new one to skip this. A registry that is not on that list must
        verify, and nothing in this file can add itself to it.
        """
        ratify = _load("z1_ratify", ".z1-control/ratify.py")
        recomputed = ratify.artifact_signature(
            units, str(units["ratified_by"]), str(units["ratified_at"]),
            str(units["ratification_decision"]))
        if "RESOURCE_UNITS.yaml" in UNVERIFIED_ARTIFACT_RATIFICATIONS:
            assert recomputed != units["ratification_hash"], (
                "RESOURCE_UNITS.yaml now verifies — remove it from "
                "UNVERIFIED_ARTIFACT_RATIFICATIONS so the exemption cannot outlive its cause")
            pytest.skip("hash predates ratify.py --artifact; see "
                        "UNVERIFIED_ARTIFACT_RATIFICATIONS")
        assert recomputed == units["ratification_hash"], (
            "ratification_hash does not match the content it claims to ratify")

    def test_header_comment_agrees_with_the_status_field(self):
        """The defect that produced this test: lines 3-4 said CANDIDATE, and
        nothing said they were wrong, for as long as nobody happened to read
        them next to the field they describe."""
        head = UNITS_PATH.read_text(encoding="utf-8").split("---", 1)[0]
        status = yaml.safe_load(UNITS_PATH.read_text(encoding="utf-8"))["status"]
        assert status in head, (
            f"the header comment does not mention status {status!r}; it describes "
            f"a state the file is not in")
        other = "CANDIDATE" if status != "CANDIDATE" else "RATIFIED"
        assert f"Status: {other}" not in head, \
            f"the header still announces 'Status: {other}' while status is {status!r}"

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

    def test_yield_density_is_measured_once_the_ledger_holds_a_closed_order(self, units, tmp_path):
        led = str(tmp_path / "ledgers" / "RESOURCE_LEDGER.jsonl")
        Path(led).parent.mkdir(parents=True, exist_ok=True)
        assert run_ledger(["init", led]) == 0
        run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"])
        run_ledger(["spend", led, "Q-1", "RAT-min", "8", "--by", "Z2", "--source", "s"])
        run_ledger(["yield", led, "Q-1", "EVID-row", "4", "--by", "Z3", "--source", "s"])
        run_ledger(["close", led, "Q-1", "--by", "Z1", "--source", "s"])
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["yield_density"]["basis"] == "MEASURED"
        assert c["yield_density"]["value"] == 0.5
        assert c["ledger"]["chain"] == "OK"

    def test_capacity_comes_from_the_ledger_and_an_override_says_so(self, units, tmp_path):
        led = str(tmp_path / "ledgers" / "RESOURCE_LEDGER.jsonl")
        Path(led).parent.mkdir(parents=True, exist_ok=True)
        assert run_ledger(["init", led]) == 0
        assert run_ledger(["cap", led, "RAT-min", "120", "--by", "Z2", "--hash", "c" * 64,
                           "--source", "Z2 declaration"]) == 0
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["constraint"]["capacity_basis"] == "DECLARED"
        assert c["constraint"]["capacity_per_week"] == 120
        assert c["constraint"]["utilization"] is not None

        over = census.run_census(tmp_path, units, capacity=1.0, today=date(2026, 6, 1))
        assert over["constraint"]["capacity_basis"] == "OVERRIDE"

    def test_a_broken_ledger_chain_reports_nothing_rather_than_zero(self, units, tmp_path):
        led = tmp_path / "ledgers" / "RESOURCE_LEDGER.jsonl"
        led.parent.mkdir(parents=True, exist_ok=True)
        assert run_ledger(["init", str(led)]) == 0
        assert run_ledger(["cap", str(led), "Z1-ktok", "50", "--source", "s"]) == 0
        lines = led.read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[-1]); obj["qty"] = 5
        lines[-1] = json.dumps(obj, sort_keys=True)
        led.write_text("\n".join(lines) + "\n", encoding="utf-8")
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["ledger"]["chain"] == "BROKEN"
        assert c["constraint"]["capacity_basis"] == "UNMEASURED"

    def test_an_unreadable_document_registry_is_unmeasured_not_zero(self, units, tmp_path):
        (tmp_path / "document-registry.yaml").write_text("documents: [{a: 1\n", encoding="utf-8")
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        row = c["obligations"]["by_class"]["doc_owner_approval"]
        assert row["count"] is None and row["basis"] == "UNMEASURED"
        assert "doc_owner_approval" in c["obligations"]["unmeasured_classes"]

    def test_constraint_designation_reports_whether_it_was_compared(self, units, tmp_path):
        c = census.run_census(tmp_path, units, capacity=None, today=date(2026, 6, 1))
        assert c["constraint_designation"]["basis"] == "ASSUMED"
        assert c["constraint_designation"]["units_with_comparable_utilization"] == 0
        assert units["constraint"]["unit"] in c["input_units"]

    def test_rat_art_is_reported_as_a_proxy(self, units):
        c = census.run_census(ROOT, units, capacity=None, today=date.today())
        assert c["stocks"]["RAT-art"]["basis"] == "PROXY"

    def test_units_command_honours_its_registry_argument(self, tmp_path, capsys):
        alt = tmp_path / "u.yaml"
        alt.write_text(UNITS_PATH.read_text(encoding="utf-8").replace(
            "symbol: RAT-min", "symbol: XX-min", 1), encoding="utf-8")
        census.cmd_units(alt)
        assert "XX-min" in capsys.readouterr().out

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

    def test_genesis_pins_the_units_registry_hash(self, led, units):
        """Genesis records BOTH hashes, and they answer different questions.

        `units_registry_sha256` is the ledger's own digest of the file it read —
        it detects the registry changing under an open ledger. `units_ratification_hash`
        is Z2's signature copied from the registry — it records which ratified
        version this ledger was opened against. Before Z2 accepted the registry
        the second was null; asserting it stays null would now assert the
        registry is unratified.
        """
        first = json.loads(Path(led).read_text(encoding="utf-8").splitlines()[0])
        assert first["type"] == "OPEN"
        assert len(first["units_registry_sha256"]) == 64
        assert first["units_ratification_hash"] == units["ratification_hash"], \
            "genesis must pin the ratification the registry actually carries"

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

    def test_nan_and_infinity_are_refused(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"]) == 0
        for bad in ("nan", "inf", "-inf"):
            assert run_ledger(["spend", led, "Q-1", "RAT-min", bad, "--by", "Z2",
                               "--source", "s"]) != 0, bad
        assert run_ledger(["claim", led, "Q-NAN", "--budget", "RAT-min=nan"]) != 0

    def test_a_zero_constraint_budget_is_a_price_not_a_blank(self, led):
        # Band A: the row declares that it draws nothing on the bottleneck.
        assert run_ledger(["claim", led, "Q-FREE", "--budget", "RAT-min=0,Z1-ktok=5"]) == 0
        ev = json.loads(Path(led).read_text(encoding="utf-8").splitlines()[-1])
        assert ev["budget"]["RAT-min"] == 0.0

    def test_claim_persists_its_source(self, led):
        assert run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10",
                           "--source", "z1-inbox/x.md"]) == 0
        ev = json.loads(Path(led).read_text(encoding="utf-8").splitlines()[-1])
        assert ev["source"] == "z1-inbox/x.md"

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
        # A label is not a signature: CLAUDE.md defines the Z2 hash as a sha256.
        assert run_ledger(["cap", led, "RAT-min", "120", "--by", "Z2", "--hash", "abc",
                           "--source", "decl"]) != 0
        assert run_ledger(["cap", led, "RAT-min", "120", "--by", "Z2", "--hash", "b" * 64,
                           "--source", "decl"]) == 0

    def test_non_constraint_capacity_does_not_need_a_hash(self, led):
        assert run_ledger(["cap", led, "Z1-ktok", "100", "--by", "Z1", "--source",
                           "behavior_spec.json"]) == 0

    def test_price_below_min_n_is_refused(self, led):
        assert run_ledger(["price", led, "Z3-hr", "Z1-ktok", "25", "--n", "3", "--window", "w",
                           "--constraint", "RAT-min", "--source", "s"]) != 0

    def test_same_dimension_price_is_refused(self, led):
        # PRICE is the cross-dimension escape hatch; EVID-row and CAL-pt are
        # both evidence, so a rate between them is not what the rule permits.
        assert run_ledger(["price", led, "EVID-row", "CAL-pt", "2", "--n", "12",
                           "--window", "w", "--constraint", "RAT-min", "--source", "s"]) != 0

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

    def test_yield_density_counts_one_dimension_only(self, led):
        # Evidence and assurance do not add. Density divides by the constraint
        # unit, so its numerator must stay inside one dimension.
        run_ledger(["claim", led, "Q-1", "--budget", "RAT-min=10"])
        run_ledger(["spend", led, "Q-1", "RAT-min", "8", "--by", "Z2", "--source", "s"])
        run_ledger(["yield", led, "Q-1", "EVID-row", "4", "--by", "Z3", "--source", "s"])
        run_ledger(["yield", led, "Q-1", "RAT-art", "40", "--by", "Z2", "--source", "s"])
        run_ledger(["close", led, "Q-1", "--by", "Z1", "--source", "s"])
        state = ledger.project(ledger.read(led))
        units_reg = ledger.Units(UNITS_PATH)
        assert ledger.density(state["orders"]["Q-1"], "RAT-min", units_reg) == 0.5
        assert ledger.density_by_unit(state["orders"]["Q-1"], "RAT-min") == {
            "EVID-row": 0.5, "RAT-art": 5.0}

    def test_registry_drift_is_visible_and_repinnable(self, led, tmp_path):
        # Hash-linking the events does not protect the unit definitions behind
        # them; drift must be reported, and recorded in the chain when accepted.
        alt = tmp_path / "units.yaml"
        alt.write_text(UNITS_PATH.read_text(encoding="utf-8") + "\n# a change\n", encoding="utf-8")
        evs = ledger.read(led)
        pin = ledger.registry_pin_status(evs, ledger.Units(alt))
        assert pin["drift"] is True
        assert run_ledger(["verify", led, "--units", str(alt), "--strict-pin"]) != 0
        assert run_ledger(["repin", led, "--units", str(alt), "--source", "sha:abc",
                           "--reason", "Z2 ratified"]) == 0
        assert run_ledger(["verify", led, "--units", str(alt), "--strict-pin"]) == 0
        assert run_ledger(["repin", led, "--units", str(alt), "--source", "s"]) != 0  # nothing to do

    def test_live_ledger_chain_is_intact(self):
        live = ROOT / "ledgers" / "RESOURCE_LEDGER.jsonl"
        if not live.exists():
            pytest.skip("no live resource ledger")
        assert ledger.verify(ledger.read(str(live))) is None


# ---------------------------------------------------------------- queue
def _queue(mode, policy=POLICY_REFUSED):
    q = (PriorityQueueEngine(mode=mode, mode_molt_id=TEST_MOLT, unpriced_policy=policy)
         if mode == MODE_RESOURCE else PriorityQueueEngine(mode=mode))
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
        q = PriorityQueueEngine(mode=MODE_RESOURCE, mode_molt_id=TEST_MOLT)
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

    def test_resource_mode_cannot_be_constructed_without_a_molt_id(self):
        # The gate changes which rows may start, so it is not reachable by a
        # caller who simply asks for it.
        with pytest.raises(ValueError, match="mode_molt_id"):
            PriorityQueueEngine(mode=MODE_RESOURCE)

    def test_unknown_unpriced_policy_is_rejected(self):
        with pytest.raises(ValueError):
            PriorityQueueEngine(mode=MODE_IMPACT, unpriced_policy="maybe")

    def test_unpriced_policy_governs_the_gate(self):
        refused = _queue(MODE_RESOURCE, POLICY_REFUSED).apply_ready_gate()
        assert [d["molt_id"] for d in refused["blocked"]] == ["UNPRICED"]

        warned = _queue(MODE_RESOURCE, POLICY_WARNED).apply_ready_gate()
        assert warned["ready_items"] == 4
        row = next(d for d in warned["ready"] if d["molt_id"] == "UNPRICED")
        assert "UNPRICED" in row["reason"] and row["can_start"]

        allowed = _queue(MODE_RESOURCE, POLICY_ALLOWED).apply_ready_gate()
        assert allowed["ready_items"] == 4
        assert all("UNPRICED" not in d["reason"] for d in allowed["ready"])

    def test_negative_and_non_finite_costs_are_rejected(self):
        for bad in (-1, float("nan"), float("inf"), "10"):
            item = QueueItem(molt_id="BAD", status="READY", impact=1, cost={"RAT-min": bad})
            with pytest.raises(ValueError):
                item.constraint_cost()


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
            {"name": "CONSTRAINT_UNIT", "current_value": "Z3-hr", "molt_id": "M-TEST-02"},
            {"name": "UNPRICED_ROW_POLICY", "current_value": "REFUSED_TO_START",
             "molt_id": "M-TEST-03"},
        ]}), encoding="utf-8")
        q = PriorityQueueEngine.from_constants(str(path))
        assert q.mode == MODE_RESOURCE and q.mode_molt_id == "M-TEST-01"
        assert q.constraint_unit == "Z3-hr"
        assert q.unpriced_policy == POLICY_REFUSED

    def test_an_unratified_constraint_unit_does_not_take_effect(self, tmp_path):
        # A Z1 edit to CONSTRAINT_UNIT must not silently move the binding unit
        # once the mode is ratified: each constant carries its own dormancy.
        path = tmp_path / "constants.json"
        path.write_text(json.dumps({"constants": [
            {"name": "QUEUE_SCORING_MODE", "current_value": "resource", "molt_id": "M-TEST-01"},
            {"name": "CONSTRAINT_UNIT", "current_value": "Z1-ktok", "molt_id": None},
        ]}), encoding="utf-8")
        q = PriorityQueueEngine.from_constants(str(path))
        assert q.constraint_unit == "RAT-min"

    def test_an_unratified_policy_falls_back_to_its_prior(self, tmp_path):
        path = tmp_path / "constants.json"
        path.write_text(json.dumps({"constants": [
            {"name": "QUEUE_SCORING_MODE", "current_value": "resource", "molt_id": "M-TEST-01"},
            {"name": "UNPRICED_ROW_POLICY", "current_value": "REFUSED_TO_START",
             "prior_value": "ALLOWED", "molt_id": None},
        ]}), encoding="utf-8")
        assert PriorityQueueEngine.from_constants(str(path)).unpriced_policy == POLICY_ALLOWED

    def test_resource_value_without_a_molt_id_does_not_activate(self, tmp_path):
        path = tmp_path / "constants.json"
        path.write_text(json.dumps({"constants": [
            {"name": "QUEUE_SCORING_MODE", "current_value": "resource", "molt_id": None},
        ]}), encoding="utf-8")
        assert PriorityQueueEngine.from_constants(str(path)).mode == MODE_IMPACT

    def test_missing_constants_file_falls_back_to_the_incumbent(self, tmp_path):
        assert PriorityQueueEngine.from_constants(str(tmp_path / "nope.json")).mode == MODE_IMPACT
