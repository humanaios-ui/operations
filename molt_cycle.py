"""
molt_cycle.py — Molt Cycle Implementation

Complete molt cycle orchestration: READ → PROPOSE → PREDICT/RATIFY → APPLY → MEASURE → KEEP/REVERT

The recursive learning function: reads from ledgers (never memory), proposes changes as molts,
Z2 ratifies, code applies and measures. Predictions are pinned and either kept or reverted
based on falsifier outcomes.

Anti-cascade rules (CLAUDE.md Decision Routing), checked by check_anti_cascade_rules():
1. One open molt per constant (no new candidate inside window W) -- CHECKED
2. No self-reference in windows (candidate not from events in its own window) -- UNVERIFIED (no causal-linkage field exists in NF_LEDGER entries)
3. K=3 system-wide limit on open molts -- CHECKED
4. Freeze after 2 reverts (Z2 Tier 2 override required to reopen) -- CHECKED (the Tier-2 reopening ruling itself is flagged, not auto-verified)
5. Ranking by Priority Queue score (no bypass) -- UNVERIFIED (no linkage field ties a molt entry to its PRIORITY_QUEUE.md rank)

Checked against molt-schema NF_LEDGER entries (rows carrying both `molt_id`
and `constant`). As of this writing no such entries exist in ledgers/NF_LEDGER.jsonl
-- MOLT_STATE.md's one ratified pilot (Q-BLOCKCHAIN-TRADING-CALIBRATION-W90PD1-MOL-001)
is recorded as prose in that file, not as a structured ledger row -- so
check_anti_cascade_rules() currently reports NO_DATA rather than a false pass.

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

    def check_anti_cascade_rules(self) -> Dict[str, Any]:
        """Check the 5 anti-cascade rules (CLAUDE.md Decision Routing) against
        real molt-schema entries in self.nf_entries (populate via read_nf_ledger()
        first). A molt-schema entry is any ledger row carrying both `molt_id` and
        `constant` keys, the shape MOLT_STATE.md documents for a ratified molt.

        Rules 1 (one open molt per constant), 3 (K=3 system-wide), and 4 (freeze
        after 2 consecutive reverts) are mechanically checkable from that shape
        and are actually computed here. Rules 2 (no self-reference: a candidate
        must not be generated from events inside its own window) and 5 (ranked by
        Priority Queue score, no bypass) require causal/cross-document linkage no
        NF_LEDGER entry carries today, and are reported as unverified rather than
        faked as passing -- the prior version of this method returned a static
        "5 passed" regardless of what the ledger actually held.

        Freeze semantics (rule 4): per constant, look at the two most recent
        *resolved* molts (outcome KEEP or REVERT) in ledger order. An
        INCONCLUSIVE outcome is excluded from that resolved sequence entirely,
        matching MOLT_STATE.md's "Measurement closure" doctrine that an
        administrative close "measured nothing and must not be allowed to
        masquerade as evidence against the constant" -- so REVERT, INCONCLUSIVE,
        REVERT still freezes on the two real measured reverts.
        """
        molt_entries = [e for e in self.nf_entries if e.get('molt_id') and e.get('constant')]

        by_constant: Dict[str, List[Dict]] = {}
        for e in molt_entries:
            by_constant.setdefault(e['constant'], []).append(e)

        open_by_constant: Dict[str, int] = {}
        frozen_constants = set()
        for constant, entries in by_constant.items():
            open_count = sum(1 for e in entries if e.get('outcome') == 'MEASURING')
            if open_count:
                open_by_constant[constant] = open_count

            resolved = [e for e in entries if e.get('outcome') in ('KEEP', 'REVERT')]
            if (len(resolved) >= 2
                    and resolved[-1].get('outcome') == 'REVERT'
                    and resolved[-2].get('outcome') == 'REVERT'):
                frozen_constants.add(constant)

        open_molt_count = sum(1 for e in molt_entries if e.get('outcome') == 'MEASURING')

        violations = []

        rule1_violations = {c: n for c, n in open_by_constant.items() if n > 1}
        if rule1_violations:
            violations.append({
                'rule': 1,
                'detail': f'multiple concurrent open molts on: {sorted(rule1_violations)}',
            })

        if open_molt_count > self.k_limit:
            violations.append({
                'rule': 3,
                'detail': f'{open_molt_count} open molts exceeds K={self.k_limit}',
            })

        rule4_violations = [c for c in frozen_constants if open_by_constant.get(c, 0) > 0]
        if rule4_violations:
            violations.append({
                'rule': 4,
                'detail': (f'open molt on frozen constant(s): {sorted(rule4_violations)} '
                           '(requires Z2 Tier-2 ruling to reopen; that ruling is not '
                           'representable in ledger data alone, so this is flagged for '
                           'review rather than auto-blocked)'),
            })

        unverified = [
            {'rule': 2, 'reason': ('no-self-reference requires causal linkage between a '
                                    'candidate and the events that produced it -- not '
                                    'present in NF_LEDGER entries')},
            {'rule': 5, 'reason': ('Priority Queue rank ordering requires cross-referencing '
                                    'PRIORITY_QUEUE.md scores against proposal submission '
                                    'order -- no linkage field exists yet')},
        ]

        if not molt_entries:
            note = ('no molt-schema entries (both `molt_id` and `constant` keys) found in '
                    'NF_LEDGER; MOLT_STATE.md documents Q-BLOCKCHAIN-TRADING-CALIBRATION-'
                    'W90PD1-MOL-001 as a ratified pilot, but it exists as prose in that '
                    'file, not as a structured ledger entry -- nothing to check yet')
        else:
            note = f'{len(molt_entries)} molt-schema entries across {len(by_constant)} constant(s)'

        return {
            'overall_status': 'BLOCKED' if violations else ('OK' if molt_entries else 'NO_DATA'),
            'rules_checked': [1, 3, 4],
            'rules_unverified': [2, 5],
            'rules_passed': 3 - len(violations),
            'rules_blocked': len(violations),
            'violations': violations,
            'unverified': unverified,
            'open_molt_count': open_molt_count,
            'frozen_constants': sorted(frozen_constants),
            'note': note,
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
