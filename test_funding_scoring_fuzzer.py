#!/usr/bin/env python3
import importlib.util
import sys
import types
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent
FUZZER_PATH = REPO_ROOT / "fuzzers" / "funding_scoring_fuzzer.py"


class FundingScoringFuzzerTests(unittest.TestCase):
    def _load_module(self):
        setup_calls = []
        fuzz_calls = []

        fake_atheris = types.SimpleNamespace(
            instrument_imports=lambda: nullcontext(),
            FuzzedDataProvider=object,
            Setup=lambda argv, callback: setup_calls.append((argv, callback)),
            Fuzz=lambda: fuzz_calls.append(True),
        )

        spec = importlib.util.spec_from_file_location("funding_scoring_fuzzer_under_test", FUZZER_PATH)
        module = importlib.util.module_from_spec(spec)

        with mock.patch.dict(sys.modules, {"atheris": fake_atheris}, clear=False):
            sys.path.insert(0, str(REPO_ROOT / "src"))
            try:
                assert spec.loader is not None
                spec.loader.exec_module(module)
            finally:
                sys.path.pop(0)

        return module, setup_calls, fuzz_calls

    def test_main_passes_sys_argv_to_atheris_setup(self) -> None:
        module, setup_calls, fuzz_calls = self._load_module()

        argv = ["funding_scoring_fuzzer", "--", "-runs=1"]
        with mock.patch.object(sys, "argv", argv):
            module.main()

        self.assertEqual([(argv, module.TestOneInput)], setup_calls)
        self.assertEqual([True], fuzz_calls)

    def test_main_falls_back_to_default_name_for_empty_argv(self) -> None:
        module, setup_calls, fuzz_calls = self._load_module()

        with mock.patch.object(sys, "argv", []):
            module.main()

        self.assertEqual([(["funding_scoring_fuzzer"], module.TestOneInput)], setup_calls)
        self.assertEqual([True], fuzz_calls)

    def test_consume_opportunity_passes_list_to_pick_value_in_list(self) -> None:
        module, _, _ = self._load_module()

        class FakeFdp:
            def ConsumeUnicodeNoSurrogates(self, max_length):
                return "text"

            def PickValueInList(self, values):
                self.values = values
                return values[0]

            def ConsumeBool(self):
                return False

        fdp = FakeFdp()

        opportunity = module._consume_opportunity(fdp)

        self.assertIsInstance(fdp.values, list)
        self.assertEqual(list(module._CATEGORIES), fdp.values)
        self.assertEqual(module._CATEGORIES[0], opportunity["category"])


if __name__ == "__main__":
    unittest.main()
