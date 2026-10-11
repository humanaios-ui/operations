"""
test_humanaios_core_tier1.py — Tests for humanaios_core.py (Layer 0 kernel)

Coverage by doctrine:
Roles:        the capability table is the whole authority model; no zone holds another's action
Propose:      falsifier required and substantive; pinned SHA required (IC-030); kind closed set
Ratify:       Z2 only; exactly the two ratified identities; the display name "Night" is refused;
              REJECT needs a reason; hash formula; optional ledger writes a RATIFY row
Verify:       any drift in candidate, signer, time, decision or contest_response breaks the hash
Window:       48h routine, 24h urgent; contest only after expiry or within [0, 48h] of a verified
              REJECT on this candidate; forged or other-candidate priors refused
Execute:      zone, hash, ACCEPT, CI — four refusals in order, then one EXECUTE row
Envelope:     anti-cascade rules 1, 3, 4
Callouts:     ten mandatory triggers, routes and Z2 response; unknown kinds refused
Session:      §A halts in order and on missing keys; §B.0 refuses; B.6 writes the receipt
Ledger:       append-only, hash-chained; an edited prior line fails verify()
CLI:          --smoke-test exits 0; unknown flags exit 2

Runs under plain `python3 -m unittest` (no pytest dependency) and under pytest.
"""

from __future__ import annotations

import hashlib
import io
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

from humanaios_core import (
    AUTHORITY_EFFECT,
    AUTHORIZED_Z2_IDENTITIES,
    CALLOUTS,
    HCM_TRANSLATION_FIXTURE,
    K_OPEN_MOLTS,
    Action,
    Candidate,
    Decision,
    GateRefused,
    Ledger,
    Ratification,
    Z2_DISPLAY_NAME,
    Zone,
    anti_cascade,
    callout_route,
    can,
    contest,
    execute,
    main,
    propose,
    ratification_hash,
    ratify,
    reconcile,
    session_close,
    session_open,
    verify_ratification,
    window_state,
)

T0 = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
FALSIFIER = "falsified if the smoke test exits non-zero on main"
Z2 = "carly.r.anderson@gmail.com"  # a ratified Z2 identity; "Night" is the display name, not a signer


def _cand(**over) -> Candidate:
    kw = dict(zone=Zone.Z1, candidate_id="Q-T-01", kind="Q", body="body", falsifier=FALSIFIER,
              pinned_sha="bda7c88", proposed_by="claude", now=T0)
    kw.update(over)
    return propose(**kw)


class RolesTest(unittest.TestCase):
    def test_capability_table_is_exclusive(self):
        self.assertTrue(can(Zone.Z1, Action.PROPOSE))
        self.assertTrue(can(Zone.Z2, Action.RATIFY))
        self.assertTrue(can(Zone.Z3, Action.EXECUTE))
        for zone in Zone:
            for action in Action:
                if action is Action.RATIFY:
                    self.assertEqual(can(zone, action), zone is Zone.Z2)
                if action is Action.PROPOSE:
                    self.assertEqual(can(zone, action), zone is Zone.Z1)
                if action is Action.EXECUTE:
                    self.assertEqual(can(zone, action), zone is Zone.Z3)
        # Z2 cannot contest its own decisions; Z1 and Z3 can (DISPUTED / GAUGE).
        self.assertFalse(can(Zone.Z2, Action.CONTEST))
        self.assertTrue(can(Zone.Z1, Action.CONTEST))
        self.assertTrue(can(Zone.Z3, Action.CONTEST))

    def test_model_has_no_authority_and_maps_to_hcm(self):
        self.assertEqual(AUTHORITY_EFFECT, "NONE")
        self.assertEqual(
            HCM_TRANSLATION_FIXTURE,
            {
                "propose": ("PIN_CONTEXT", "OBSERVE", "CLAIM", "CHALLENGE", "WARRANT"),
                "ratify": ("IMPORT_AUTHORITY",),
                "execute": ("RECORD_ACTION",),
                "session_close": ("RECORD_OUTCOME", "CLOSE"),
            },
        )


