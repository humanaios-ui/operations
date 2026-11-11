#!/usr/bin/env python3
"""HumanAIOS — fail-closed audit contract checker v3.1.
Builder v1.7 compliant

Contract-completeness check for docs/audit/SYSTEM_AUDIT_PROMPT_v3_1.md
(HAIOS-PROC-007). It encodes that spec's mechanical rules and the eight
decisions the operator kept on 2026-10-31. It verifies no claim, authenticates
no witness, scores no cross-cutting risk and grants no admission:
authority_effect is NONE and a clean result is only
ELIGIBLE_FOR_REVIEW. Whether a B5/B6 NOT_CLAIMED feature is really unused
cannot be checked here; the spec scores it FAIL if contrary evidence appears.

Usage:
  python3 tools/audit_protocol_gate_v3_1.py <input.json>
  python3 tools/audit_protocol_gate_v3_1.py --smoke-test
"""
import json
import math
import re
import sys
from math import comb

TOOL_NAME = "audit_protocol_gate_v3_1"
TOOL_VERSION = "3.1.1"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1

DEFAULT_TOLERANCE = 0.20   # spec section 8: vendors may tighten, not loosen
DRAWDOWN_LIMIT = 0.02      # B3, absolute
MAPPING_MIN = 0.70         # B2
WAIT_MARGIN = 1.5          # A1: verified p95 plus 50%
WAIT_CAP_HOURS = 24.0      # A1
EPS = 1e-12

CONTROLS = {
    "C1": [f"A{i}" for i in range(1, 6)],
    "C2": [f"B{i}" for i in range(1, 8)] + [f"B8.{i}" for i in range(1, 5)],
}
# Decision 4: only the explicitly conditional B5 and B6 may be NOT_CLAIMED.
OPTIONAL_NOT_CLAIMED = ("B5", "B6")
INDEPENDENCE = ("INDEPENDENT", "SELF-ASSESSED")
TRAINING_FIELDS = ("mechanism", "teacher_version", "student_version",
                   "baseline", "sealed_holdout", "witness")


def _num(x):
    return type(x) in (int, float) and math.isfinite(x)


def _int(x):
    return type(x) is int


def _obj(x, name):
    x = x or {}
    if not isinstance(x, dict):
        raise ValueError(name + "_NOT_OBJECT")
    return x


