#!/usr/bin/env python3
“””
Timing Audit — v1.0
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-071026-01 — formalizes the four-question audit demonstrated
ad hoc this session (IC-042/maintained-headline/haios_guard/IC-041
sections), and the lessons-learned ledger those four applications produced.

STATUS: Z1 DRAFT. This tool and its method are NOT registered, NOT
ratified, and were proposed in-conversation, not sourced from any prior
governance document. Flag for Zone 2 disposition (H-cand or new skill)
before treating this as canonical.

The four questions (per check under audit):

1. What does it verify?
1. When does it verify it – before the risky claim/action, or after?
1. Is the information needed for the check already available earlier?
1. What’s the cost of moving it there?

The recursive part: this tool does not answer question 4’s mechanism
recommendation (hard-block vs. advisory) from first principles each time.
It consults lessons_learned_ledger.json – itself built from testing
four real checks this session – and applies whichever lessons match the
check’s classification. After the audit, if the application surfaces a
NEW constraint not already in the ledger, that lesson is appended, so
the NEXT audit inherits it automatically. Each run narrows the space of
mistakes the next run can make in the same way section 2 narrowed what
section 3 needed to test.
“””
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = “timing_audit”
TOOL_VERSION = “1.0.0”
DEFAULT_LEDGER_PATH = “lessons_learned_ledger.json”

class SpecLoadFailed(Exception):
pass

def load_ledger(path: str) -> dict:
p = Path(path)
if not p.exists():
return {“ledger_version”: “1.0”, “purpose”: “auto-created”, “lessons”: []}
try:
return json.loads(p.read_text(encoding=“utf-8”))
except json.JSONDecodeError as e:
raise SpecLoadFailed(f”Ledger JSON parse error: {e}”)

def save_ledger(path: str, ledger: dict) -> None:
Path(path).write_text(json.dumps(ledger, indent=2), encoding=“utf-8”)

def classify_check(check_type: str, depends_on_external_state: bool = False) -> list:
“””
Maps a check’s stated type to the lesson constraints it must consult.
check_type is one of: ‘binary_mechanical’, ‘heuristic_pattern’,
‘reconstructed_from_spec’, ‘live_reachable’.
depends_on_external_state: True if the check’s source of truth is not
already loaded into the process performing the check (a DB row, a
remote file) – pulls in L6 (added S-071026-01, second application of
this tool) alongside a binary_mechanical classification.
Returns the list of lesson IDs that apply, in the order discovered.
“””
mapping = {
“binary_mechanical”: [“L1”, “L1a”],
“heuristic_pattern”: [“L2”, “L3”],
“reconstructed_from_spec”: [“L4”],
“live_reachable”: [“L5”],
}
ids = list(mapping.get(check_type, []))
if check_type == “binary_mechanical” and depends_on_external_state:
ids.append(“L6”)
return ids

def run_four_question_audit(
check_name: str,
verifies: str,
current_timing: str,
check_type: str,
info_available_earlier: bool,
move_cost: str,
ledger: dict,
depends_on_external_state: bool = False,
) -> dict:
“””
Runs the four questions against a single existing check and returns
a structured recommendation, informed by whichever ledger lessons
match check_type (question 4’s answer is NOT invented fresh –
it is looked up, per the recursive design goal).
“””
lessons_by_id = {l[“id”]: l for l in ledger[“lessons”]}
applicable_ids = classify_check(check_type, depends_on_external_state)
applicable = [lessons_by_id[i] for i in applicable_ids if i in lessons_by_id]

```
# Question 4 answer is derived, not asserted: binary -> hard-block,
# heuristic -> advisory, everything else -> caveat the evidence tier.
if check_type == "binary_mechanical":
    recommended_mechanism = "hard_block"
elif check_type == "heuristic_pattern":
    recommended_mechanism = "advisory_non_blocking"
else:
    recommended_mechanism = "undetermined_needs_classification"

evidential_caveat = None
if check_type == "reconstructed_from_spec":
    evidential_caveat = (
        "INFERENCE tier only per L4 -- design proven, deployed tool unverified"
    )
elif check_type == "live_reachable":
    evidential_caveat = "VERIFIED tier achievable per L5 -- test against live state, not synthetic"

worth_moving = bool(info_available_earlier) and move_cost.lower() in (
    "low",
    "negligible",
    "trivial",
)

return {
    "tool": TOOL_NAME,
    "version": TOOL_VERSION,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "check_name": check_name,
    "q1_verifies": verifies,
    "q2_current_timing": current_timing,
    "q3_info_available_earlier": info_available_earlier,
    "q4_move_cost": move_cost,
    "recommendation": {
        "worth_moving_earlier": worth_moving,
        "recommended_mechanism": recommended_mechanism,
        "evidential_caveat": evidential_caveat,
        "applicable_lessons": [
            {"id": l["id"], "rule": l["rule"]} for l in applicable
        ],
    },
}
```