class ProposeTest(unittest.TestCase):
    def test_substantive_falsifier_required(self):
        for bad in ("", "   ", "TBD", "n/a", "None", "unknown"):
            with self.assertRaises(GateRefused):
                _cand(falsifier=bad)

    def test_pinned_sha_required(self):
        with self.assertRaises(GateRefused):
            _cand(pinned_sha="")
        with self.assertRaises(GateRefused):
            _cand(pinned_sha="   ")

    def test_kind_is_closed_set(self):
        for kind in ("F", "IC", "H", "MOLT", "Q"):
            self.assertEqual(_cand(kind=kind).kind, kind)
        with self.assertRaises(GateRefused):
            _cand(kind="VIBE")

    def test_only_z1_proposes(self):
        with self.assertRaises(GateRefused):
            _cand(zone=Zone.Z2)
        with self.assertRaises(GateRefused):
            _cand(zone=Zone.Z3)

    def test_candidate_is_frozen(self):
        c = _cand()
        with self.assertRaises(Exception):
            c.body = "changed"  # type: ignore[misc]


class RatifyTest(unittest.TestCase):
    def test_only_z2_ratifies(self):
        c = _cand()
        for zone in (Zone.Z1, Zone.Z3):
            with self.assertRaises(GateRefused):
                ratify(zone, c, Z2, T0, Decision.ACCEPT)

    def test_identity_must_be_authorized(self):
        c = _cand()
        for who in ("carly.r.anderson@gmail.com", "aioshuman@gmail.com"):
            r = ratify(Zone.Z2, c, who, T0, Decision.ACCEPT)
            self.assertTrue(verify_ratification(c, r))
        # The display name is a label, not a signature (z2_ratification_gate.yml allowlists only the emails).
        self.assertEqual(Z2_DISPLAY_NAME, "Night")
        for who in (Z2_DISPLAY_NAME, "night", "claude", "Carly.R.Anderson@gmail.com"):
            with self.assertRaises(GateRefused):
                ratify(Zone.Z2, c, who, T0, Decision.ACCEPT)
        self.assertEqual(AUTHORIZED_Z2_IDENTITIES, frozenset({"carly.r.anderson@gmail.com", "aioshuman@gmail.com"}))
        self.assertNotIn(Z2_DISPLAY_NAME, AUTHORIZED_Z2_IDENTITIES)

    def test_hand_built_ratification_by_display_name_never_verifies(self):
        c = _cand()
        digest = ratification_hash(c, Z2_DISPLAY_NAME, T0, Decision.ACCEPT)
        self.assertFalse(verify_ratification(c, Ratification(c.candidate_id, Z2_DISPLAY_NAME, T0, Decision.ACCEPT, digest)))

    def test_ledger_rows_on_success_only(self):
        ledger = Ledger()
        c = _cand(ledger=ledger)
        self.assertEqual([e.kind for e in ledger.events()], ["PROPOSE"])
        self.assertEqual(ledger.events("PROPOSE")[0].payload["candidate_id"], c.candidate_id)
        with self.assertRaises(GateRefused):
            _cand(falsifier="TBD", ledger=ledger)
        with self.assertRaises(GateRefused):
            ratify(Zone.Z2, c, Z2_DISPLAY_NAME, T0, Decision.ACCEPT, ledger=ledger)
        self.assertEqual(len(ledger), 1, "refusals write nothing")
        r = ratify(Zone.Z2, c, Z2, T0, Decision.EDIT, ledger=ledger)
        row = ledger.events("RATIFY")[0]
        self.assertEqual(row.by, Z2)
        self.assertEqual(row.payload, {"candidate_id": c.candidate_id, "decision": "EDIT", "hash": r.hash, "contested": False})
        self.assertTrue(ledger.verify())

    def test_reject_requires_reason(self):
        c = _cand()
        with self.assertRaises(GateRefused):
            ratify(Zone.Z2, c, Z2, T0, Decision.REJECT)
        r = ratify(Zone.Z2, c, Z2, T0, Decision.REJECT, reason="falsifier too broad")
        self.assertEqual(r.reason, "falsifier too broad")

    def test_hash_formula_matches_claude_md(self):
        c = _cand()
        r = ratify(Zone.Z2, c, Z2, T0, Decision.EDIT)
        expected = hashlib.sha256(
            f"{c.canonical()} | by={Z2} | at={T0.isoformat()} | decision=EDIT".encode()
        ).hexdigest()
        self.assertEqual(r.hash, expected)
        with_contest = ratification_hash(c, Z2, T0, Decision.ACCEPT, "re-read")
        expected2 = hashlib.sha256(
            f"{c.canonical()} | by={Z2} | at={T0.isoformat()} | decision=ACCEPT | contest_response=re-read".encode()
        ).hexdigest()
        self.assertEqual(with_contest, expected2)
        self.assertEqual(len(r.hash), 64)
        int(r.hash, 16)  # valid hex, the same check ci_gates.Z2HashGate applies


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.c = _cand()
        self.r = ratify(Zone.Z2, self.c, Z2, T0, Decision.ACCEPT)

    def test_clean_verifies(self):
        self.assertTrue(verify_ratification(self.c, self.r))

    def test_every_field_is_covered(self):
        c = self.c
        variants = [
            Candidate(c.candidate_id, c.kind, c.body + "!", c.falsifier, c.pinned_sha, c.proposed_by, c.proposed_at),
            Candidate(c.candidate_id, c.kind, c.body, c.falsifier + "!", c.pinned_sha, c.proposed_by, c.proposed_at),
            Candidate(c.candidate_id, c.kind, c.body, c.falsifier, "other-sha", c.proposed_by, c.proposed_at),
            Candidate(c.candidate_id, "H", c.body, c.falsifier, c.pinned_sha, c.proposed_by, c.proposed_at),
            Candidate("Q-OTHER", c.kind, c.body, c.falsifier, c.pinned_sha, c.proposed_by, c.proposed_at),
        ]
        for v in variants:
            self.assertFalse(verify_ratification(v, self.r))
        r = self.r
        self.assertFalse(verify_ratification(c, Ratification(r.candidate_id, r.by, r.at + timedelta(seconds=1), r.decision, r.hash)))
        self.assertFalse(verify_ratification(c, Ratification(r.candidate_id, r.by, r.at, Decision.EDIT, r.hash)))
        self.assertFalse(verify_ratification(c, Ratification(r.candidate_id, r.by, r.at, r.decision, r.hash, "x")))
        self.assertFalse(verify_ratification(c, Ratification(r.candidate_id, "claude", r.at, r.decision, r.hash)))
        self.assertFalse(verify_ratification(c, Ratification(r.candidate_id, r.by, r.at, r.decision, "0" * 64)))


