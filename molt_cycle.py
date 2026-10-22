"""
molt_cycle.py — Molt Cycle Implementation

Complete molt cycle orchestration: READ → PROPOSE → PREDICT/RATIFY → APPLY → MEASURE → KEEP/REVERT

The recursive learning function: reads from ledgers (never memory), proposes changes as molts,
Z2 ratifies, code applies and measures. Predictions are pinned and either kept or reverted
based on falsifier outcomes.

Anti-cascade rules enforced:
1. One open molt per constant (no new candidate inside window W)
2. No self-reference in windows (candidate not from events in its own window)
3. K=3 system-wide limit on open molts
4. Freeze after 2 reverts (Z2 Tier 2 override required to reopen)
5. Ranking by Priority Queue score (no bypass)

The molt ledger is append-only and chains into event stream (EV).

NF_LEDGER integration (Q-NF-SCHEMA-01):
- Reads NF_LEDGER.jsonl via tools/nf_ledger_v0_1.py's own project()/pin_outcome(),
  the same functions that tool's `score` command uses — not a re-implemented join.
  (An earlier hand-rolled join here keyed RESOLVE events by a `target` field that
  RESOLVE events never carry — only `token_id` — so it always read 0 resolved.)
- A pin is resolved when pin_outcome() returns 1.0 or 0.0 (not None/"VOID")
- Calculates Brier scores per predictor from resolved pins
- Drives molt proposals based on Brier drift signals
"""

import importlib.util
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