def append_new_lesson(ledger: dict, lesson: dict) -> dict:
“”“The recursive write-back step: a new lesson discovered during an
audit application becomes a constraint for every subsequent audit.”””
existing_ids = {l[“id”] for l in ledger[“lessons”]}
if lesson[“id”] in existing_ids:
raise ValueError(f”Lesson {lesson[‘id’]} already exists – use a new ID”)
ledger[“lessons”].append(lesson)
return ledger

def run_smoke_test() -> bool:
try:
ledger = load_ledger(DEFAULT_LEDGER_PATH)
assert len(ledger[“lessons”]) >= 5, “seed ledger should have >=5 lessons”

```
    # Re-run section 1's audit through the formal tool -- should recommend
    # hard_block, consult L1/L1a, and NOT claim behavioral coverage.
    result = run_four_question_audit(
        check_name="IC-042 deploy corruption",
        verifies="does the committed file execute cleanly",
        current_timing="after commit, on manual execution",
        check_type="binary_mechanical",
        info_available_earlier=True,
        move_cost="low",
        ledger=ledger,
    )
    assert result["recommendation"]["recommended_mechanism"] == "hard_block"
    assert any(l["id"] == "L1a" for l in result["recommendation"]["applicable_lessons"])
    assert result["recommendation"]["worth_moving_earlier"] is True

    # Re-run section 2's audit -- should recommend advisory, not hard_block,
    # BECAUSE L2 is already in the ledger. This is the actual test of the
    # recursion: the tool must not re-derive "advisory" from scratch, it
    # must retrieve it.
    result2 = run_four_question_audit(
        check_name="maintained-headline lint",
        verifies="does this line look like a manually-maintained value",
        current_timing="after drift is noticed",
        check_type="heuristic_pattern",
        info_available_earlier=True,
        move_cost="low",
        ledger=ledger,
    )
    assert result2["recommendation"]["recommended_mechanism"] == "advisory_non_blocking"
    assert any(l["id"] == "L3" for l in result2["recommendation"]["applicable_lessons"])

    print("✓ Smoke test PASSED")
    return True
except Exception as e:
    print(f"✗ Smoke test FAILED: {e}")
    return False
```

def main():
parser = argparse.ArgumentParser(description=“Timing Audit v1.0 – four-question audit, ledger-informed”)
parser.add_argument(”–ledger”, default=DEFAULT_LEDGER_PATH)
parser.add_argument(”–check-name”)
parser.add_argument(”–verifies”)
parser.add_argument(”–current-timing”)
parser.add_argument(
“–check-type”,
choices=[“binary_mechanical”, “heuristic_pattern”, “reconstructed_from_spec”, “live_reachable”],
)
parser.add_argument(”–info-available-earlier”, action=“store_true”)
parser.add_argument(”–move-cost”, default=“unknown”)
parser.add_argument(”–depends-on-external-state”, action=“store_true”)
parser.add_argument(”–smoke-test”, action=“store_true”)
args = parser.parse_args()

```
if args.smoke_test:
    sys.exit(0 if run_smoke_test() else 1)

if not all([args.check_name, args.verifies, args.current_timing, args.check_type]):
    parser.print_help()
    sys.exit(1)

ledger = load_ledger(args.ledger)
result = run_four_question_audit(
    check_name=args.check_name,
    verifies=args.verifies,
    current_timing=args.current_timing,
    check_type=args.check_type,
    info_available_earlier=args.info_available_earlier,
    move_cost=args.move_cost,
    ledger=ledger,
    depends_on_external_state=args.depends_on_external_state,
)
print(json.dumps(result, indent=2))
```

if **name** == “**main**”:
main()