class WindowAndContestTest(unittest.TestCase):
    def test_window_states(self):
        c = _cand()
        self.assertEqual(window_state(c, T0, decided=False), "OPEN")
        self.assertEqual(window_state(c, T0 + timedelta(hours=48), decided=False), "OPEN")
        self.assertEqual(window_state(c, T0 + timedelta(hours=48, seconds=1), decided=False), "EXPIRED")
        self.assertEqual(window_state(c, T0 + timedelta(hours=24, seconds=1), decided=False, urgent=True), "EXPIRED")
        self.assertEqual(window_state(c, T0 + timedelta(days=30), decided=True), "DECIDED")

    def test_contest_without_decision_needs_expiry(self):
        c = _cand()
        with self.assertRaises(GateRefused):
            contest(Zone.Z1, c, None, T0 + timedelta(hours=10), "impatient")
        self.assertIn("no decision inside window", contest(Zone.Z1, c, None, T0 + timedelta(hours=49), "GAP"))

    def test_contest_of_reject_inside_48h_only(self):
        c = _cand()
        rej = ratify(Zone.Z2, c, Z2, T0 + timedelta(hours=1), Decision.REJECT, reason="no")
        self.assertIn("contested", contest(Zone.Z1, c, rej, rej.at + timedelta(hours=47), "please re-read"))
        with self.assertRaises(GateRefused):
            contest(Zone.Z1, c, rej, rej.at + timedelta(hours=49), "late")
        with self.assertRaises(GateRefused):
            contest(Zone.Z1, c, rej, rej.at, "")  # no reason
        self.assertIn("contested", contest(Zone.Z1, c, rej, rej.at, "at the instant of the REJECT"))  # elapsed 0 is in [0, 48h]
        with self.assertRaisesRegex(GateRefused, "dated before"):
            contest(Zone.Z1, c, rej, rej.at - timedelta(seconds=1), "pre-dated")

    def test_contest_requires_a_verified_prior_on_this_candidate(self):
        c = _cand()
        other = _cand(candidate_id="Q-T-02")
        rej = ratify(Zone.Z2, c, Z2, T0, Decision.REJECT, reason="no")
        with self.assertRaisesRegex(GateRefused, "does not verify"):
            contest(Zone.Z1, other, rej, T0 + timedelta(hours=1), "a REJECT signed for a different candidate")
        forged = Ratification(c.candidate_id, Z2, T0, Decision.REJECT, "0" * 64, None, "forged")
        with self.assertRaisesRegex(GateRefused, "does not verify"):
            contest(Zone.Z1, c, forged, T0 + timedelta(hours=1), "a REJECT whose hash is invented")
        unsigned = Ratification(c.candidate_id, Z2_DISPLAY_NAME, T0, Decision.REJECT,
                                ratification_hash(c, Z2_DISPLAY_NAME, T0, Decision.REJECT), None, "x")
        with self.assertRaisesRegex(GateRefused, "does not verify"):
            contest(Zone.Z1, c, unsigned, T0 + timedelta(hours=1), "a REJECT by the display name")

    def test_only_reject_is_contestable_and_z2_cannot_contest(self):
        c = _cand()
        for d in (Decision.ACCEPT, Decision.EDIT):
            r = ratify(Zone.Z2, c, Z2, T0, d)
            with self.assertRaises(GateRefused):
                contest(Zone.Z1, c, r, T0, "why")
        rej = ratify(Zone.Z2, c, Z2, T0, Decision.REJECT, reason="no")
        with self.assertRaises(GateRefused):
            contest(Zone.Z2, c, rej, T0, "self-contest")

    def test_public_time_boundaries_reject_naive_datetimes(self):
        naive = datetime(2026, 10, 11, 12, 0)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            _cand(now=naive)
        c = _cand()
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            Candidate(c.candidate_id, c.kind, c.body, c.falsifier, c.pinned_sha, c.proposed_by, naive)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            ratification_hash(c, Z2, naive, Decision.ACCEPT)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            ratify(Zone.Z2, c, Z2, naive, Decision.ACCEPT)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            Ratification(c.candidate_id, Z2, naive, Decision.ACCEPT, "0" * 64)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            window_state(c, naive, decided=False)
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            contest(Zone.Z1, c, None, naive, "time check")

    def test_re_read_is_a_new_event_not_a_rewrite(self):
        c = _cand()
        rej = ratify(Zone.Z2, c, Z2, T0, Decision.REJECT, reason="no")
        acc = ratify(Zone.Z2, c, Z2, T0 + timedelta(hours=5), Decision.ACCEPT, contest_response="re-read")
        self.assertNotEqual(rej.hash, acc.hash)
        self.assertTrue(verify_ratification(c, rej))
        self.assertTrue(verify_ratification(c, acc))
        self.assertEqual(acc.contest_response, "re-read")


