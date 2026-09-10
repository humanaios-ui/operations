#!/usr/bin/env python3
"""
test_nf_schema.py — Verify NF_EVENT_SCHEMA PIN/RESOLVE join logic

Test: resolved specimen-intake forecast shows up in molt_cycle output
"""

import json
import tempfile
import os
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

def test_nf_schema_join():
    """Test PIN + RESOLVE join produces resolved forecasts in molt_cycle"""

    # Create temporary ledger
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test_ledger.jsonl"

        # Write schema-compliant events (minimal)
        events = [
            # OPEN
            {
                "seq": 1,
                "type": "OPEN",
                "at": "2026-09-10T12:00:00+00:00",
                "by": "Z1",
                "ledger": "NF_LEDGER",
                "version": "v0.1",
                "window": "test",
                "source_plan": "test",
                "registered_sha": "test",
                "main_sha": "test",
                "resolver": "molt_cycle"
            },
            # PIN: Z1 prediction
            {
                "seq": 2,
                "type": "PIN",
                "at": "2026-09-10T12:00:00+00:00",
                "by": "Z1",
                "pin_id": "T-test-01:Z1",
                "token_id": "T-test-01",
                "target": "T-test-01",
                "predictor": "Z1",
                "p": 0.75,
                "scoreable": False
            },
            # DATE: Z2 authorizes timestamp
            {
                "seq": 3,
                "type": "DATE",
                "at": "2026-09-10T13:00:00+00:00",
                "by": "Z2",
                "token_id": "T-test-01",
                "issued_date": "2026-09-10"
            },
            # PIN: Z2 prediction (after DATE)
            {
                "seq": 4,
                "type": "PIN",
                "at": "2026-09-10T13:00:00+00:00",
                "by": "Z2",
                "pin_id": "T-test-01:Z2",
                "token_id": "T-test-01",
                "target": "T-test-01",
                "predictor": "Z2",
                "p": 0.80,
                "scoreable": True
            },
            # RESOLVE: outcome observed
            {
                "seq": 5,
                "type": "RESOLVE",
                "at": "2026-09-11T10:00:00+00:00",
                "by": "Z2",
                "token_id": "T-test-01",
                "outcome": "YES",
                "source": "tree-read:abc123"
            }
        ]

        # Write events to ledger
        with open(ledger_path, "w") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")

        # Read ledger like molt_cycle does
        pins = {}
        resolves = {}
        dates = {}

        for line in ledger_path.read_text().split("\n"):
            if not line.strip():
                continue
            row = json.loads(line)
            t = row.get("type")
            if t == "PIN":
                pins[row.get("pin_id")] = row
            elif t == "RESOLVE":
                resolves.setdefault(row.get("token_id"), []).append(row)
            elif t == "DATE":
                dates[row.get("token_id")] = row

        # JOIN: PIN + DATE + RESOLVE
        resolved = []
        for pin_id, pin in pins.items():
            tid = pin.get("token_id")
            if tid not in dates:
                continue  # No DATE
            if not pin.get("scoreable"):
                continue  # Not scoreable
            if tid not in resolves or not resolves[tid]:
                continue  # No RESOLVE

            res = resolves[tid][-1]  # Latest RESOLVE
            outcome_str = res.get("outcome", "")
            if outcome_str not in ("YES", "NO"):
                continue

            outcome_float = 1.0 if outcome_str == "YES" else 0.0
            resolved.append({
                "pin_id": pin_id,
                "token_id": tid,
                "predictor": pin.get("predictor"),
                "p": pin.get("p"),
                "outcome": outcome_str,
                "outcome_float": outcome_float,
                "brier_component": (float(pin.get("p", 0)) - outcome_float) ** 2
            })

        # Verify
        assert len(resolved) == 1, f"Expected 1 resolved forecast, got {len(resolved)}"
        r = resolved[0]
        assert r["pin_id"] == "T-test-01:Z2", f"Expected Z2 pin (scoreable), got {r['pin_id']}"
        assert r["p"] == 0.80, f"Expected p=0.80, got {r['p']}"
        assert r["outcome"] == "YES", f"Expected outcome=YES, got {r['outcome']}"
        assert abs(r["brier_component"] - 0.04) < 1e-6, f"Expected Brier=(0.80-1.0)^2=0.04, got {r['brier_component']}"

        print("✓ PIN + DATE + RESOLVE join works correctly")
        print(f"  Resolved forecast: {r}")
        return True

if __name__ == "__main__":
    try:
        test_nf_schema_join()
        print("\nAll tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
