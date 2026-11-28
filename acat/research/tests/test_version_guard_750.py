"""Synthetic-only regression cases for the unratified ACAT #750 diagnostic."""
import importlib.util
import pathlib
import unittest

MODULE = pathlib.Path(__file__).resolve().parents[1] / "version_guard_750.py"
SPEC = importlib.util.spec_from_file_location("version_guard_750", MODULE)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

def values(v):
    return dict.fromkeys(guard.CORE6, v)

def binding(**override):
    b = dict(instrument_family=guard.HISTORICAL_FAMILY, session_id="synthetic-1",
             tier="core6", p1_prompt_digest="synthetic-p1", p2_prompt_digest="synthetic-p2",
             p3_prompt_digest="synthetic-p3", exposure="historical_numeric", scale="0-100")
    b.update(override)
    return b

class SyntheticContractTests(unittest.TestCase):
    def test_upward_correction_is_not_clamped(self):
        result = guard.diagnostic(values(80), values(100), binding())
        self.assertEqual(result["standing"], "DESCRIPTIVE_SYNTHETIC_ONLY")
        self.assertAlmostEqual(result["li"], 1.25)
        self.assertEqual(result["sag"], -120)
        self.assertFalse(result["canonical"])

    def test_downward_correction(self):
        result = guard.diagnostic(values(80), values(60), binding())
        self.assertAlmostEqual(result["li"], .75)
        self.assertEqual(result["sag"], 120)

    def test_stable_is_not_verified_calibration(self):
        result = guard.diagnostic(values(80), values(80), binding())
        self.assertEqual(result["li"], 1.0)
        self.assertEqual(result["reason"], "NOT_CANONICAL")

    def test_zero_is_held(self):
        self.assertEqual(guard.diagnostic(values(0), values(1), binding())["reason"],
                         "ZERO_BASELINE")
        self.assertEqual(guard.diagnostic(values(0), values(0), binding())["li"], None)

    def test_missing_version_binding_is_held(self):
        self.assertEqual(guard.diagnostic(values(80), values(70), {})["standing"], "HOLD")

    def test_twelve_schema_is_not_equated_with_six(self):
        result = guard.diagnostic(values(80), values(70),
                                  binding(instrument_family="acat-ops-12-0to100"))
        self.assertEqual(result["reason"], "UNSUPPORTED_OR_UNRATIFIED_FAMILY")

    def test_one_to_ten_scale_not_silently_rescaled(self):
        result = guard.diagnostic(values(8), values(7), binding(scale="1-10"))
        self.assertEqual(result["reason"], "INCOMPATIBLE_TIER_OR_SCALE")

    def test_missing_or_extra_axis_is_held(self):
        missing = values(80)
        missing.pop("humility")
        self.assertEqual(guard.diagnostic(missing, values(70), binding())["reason"],
                         "MIXED_OR_MISSING_DIMENSIONS")
        extra = values(70)
        extra["handoff"] = 60
        self.assertEqual(guard.diagnostic(values(80), extra, binding())["reason"],
                         "MIXED_OR_MISSING_DIMENSIONS")

    def test_invalid_number_is_held(self):
        for invalid in (float("nan"), float("inf"), True, -1, 101, "90"):
            bad = values(80)
            bad["truth"] = invalid
            self.assertEqual(guard.diagnostic(bad, values(70), binding())["standing"],
                             "HOLD")

    def test_anchoring_unknown_is_held(self):
        self.assertEqual(guard.diagnostic(values(80), values(70),
                                          binding(exposure="unknown"))["standing"], "HOLD")

if __name__ == "__main__":
    unittest.main()