class ExecuteTest(unittest.TestCase):
    def setUp(self):
        self.c = _cand()
        self.acc = ratify(Zone.Z2, self.c, Z2, T0, Decision.ACCEPT)
        self.ledger = Ledger()

    def test_four_refusals_in_order(self):
        with self.assertRaisesRegex(GateRefused, "cannot EXECUTE"):
            execute(Zone.Z1, self.c, self.acc, True, "x", T0, self.ledger)
        with self.assertRaisesRegex(GateRefused, "no Z2 hash"):
            execute(Zone.Z3, self.c, None, True, "x", T0, self.ledger)
        forged = Ratification(self.c.candidate_id, "Night", T0, Decision.ACCEPT, "f" * 64)
        with self.assertRaisesRegex(GateRefused, "does not verify"):
            execute(Zone.Z3, self.c, forged, True, "x", T0, self.ledger)
        edit = ratify(Zone.Z2, self.c, Z2, T0, Decision.EDIT)
        with self.assertRaisesRegex(GateRefused, "not ACCEPT"):
            execute(Zone.Z3, self.c, edit, True, "x", T0, self.ledger)
        with self.assertRaisesRegex(GateRefused, "not green"):
            execute(Zone.Z3, self.c, self.acc, False, "x", T0, self.ledger)
        self.assertEqual(len(self.ledger), 0, "no refusal writes a row")

    def test_clean_execute_writes_one_row(self):
        ev = execute(Zone.Z3, self.c, self.acc, True, "z3-ops", T0, self.ledger)
        self.assertEqual(ev.kind, "EXECUTE")
        self.assertEqual(ev.by, "z3-ops")
        self.assertEqual(ev.payload["z2_hash"], self.acc.hash)
        self.assertEqual(ev.payload["pinned_sha"], "bda7c88")
        self.assertEqual(len(self.ledger), 1)
        self.assertTrue(self.ledger.verify())

    def test_execute_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            execute(Zone.Z3, self.c, self.acc, True, "z3-ops", datetime(2026, 10, 11, 12, 0), self.ledger)


