"""Follow-up to PR #1153 (CodeRabbit on integration/oracle.py): the delta must be exact, and extreme values must not
crash the oracle. Written BEFORE the fix (author-run)."""
import unittest

from integration.oracle import evaluate


def record(**kw):
    base = {"baseline": "0", "proposed": "1", "min_allowed": "0", "max_allowed": "2", "max_delta": "1",
            "artifact_present": "true", "actual_value": "1"}
    base.update(kw)
    return base


class DeltaIsExact(unittest.TestCase):
    def test_delta_slightly_over_the_limit_is_not_rounded_down_to_the_limit(self):
        over = "1." + "0" * 27 + "1"
        out = evaluate(record(proposed=over, actual_value=over))
        self.assertEqual(out["verdict"], "FAIL")
        self.assertIn("delta_exceeded", out["reasons"])

    def test_delta_slightly_under_the_limit_still_passes(self):
        under = "0." + "9" * 40
        out = evaluate(record(proposed=under, actual_value=under))
        self.assertEqual(out["verdict"], "PASS")

    def test_delta_exactly_at_the_limit_is_inclusive_even_with_many_digits(self):
        exact = "1." + "0" * 40
        out = evaluate(record(proposed=exact, actual_value=exact, max_delta="1"))
        self.assertEqual(out["verdict"], "PASS")
        self.assertIn("delta_boundary_inclusive", out["reasons"])

    def test_zero_delta_still_allowed(self):
        out = evaluate(record(baseline="1", proposed="1", max_delta="0", actual_value="1"))
        self.assertEqual((out["verdict"], "zero_delta_allowed" in out["reasons"]), ("PASS", True))

    def test_negative_direction_is_exact_too(self):
        over = "-1." + "0" * 27 + "1"
        out = evaluate(record(proposed=over, actual_value=over, min_allowed="-2", max_allowed="0"))
        self.assertEqual(out["verdict"], "FAIL")


class ExtremeValuesDoNotCrash(unittest.TestCase):
    def test_huge_exponent_gives_unknown_not_an_exception(self):
        big = "1e1000000"
        out = evaluate(record(proposed=big, max_allowed=big, max_delta=big, actual_value=big))
        self.assertEqual(out["verdict"], "UNKNOWN")

    def test_tiny_exponent_gives_unknown_not_an_exception(self):
        out = evaluate(record(baseline="1e-1000000"))
        self.assertEqual(out["verdict"], "UNKNOWN")

    def test_evaluate_never_raises_on_numeric_strings(self):
        for v in ("1e999999999", "-1e999999999", "9" * 5000, "1e-999999999", "0.0000000001e999"):
            for field in ("baseline", "proposed", "min_allowed", "max_allowed", "max_delta"):
                out = evaluate(record(**{field: v}))
                self.assertIn(out["verdict"], {"PASS", "FAIL", "UNKNOWN"})

    def test_the_documented_range_limit_is_enforced_not_just_the_arithmetic_trap(self):
        inside = "1e1000"
        outside = "1e1001"
        self.assertNotEqual(evaluate(record(max_allowed=inside))["reasons"], ["numeric_out_of_supported_range"])
        out = evaluate(record(max_allowed=outside))
        self.assertEqual((out["verdict"], out["reasons"]), ("UNKNOWN", ["numeric_out_of_supported_range"]))
        out = evaluate(record(baseline="1." + "0" * 1000 + "1"))  # 1002 digits
        self.assertEqual((out["verdict"], out["reasons"]), ("UNKNOWN", ["numeric_out_of_supported_range"]))

    def test_ordinary_values_are_unaffected(self):
        self.assertEqual(evaluate(record())["verdict"], "PASS")
        self.assertEqual(evaluate(record(proposed="3", actual_value="3"))["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