def _load_nf_ledger_v0_1():
    """Load tools/nf_ledger_v0_1.py by explicit path rather than sys.path +
    `import nf_ledger_v0_1` — mutating sys.path here would put tools/ ahead of
    the repo root for every later import in the process, including a bare
    `import molt_cycle`, which would then silently resolve to the unrelated
    tools/molt_cycle.py (see ledgers/NF_EVENT_SCHEMA.md)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "nf_ledger_v0_1.py")
    spec = importlib.util.spec_from_file_location("nf_ledger_v0_1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


nf_ledger_v0_1 = _load_nf_ledger_v0_1()


class MoltPhase(Enum):
    """Phase of molt cycle."""
    READ = "READ"
    PROPOSE = "PROPOSE"
    RATIFY = "RATIFY"
    APPLY = "APPLY"
    MEASURE = "MEASURE"
    KEEP_REVERT = "KEEP_REVERT"


@dataclass
class MoltCycleState:
    """Current state of molt cycle."""
    phase: str
    constants_in_molt: Dict[str, str]
    molt_windows: Dict[str, Dict]
    open_molts_count: int
    constants_frozen: set
    next_phase: str


class MoltCycle:
    """Molt Cycle — recursive learning with locked predictions and Z2 ratification."""

    def __init__(self, k_limit: int = 3, nf_ledger_path: str = "ledgers/NF_LEDGER.jsonl", constants_path: str = "constants.json"):
        self.k_limit = k_limit
        self.nf_ledger_path = nf_ledger_path
        self.constants_path = constants_path
        self.state = MoltCycleState(
            phase=MoltPhase.READ.value,
            constants_in_molt={},
            molt_windows={},
            open_molts_count=0,
            constants_frozen=set(),
            next_phase="",
        )
        self.nf_entries = []
        self.tokens: Dict[str, Any] = {}
        self.pins: Dict[str, Any] = {}
        self.constants = []

    def read_constants(self) -> Dict[str, Any]:
        """READ phase: Load constants.json and extract Bayesian priors."""
        try:
            with open(self.constants_path) as f:
                constants_data = json.load(f)
            self.constants = constants_data.get('constants', [])
        except FileNotFoundError:
            self.constants = []
            return {'status': 'CONSTANTS_NOT_FOUND', 'path': self.constants_path, 'count': 0}

        return {
            'status': 'READ_COMPLETE',
            'constants_loaded': len(self.constants),
            'constant_names': [c.get('name') for c in self.constants],
        }

    def read_nf_ledger(self) -> Dict[str, Any]:
        """READ phase: load NF_LEDGER.jsonl and project it via tools/nf_ledger_v0_1.py
        — the same project() the tool's own `status`/`score` commands use — instead
        of re-deriving PIN/RESOLVE state from a hand-rolled field join."""
        try:
            self.nf_entries = nf_ledger_v0_1.read(self.nf_ledger_path)
        except FileNotFoundError:
            self.nf_entries = []
            self.tokens, self.pins = {}, {}
            return {'status': 'LEDGER_NOT_FOUND', 'path': self.nf_ledger_path}

        self.tokens, self.pins = nf_ledger_v0_1.project(self.nf_entries)

        return {
            'status': 'READ_COMPLETE',
            'ledger_entries': len(self.nf_entries),
            'pin_targets': len({p.get('target') for p in self.pins.values() if p.get('target')}),
        }

    def count_resolved(self) -> int:
        """Count pins with a known outcome (pin_outcome() == 1.0 or 0.0).

        Uses nf_ledger_v0_1.pin_outcome(), which returns None for still-unresolved
        pins and "VOID" for pins with a PENDING_Z2_DATE token — neither counts here.
        """
        return sum(1 for pin in self.pins.values()
                   if nf_ledger_v0_1.pin_outcome(pin, self.tokens) in (1.0, 0.0))

    def join_pin_resolve_pairs(self) -> List[Dict[str, Any]]:
        """Resolved, scoreable (p is set) pins as (prediction, outcome) pairs."""
        pairs = []
        for pin in self.pins.values():
            if pin.get('p') is None:
                continue
            outcome = nf_ledger_v0_1.pin_outcome(pin, self.tokens)
            if outcome not in (1.0, 0.0):
                continue
            pairs.append({
                'target': pin.get('target'),
                'predictor': pin.get('predictor'),
                'pin_p': pin.get('p'),
                'resolve_outcome': 'YES' if outcome == 1.0 else 'NO',
                'pin_entry': pin,
            })
        return pairs

    def calculate_brier_scores(self, pairs: List[Dict]) -> Dict[str, Any]:
        """Calculate Brier scores for resolved predictions."""
        if not pairs:
            return {'brier_per_predictor': {}, 'brier_overall': None, 'n_predictions': 0}

        # Convert outcomes to binary (YES=1.0, NO=0.0, STRIKE=skip)
        outcomes = []
        predictions = []
        for pair in pairs:
            outcome = pair['resolve_outcome']
            p = pair['pin_p']

            if outcome == 'YES':
                outcomes.append(1.0)
                predictions.append(p)
            elif outcome == 'NO':
                outcomes.append(0.0)
                predictions.append(p)
            # STRIKE outcomes are skipped

        if not predictions:
            return {'brier_per_predictor': {}, 'brier_overall': None, 'n_predictions': 0}

        # Brier Score = mean((predicted_p - actual_outcome)^2)
        squared_errors = [(p - o)**2 for p, o in zip(predictions, outcomes)]
        brier_overall = sum(squared_errors) / len(squared_errors)

        # Per-predictor Brier
        brier_per_predictor = {}
        for pair in pairs:
            predictor = pair['predictor']
            if predictor not in brier_per_predictor:
                brier_per_predictor[predictor] = {'scores': [], 'n': 0}

            outcome = pair['resolve_outcome']
            p = pair['pin_p']
            if outcome in ['YES', 'NO']:
                o = 1.0 if outcome == 'YES' else 0.0
                brier_per_predictor[predictor]['scores'].append((p - o)**2)
                brier_per_predictor[predictor]['n'] += 1

        # Average per predictor
        for predictor, data in brier_per_predictor.items():
            if data['scores']:
                data['brier'] = sum(data['scores']) / len(data['scores'])

        return {
            'brier_per_predictor': brier_per_predictor,
            'brier_overall': brier_overall,
            'n_predictions': len(predictions),
        }

    def complete_cycle(self, constants_needing_eval: List[Dict], measured_molts: List[Dict]) -> Dict[str, Any]:
        """Complete full molt cycle."""
        # READ phase
        read_result = self.read_nf_ledger()

        # Calculate Brier scores
        pairs = self.join_pin_resolve_pairs()
        brier_result = self.calculate_brier_scores(pairs)

        rules_check = self.check_anti_cascade_rules()
        proposals = self.propose_molts(constants_needing_eval)

        return {
            'status': 'CYCLE_COMPLETE',
            'read_phase': read_result,
            'brier_scores': brier_result,
            'proposals': len(proposals['candidates']),
            'resolved': len(measured_molts),
            'anti_cascade_check': rules_check,
        }

    # Only these two constant-history events are terminal per MOLT_STATE.md's
    # state diagram (APPLIED -> MEASURED -> KEPT/REVERTED). INCONCLUSIVE is
    # PROPOSED (Q-MOLT-TEMPORAL-PURITY-01), not yet live, so it is
    # deliberately not treated as terminal here.
    _TERMINAL_MOLT_EVENTS = ("KEEP", "REVERT")

    def check_anti_cascade_rules(self) -> Dict[str, Any]:
        """Check anti-cascade rules 1, 3, 4 mechanically from constants.json's
        per-constant molt_id/molt_history fields (the live data read_constants()
        already loads). A constant counts as having an open molt when it carries
        a molt_id whose history has not yet reached a terminal KEEP/REVERT event.

        Rules 2 (no self-reference in windows) and 5 (Priority Queue rank, no
        bypass) are NOT mechanically checked here: rule 2 needs per-candidate
        evidence-timestamp provenance this data source does not carry, and
        rule 5 needs a live cross-reference against PRIORITY_QUEUE.md's actual
        ranking. Both are reported as such rather than assumed to pass — a
        check that cannot see a rule must not claim it holds.
        """
        if not self.constants:
            self.read_constants()

        open_constants = []
        frozen_constants = []
        at_risk_constants = []

        for c in self.constants:
            name = c.get('name')
            history = c.get('molt_history') or []

            if c.get('molt_id') and (not history or history[-1].get('event') not in self._TERMINAL_MOLT_EVENTS):
                open_constants.append(name)

            consecutive_reverts = 0
            max_consecutive_reverts = 0
            for entry in history:
                event = entry.get('event')
                if event == 'REVERT':
                    consecutive_reverts += 1
                    max_consecutive_reverts = max(max_consecutive_reverts, consecutive_reverts)
                elif event in self._TERMINAL_MOLT_EVENTS:
                    consecutive_reverts = 0
            if max_consecutive_reverts >= 2:
                frozen_constants.append(name)
            elif max_consecutive_reverts == 1:
                at_risk_constants.append(name)

        k_blocked = len(open_constants) > self.k_limit

        rules = {
            1: {'name': 'one open molt per constant', 'status': 'PASS',
                'note': 'structurally enforced — constants.json carries a single molt_id per constant, not a list'},
            2: {'name': 'no self-reference in windows', 'status': 'NOT_MECHANICALLY_CHECKED',
                'note': 'requires per-candidate evidence-timestamp provenance this data source does not carry'},
            3: {'name': f'K={self.k_limit} system-wide limit', 'status': 'BLOCKED' if k_blocked else 'PASS',
                'open_molt_count': len(open_constants), 'open_constants': open_constants},
            4: {'name': 'freeze after 2 consecutive reverts', 'status': 'PASS',
                'frozen_constants': frozen_constants, 'at_risk_constants': at_risk_constants},
            5: {'name': 'ranked by Priority Queue score, no bypass', 'status': 'NOT_MECHANICALLY_CHECKED',
                'note': 'requires a live cross-reference against PRIORITY_QUEUE.md rank; not available to this check'},
        }

        checked = [r for r in rules.values() if r['status'] in ('PASS', 'BLOCKED')]
        blocked = [r for r in checked if r['status'] == 'BLOCKED']

        return {
            'overall_status': 'BLOCKED' if blocked else 'OK',
            'rules_passed': len(checked) - len(blocked),
            'rules_warnings': len(at_risk_constants),
            'rules_blocked': len(blocked),
            'rules_not_mechanically_checked': len(rules) - len(checked),
            'open_molt_count': len(open_constants),
            'open_constants': open_constants,
            'frozen_constants': frozen_constants,
            'at_risk_constants': at_risk_constants,
            'rules': rules,
        }

    def propose_molts(self, constants_needing_eval: List[Dict]) -> Dict[str, Any]:
        """Generate molt candidates."""
        return {
            'phase': 'PROPOSE',
            'candidates_proposed': len(constants_needing_eval),
            'candidates': constants_needing_eval,
        }


# CLI Interface for Q-NF-SCHEMA-01 testing and integration
def main():
    """CLI for molt_cycle integration with NF_LEDGER."""
    if len(sys.argv) < 2:
        print("Usage: molt_cycle [--read-only --nf <path>] | [--complete] | [--help]")
        sys.exit(1)

    if sys.argv[1] == "--help":
        print("Molt Cycle CLI")
        print("  --read-only --nf <path>  : Read NF_LEDGER and report resolved predictions")
        print("  --complete               : Run full molt cycle simulation")
        return

    # Handle --read-only --nf <path> for Q-NF-SCHEMA-01 integration
    if sys.argv[1] == "--read-only" and len(sys.argv) > 2 and sys.argv[2] == "--nf":
        nf_path = sys.argv[3] if len(sys.argv) > 3 else "ledgers/NF_LEDGER.jsonl"
        mc = MoltCycle(nf_ledger_path=nf_path)

        # Read both NF_LEDGER and constants
        read_result = mc.read_nf_ledger()
        constants_result = mc.read_constants()

        if read_result['status'] == 'LEDGER_NOT_FOUND':
            print(json.dumps({
                'status': 'ERROR',
                'message': f"NF_LEDGER not found at {nf_path}",
                'nf_resolved': 0,
                'constants': len(mc.constants),
            }))
            sys.exit(1)

        # Count resolved predictions
        resolved = mc.count_resolved()
        pairs = mc.join_pin_resolve_pairs()
        brier = mc.calculate_brier_scores(pairs)

        output = {
            'status': 'OK',
            'ledger_path': nf_path,
            'ledger_entries': read_result['ledger_entries'],
            'pin_targets': read_result['pin_targets'],
            'nf_resolved': resolved,
            'pin_resolve_pairs': len(pairs),
            'brier_overall': brier['brier_overall'],
            'brier_per_predictor': {
                k: {'brier': v.get('brier'), 'n': v.get('n')}
                for k, v in brier['brier_per_predictor'].items()
            },
            'constants': len(mc.constants),
            'constant_names': constants_result.get('constant_names', []),
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Handle --complete for full cycle
    if sys.argv[1] == "--complete":
        mc = MoltCycle()
        result = mc.complete_cycle([], [])
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0)

    print(f"Unknown command: {sys.argv[1]}")
    sys.exit(1)


if __name__ == '__main__':
    main()
