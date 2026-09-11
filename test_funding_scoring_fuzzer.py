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
    def test_main_passes_sys_argv_to_atheris_setup(self) -> None:
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

        argv = ["funding_scoring_fuzzer", "--", "-runs=1"]
        with mock.patch.object(sys, "argv", argv):
            module.main()

        self.assertEqual([(argv, module.TestOneInput)], setup_calls)
        self.assertEqual([True], fuzz_calls)


if __name__ == "__main__":
    unittest.main()