class EnvelopeTest(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(anti_cascade("c", {}, {}), [])
        self.assertEqual(len(anti_cascade("c", {"c": "M"}, {})), 1)
        full = {f"c{i}": f"M{i}" for i in range(K_OPEN_MOLTS)}
        self.assertTrue(any("rule 3" in r for r in anti_cascade("new", full, {})))
        self.assertTrue(any("rule 4" in r for r in anti_cascade("c", {}, {"c": 2})))
        self.assertTrue(any("rule 4" in r for r in anti_cascade("c", {}, {"c": 5})))
        self.assertEqual(anti_cascade("c", {}, {"c": 1}), [])
        # all three at once
        self.assertEqual(len(anti_cascade("c0", full, {"c0": 2})), 3)


class CalloutTest(unittest.TestCase):
    def test_ten_callouts_and_routes(self):
        self.assertEqual(len(CALLOUTS), 10)
        self.assertEqual(callout_route("MOLT"), (("Z2",), "Ratify, edit, or reject"))
        self.assertEqual(callout_route("DISPUTED")[0], ("Z2", "FS"))
        with self.assertRaises(GateRefused):
            callout_route("receipt-gap")  # names are literal


class SessionTest(unittest.TestCase):
    FULL = {
        "pinned_sha": "abc", "registered_read_at_sha": "abc", "queue_read": True,
        "zone_registry_ok": True, "manifest_ok": True,
        "position": "p", "destination": "d", "probability": 0.5,
    }

    def test_open_halts_in_order(self):
        halts = session_open({})
        self.assertEqual([h[:3] for h in halts], ["A.1", "A.2", "A.3", "A.4", "A.5", "A.6"])
        self.assertEqual(session_open(self.FULL), [])

    def test_open_each_key(self):
        for key, tag in (("queue_read", "A.3"), ("zone_registry_ok", "A.4"), ("manifest_ok", "A.5")):
            halts = session_open({**self.FULL, key: False})
            self.assertEqual(len(halts), 1)
            self.assertTrue(halts[0].startswith(tag))
        self.assertTrue(session_open({**self.FULL, "registered_read_at_sha": "other"})[0].startswith("A.2"))
        for p in (None, -0.1, 1.5, "high", True, False):  # bool is an int subclass; a flag is not a calibration
            halts = session_open({**self.FULL, "probability": p})
            self.assertEqual(len(halts), 1, f"probability={p!r}")
            self.assertTrue(halts[0].startswith("A.6"))
        for p in (0, 1, 0.5):
            self.assertEqual(session_open({**self.FULL, "probability": p}), [])

    def test_close_b0_refuses(self):
        ledger = Ledger()
        with self.assertRaisesRegex(GateRefused, "B.0"):
            session_close({}, ledger, T0, "claude")
        with self.assertRaisesRegex(GateRefused, "prereg"):
            session_close({"code_ran": True}, ledger, T0, "claude")
        with self.assertRaisesRegex(GateRefused, "HANDOFF"):
            session_close({"code_ran": True, "prereg_verified": True}, ledger, T0, "claude")
        self.assertEqual(len(ledger), 0)

    def test_close_reconciles_and_routes_gaps(self):
        ledger = Ledger()
        state = {"code_ran": True, "prereg_verified": True, "handoff_written": True,
                 "claims": ["a.py", "b.md", "shipped it"], "tree": ["a.py", "b.md", "c.py"]}
        receipt = session_close(state, ledger, T0, "claude")
        self.assertEqual(receipt.matched, ("a.py", "b.md"))
        self.assertEqual(receipt.gaps, ("shipped it",))
        self.assertFalse(receipt.clean)
        kinds = [e.kind for e in ledger.events()]
        self.assertEqual(kinds, ["RECEIPT", "CALLOUT"])
        self.assertEqual(ledger.events("CALLOUT")[0].payload["routes"], ["Q", "FS"])

    def test_clean_close_writes_no_callout(self):
        ledger = Ledger()
        state = {"code_ran": True, "prereg_verified": True, "handoff_written": True,
                 "claims": ["a.py"], "tree": ["a.py"]}
        self.assertTrue(session_close(state, ledger, T0, "claude").clean)
        self.assertEqual([e.kind for e in ledger.events()], ["RECEIPT"])

    def test_reconcile_is_exact_match(self):
        self.assertEqual(reconcile([], []).matched, ())
        self.assertTrue(reconcile([], ["x"]).clean)  # the tree may hold more than was claimed
        self.assertEqual(reconcile(["x", "y"], ["x"]).gaps, ("y",))

    def test_close_rejects_naive_timestamp(self):
        state = {"code_ran": True, "prereg_verified": True, "handoff_written": True}
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            session_close(state, Ledger(), datetime(2026, 10, 11, 12, 0), "claude")


class LedgerTest(unittest.TestCase):
    def test_chain_and_tamper(self):
        ledger = Ledger()
        a = ledger.append("PROPOSE", T0, "claude", {"id": 1})
        b = ledger.append("RATIFY", T0, "Night", {"id": 1})
        self.assertEqual(a.prev_hash, Ledger.GENESIS)
        self.assertEqual(b.prev_hash, a.hash)
        self.assertTrue(ledger.verify())
        ledger._events[0] = type(a)(a.kind, a.at, a.by, {"id": 2}, a.prev_hash, a.hash)
        self.assertFalse(ledger.verify())

    def test_filter_by_kind(self):
        ledger = Ledger()
        ledger.append("PROPOSE", T0, "claude", {})
        ledger.append("CALLOUT", T0, "claude", {})
        self.assertEqual(len(ledger.events("CALLOUT")), 1)
        self.assertEqual(len(ledger.events()), 2)

    def test_append_normalizes_and_detaches_nested_payload(self):
        ledger = Ledger()
        payload = {"routes": ["Q", "FS"], "nested": {"items": [1, 2]}}
        event = ledger.append("CALLOUT", T0, "claude", payload)
        payload["routes"].append("Z2")
        payload["nested"]["items"].append(3)
        self.assertEqual(event.payload, {"routes": ["Q", "FS"], "nested": {"items": [1, 2]}})
        self.assertTrue(ledger.verify())

    def test_event_boundary_rejects_naive_datetime(self):
        with self.assertRaisesRegex(GateRefused, "timezone-aware"):
            Ledger().append("PROPOSE", datetime(2026, 10, 11, 12, 0), "claude", {})


class CliTest(unittest.TestCase):
    def test_smoke_test_exit_zero(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["--smoke-test"]), 0)
        self.assertIn("checks OK", out.getvalue())

    def test_unknown_flag_exit_two(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--nope"]), 2)
            self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