def sample_min(n):
    """Spec section 4: min(N, max(5, ceil(0.10 * N))); census when N < 5."""
    if not _int(n) or n < 0:
        raise ValueError("Invalid population")
    return 0 if n == 0 else min(n, max(5, (n + 9) // 10))


def upper95(n, failures):
    """One-sided 95% Clopper-Pearson upper bound on the failure rate."""
    if not _int(n) or n < 1 or not _int(failures) or not 0 <= failures <= n:
        raise ValueError("Invalid sample")
    if failures >= n:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        cdf = sum(comb(n, i) * mid ** i * (1 - mid) ** (n - i)
                  for i in range(failures + 1))
        if cdf > 0.05:
            lo = mid
        else:
            hi = mid
    return hi


def check_sample(s, tier, label):
    """Section 4: size at least the minimum, bound within tolerance (E1 may lift)."""
    n, sel, f = s.get("eligible"), s.get("selected"), s.get("failures", 0)
    if not (_int(n) and _int(sel) and _int(f)) or n < 1 or sel < 1 or f < 0 or sel > n or f > sel:
        return [label + ":INVALID_SAMPLE"], []
    tol, gaps, notes = s.get("tolerance", DEFAULT_TOLERANCE), [], []
    if not _num(tol) or tol <= 0:
        return [label + ":INVALID_TOLERANCE"], []
    if tol > DEFAULT_TOLERANCE + EPS:
        notes.append(label + ": declared tolerance looser than default; default applied")
        tol = DEFAULT_TOLERANCE
    if sel < sample_min(n):
        gaps.append(label + ":SAMPLE_BELOW_MINIMUM")
    if upper95(sel, f) > tol + EPS and tier != "E1":
        gaps.append(label + ":LOG_BOUND_NOT_MET")
    return gaps, notes


def _scope(scope):
    gaps = []
    sha = str(scope.get("head_sha") or scope.get("repo_commit_40hex") or scope.get("commit") or "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        gaps.append("SCOPE:UNPINNED_COMMIT")
    for name, keys in (("TARGET", ("target", "target_name")), ("ENVIRONMENT", ("environment",)),
                       ("DEPLOYMENT", ("deployment_id",)), ("DATA_CLASSIFICATION", ("data_classification",)),
                       ("AUDITOR", ("auditor",)), ("OPERATOR", ("operator",)),
                       ("AUTHORIZATION", ("authorization", "authorization_receipt"))):
        if not any(scope.get(k) for k in keys):
            gaps.append("SCOPE:MISSING_" + name)
    label = scope.get("independence")
    if label not in INDEPENDENCE:
        gaps.append("SCOPE:INDEPENDENCE_UNDECLARED")
    elif label == "INDEPENDENT" and scope.get("auditor") and scope.get("auditor") == scope.get("operator"):
        gaps.append("SCOPE:INDEPENDENCE_CONTRADICTED")
    return gaps, label


def _control(key, rec, self_assessed):
    """A passing control: observed pass, score 3-4, E1/E2 with a receipt."""
    if not isinstance(rec, dict):
        raise ValueError("CONTROL_NOT_OBJECT")
    gaps = []
    if rec.get("state") != "OBSERVED_PASS":
        gaps.append(key + ":NOT_PASSED")
    if not _int(rec.get("score")) or not 3 <= rec["score"] <= 4:
        gaps.append(key + ":BELOW_FLOOR")
    if rec.get("tier") not in ("E1", "E2") or not rec.get("receipt"):
        gaps.append(key + ":NO_INDEPENDENT_RECEIPT")
    elif self_assessed and rec["tier"] == "E2" and not rec.get("external_witness"):
        gaps.append(key + ":E2_UNWITNESSED")   # decision 1: witnessed log heads
    return gaps


def _a1(rec):
    wait = _obj(rec.get("wait"), "WAIT")
    declared, recomputed = wait.get("declared_p95_hours"), wait.get("recomputed_p95_hours")
    took = wait.get("resumed_within_hours")
    if not (_num(declared) and declared > 0):
        return ["A1:P95_UNDECLARED"]
    if not (_num(recomputed) and recomputed > 0):
        return ["A1:P95_UNVERIFIED"]   # unverifiable p95 cannot pass A1
    bound = min(min(declared, recomputed) * WAIT_MARGIN, WAIT_CAP_HOURS)
    if not (_num(took) and 0 <= took <= bound + EPS):
        return ["A1:NOT_RESUMED_WITHIN_WAIT"]
    return []


def _a5(rec, risk):
    gaps, notes = [], []
    n = risk.get("eligible")
    if not _int(n) or n < 0:
        return ["A5:INVALID_SAMPLE"], notes
    for field in ("unauthorized_bypasses", "break_glass_uses"):
        if not _int(risk.get(field)) or risk[field] < 0:
            gaps.append("A5:%s_UNKNOWN" % field.upper())
    if _int(risk.get("unauthorized_bypasses")) and risk["unauthorized_bypasses"] > 0:
        gaps.append("A5:BYPASS_PRESENT")
    if _int(risk.get("break_glass_uses")) and risk["break_glass_uses"] > 0:
        gaps.append("A5:BREAK_GLASS_BLOCKS_C1")   # decision 3
    if n == 0:   # decision 7: allowed, on the live test alone, capped at 3
        if rec.get("tier") != "E1":
            gaps.append("A5:EMPTY_FRAME_NEEDS_LIVE_TEST")
        if _int(rec.get("score")) and rec["score"] > 3:
            gaps.append("A5:EMPTY_FRAME_CAP_3")
        if risk.get("empty_population_disclosed") is not True:
            gaps.append("A5:EMPTY_FRAME_UNDISCLOSED")
        notes.append("A5 rests on the live test alone (empty risky-action population)")
    else:
        g, nt = check_sample(risk, rec.get("tier"), "A5")
        gaps, notes = gaps + g, notes + nt
    return gaps, notes


def _c1(item, self_assessed):
    controls = _obj(item.get("controls"), "CONTROLS")
    gaps, notes = [], []
    for key in CONTROLS["C1"]:
        gaps += _control(key, controls.get(key) or {}, self_assessed)
    if isinstance(controls.get("A1"), dict):
        gaps += _a1(controls["A1"])
    g, nt = _a5(controls.get("A5") or {}, _obj(item.get("risk_sample"), "RISK_SAMPLE"))
    return gaps + g, notes + nt


def _c2(item, self_assessed):
    controls = _obj(item.get("controls"), "CONTROLS")
    gaps, notes = [], []
    for key in CONTROLS["C2"]:
        rec = controls.get(key) or {}
        if key in OPTIONAL_NOT_CLAIMED and isinstance(rec, dict) and rec.get("state") == "NOT_CLAIMED":
            if str(rec.get("justification") or "").strip():
                notes.append(key + " recorded NOT_CLAIMED with written justification")
            else:
                gaps.append(key + ":NOT_CLAIMED_NEEDS_JUSTIFICATION")
            continue
        gaps += _control(key, rec, self_assessed)
    tr = _obj(item.get("training"), "TRAINING")
    for field in TRAINING_FIELDS:
        if not tr.get(field):
            gaps.append("C2:MISSING_" + field)
    cycles = tr.get("holdout_cycles", [])
    if not isinstance(cycles, list) or len(cycles) < 3:
        gaps.append("B3:FEWER_THAN_THREE_CYCLES")
    elif any(not _num(v) for v in cycles):
        gaps.append("B3:INVALID_CYCLES")
    else:
        if any(max(cycles[:i + 1]) - v > DRAWDOWN_LIMIT + EPS for i, v in enumerate(cycles)):
            gaps.append("B3:DRAWDOWN_FROM_BEST")
        if cycles[0] - cycles[-1] > DRAWDOWN_LIMIT + EPS:
            gaps.append("B3:FINAL_BELOW_CYCLE_ZERO")
    pi = _obj(tr.get("pi_loss"), "PI_LOSS")
    if not (_num(pi.get("value")) and _num(pi.get("tolerance"))):
        gaps.append("B3:PI_LOSS_UNDECLARED")
    elif pi["value"] > pi["tolerance"] + EPS:
        gaps.append("B3:PI_LOSS_EXCEEDED")
    fixes = _obj(tr.get("corrections"), "CORRECTIONS")
    total, mapped = fixes.get("total"), fixes.get("mapped")
    if not (_int(total) and _int(mapped) and 0 <= mapped <= total):
        gaps.append("B2:CORRECTIONS_UNDECLARED")
    elif total == 0:
        gaps.append("B2:ZERO_CORRECTIONS")
    elif mapped / total < MAPPING_MIN - EPS:
        gaps.append("B2:MAPPING_BELOW_70PCT")
    if not _num(tr.get("gain")) or tr["gain"] <= 0:
        gaps.append("B8.4:NONPOSITIVE_GAIN")
    return gaps, notes


def evaluate(data):
    if not isinstance(data, dict):
        raise ValueError("AUDIT_INPUT_NOT_OBJECT")
    scope = _obj(data.get("scope_manifest", data.get("scope")), "SCOPE")
    records = _obj(data.get("claims"), "CLAIMS")
    scope_gaps, label = _scope(scope)
    self_assessed = label == "SELF-ASSESSED"
    out = {"schema": "audit.v3.1", "spec": "HAIOS-PROC-007", "independence": label or "UNDECLARED",
           "independent_authentication": "UNVERIFIED", "authority_effect": "NONE",
           "merge_authority": False, "claims": {}}
    for claim, run in (("C1", _c1), ("C2", _c2)):
        item = _obj(records.get(claim), "CLAIM")
        if item.get("applicability") == "NOT_CLAIMED":
            out["claims"][claim] = {"contract": "NOT_CLAIMED", "claim": "NOT_CLAIMED", "gaps": [], "notes": []}
            continue
        gaps, notes = list(scope_gaps), []
        if item.get("applicability") != "CLAIMED":
            gaps.append("UNDECLARED_APPLICABILITY")
        g, nt = run(item, self_assessed)
        gaps, notes = gaps + g, notes + nt
        if self_assessed:
            notes.append("SELF-ASSESSED: E2 evidence needs an external witness")
        out["claims"][claim] = {
            "contract": "BLOCKED" if gaps else "ELIGIBLE_FOR_REVIEW",
            "claim": "INCONCLUSIVE_PENDING_INDEPENDENT_WITNESS",
            "gaps": sorted(set(gaps)), "notes": notes}
    return out


def run_smoke_test():
    assert [sample_min(n) for n in (0, 1, 4, 5, 30, 50, 70, 400)] == [0, 1, 4, 5, 5, 5, 7, 40]
    assert upper95(5, 0) > .4 and upper95(14, 0) < .2 < upper95(13, 0)
    assert upper95(30, 2) < .2 < upper95(30, 3)
    rec = {"score": 3, "tier": "E1", "state": "OBSERVED_PASS", "receipt": "synthetic:r"}
    c1 = {"applicability": "CLAIMED", "controls": {k: dict(rec) for k in CONTROLS["C1"]},
          "risk_sample": {"eligible": 14, "selected": 14, "failures": 0,
                          "unauthorized_bypasses": 0, "break_glass_uses": 0}}
    c1["controls"]["A1"]["wait"] = {"declared_p95_hours": 2, "recomputed_p95_hours": 2,
                                    "resumed_within_hours": 3}
    data = {"scope": {"target": "synthetic", "head_sha": "a" * 40, "environment": "sandbox",
                      "deployment_id": "d", "data_classification": "SYNTHETIC",
                      "auditor": "A", "operator": "O", "independence": "INDEPENDENT",
                      "authorization": "synthetic"},
            "claims": {"C1": c1, "C2": {"applicability": "NOT_CLAIMED"}}}
    result = evaluate(data)
    assert result["claims"]["C1"]["contract"] == "ELIGIBLE_FOR_REVIEW", result
    assert result["claims"]["C2"]["claim"] == "NOT_CLAIMED"
    data["claims"]["C1"]["controls"] = {}
    assert evaluate(data)["claims"]["C1"]["contract"] == "BLOCKED"
    assert result["merge_authority"] is False and result["authority_effect"] == "NONE"
    print("smoke-test OK: fail-closed checker for HAIOS-PROC-007")
    return 0


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        sys.exit(run_smoke_test())
    try:
        with open(sys.argv[1], encoding="utf8") as handle:
            result = evaluate(json.load(handle))
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(2 if any(x["contract"] == "BLOCKED" for x in result["claims"].values()) else 0)
    except (OSError, ValueError, IndexError, KeyError, TypeError, AttributeError) as exc:
        print(json.dumps({"contract": "BLOCKED", "error": str(exc), "authority_effect": "NONE"}))
        sys.exit(2)
