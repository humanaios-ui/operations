#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parent
FUZZER_PATH = REPO_ROOT / "fuzzers" / "funding_scoring_fuzzer.py"


class _FakeAtheris:
    class FuzzedDataProvider:
        pass

    def __init__(self) -> None:
        self.setup_args = None
        self.fuzz_called = False

    def instrument_imports(self):
        return nullcontext()

    def Setup(self, argv, callback) -> None:
        self.setup_args = (list(argv), callback)

    def Fuzz(self) -> None:
        self.fuzz_called = True


def _load_fuzzer_module(fake_atheris: _FakeAtheris):
    spec = importlib.util.spec_from_file_location("test_funding_scoring_fuzzer_module", FUZZER_PATH)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(
        sys.modules,
        {
            "atheris": fake_atheris,
        },
    ):
        sys.path.insert(0, str(REPO_ROOT / "src"))
        try:
            assert spec.loader is not None
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
    return module


class FundingScoringFuzzerTests(unittest.TestCase):
    def test_main_passes_sys_argv_to_atheris_setup(self) -> None:
        fake_atheris = _FakeAtheris()
        module = _load_fuzzer_module(fake_atheris)

        argv = ["funding_scoring_fuzzer", "--", "-runs=1"]
        with patch.object(sys, "argv", argv):
            module.main()

        self.assertEqual(fake_atheris.setup_args[0], argv)
        self.assertIs(fake_atheris.setup_args[1], module.TestOneInput)
        self.assertTrue(fake_atheris.fuzz_called)

    def test_main_passes_non_empty_argv_to_atheris_setup(self) -> None:
        fake_atheris = _FakeAtheris()
        module = _load_fuzzer_module(fake_atheris)

        module.main([])

        self.assertEqual(fake_atheris.setup_args[0], ["funding_scoring_fuzzer"])
        self.assertIs(fake_atheris.setup_args[1], module.TestOneInput)
        self.assertTrue(fake_atheris.fuzz_called)

    def test_main_preserves_runtime_argv(self) -> None:
        fake_atheris = _FakeAtheris()
        module = _load_fuzzer_module(fake_atheris)

        module.main(["fuzzer-bin", "-runs=4"])

        self.assertEqual(fake_atheris.setup_args[0], ["fuzzer-bin", "-runs=4"])

    def test_consume_opportunity_uses_list_for_pick_value(self) -> None:
        class _RecordingFdp:
            def __init__(self) -> None:
                self.picked_values_type = None

            def ConsumeUnicodeNoSurrogates(self, _max_length: int) -> str:
                return "x"

            def PickValueInList(self, values):
                self.picked_values_type = type(values)
                return values[0]

            def ConsumeBool(self) -> bool:
                return False

        fake_atheris = _FakeAtheris()
        module = _load_fuzzer_module(fake_atheris)
        fdp = _RecordingFdp()

        opportunity = module._consume_opportunity(fdp)

        self.assertIs(fdp.picked_values_type, list)
        self.assertEqual(opportunity["category"], "grants")


if __name__ == "__main__":
    unittest.main()
