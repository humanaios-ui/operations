from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "automata-lineage-lab"
    / "pilot-001-talos"
    / "talos_state_machine.py"
)


spec = importlib.util.spec_from_file_location("talos_state_machine", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class TalosStateMachineTest(unittest.TestCase):
    def test_talos_variants_keep_fixed_contract_and_no_prohibited_actions(self) -> None:
        scenarios = module.load_scenarios(MODULE_PATH.with_name("talos_scenarios.json"))
        records = module.evaluate_all(scenarios)

        self.assertEqual(len(records), len(module.VARIANTS) * len(scenarios))
        self.assertTrue(all(record["fixed_contract"] for record in records))
        self.assertTrue(all(not record["prohibited_action_violation"] for record in records))

    def test_talos_variants_match_expected_outcomes(self) -> None:
        scenarios = module.load_scenarios(MODULE_PATH.with_name("talos_scenarios.json"))
        records = module.evaluate_all(scenarios)

        self.assertTrue(all(record["outcome"] == record["expected_outcome"] for record in records))


if __name__ == "__main__":
    unittest.main()
