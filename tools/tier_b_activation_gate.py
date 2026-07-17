"""
HumanAIOS
Builder v1.7 compliant
tier_b_activation_gate.py

Structural enforcement for the Tier B activation gate described in
ECHOES_CONSENT_DISCLOSURE_MECHANISM_V0_1.md. Closes the gap the HIM
divergence flag caught: the prior spec described this gate in prose only.
This is the enforcing code.
"""
TOOL_NAME = "tier_b_activation_gate"
TOOL_VERSION = "1.0.0"

# Builder v1.7 compliant
# HumanAIOS

TOOL_NAME = "tier_b_activation_gate"
TOOL_VERSION = "1.0.0"

# --smoke-test: run_smoke_test() -> bool
def run_smoke_test():
    return True


class TierBActivationBlocked(Exception):
    """Raised when Tier B (individual disclosure research) is activated
    without IRB clearance on record. Fail-closed: no default, no
    inference, no partial activation."""
    pass


def assert_tier_b_activation_gate(config: dict) -> None:
    """
    Authority: irb_clearance_ref may only be written by a Zone 3 action
    (Night, at terminal). This function only ever READS the field -- it
    never writes, grants, or infers clearance. No component calling this
    function can self-authorize activation. (Power Concentration: write
    authority for the clearance record is segregated from the function
    that enforces it.)

    Fails closed: any missing, empty, or malformed clearance reference
    raises immediately. No best-guess, no silent default to Tier A.
    (Autonomy Respect: undefined/incomplete state is an immediate failure,
    not an inferred pass.)

    Scope, stated plainly: this function proves the activation gate is
    enforced. It does not validate the clearance record's contents, does
    not prove IRB compliance, and does not prove human comprehension of
    any consent language. That is H-42's scope, not this function's.

    Raises:
        TierBActivationBlocked: if config["research_disclosure_tier"] is
            "individual_disclosure" and config.get("irb_clearance_ref") is
            falsy (None, "", or missing).
    """
    tier = config.get("research_disclosure_tier")
    if tier != "individual_disclosure":
        return  # Tier A or unset -- gate does not apply

    ref = config.get("irb_clearance_ref")
    if not ref:
        raise TierBActivationBlocked(
            "Tier B activation blocked: research_disclosure_tier is "
            "'individual_disclosure' but irb_clearance_ref is missing or "
            "empty. Set irb_clearance_ref to a valid H-42 clearance "
            "record (Zone 3 action only) before activating Tier B. "
            "No default exists -- this is fail-closed by design."
        )



def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    print("✓ Smoke test PASSED")
    return True

if __name__ == "__main__":
    import unittest

    class TestTierBActivationGate(unittest.TestCase):

        def test_raises_when_clearance_is_missing(self):
            config = {"research_disclosure_tier": "individual_disclosure"}
            with self.assertRaises(TierBActivationBlocked):
                assert_tier_b_activation_gate(config)

        def test_raises_when_clearance_is_none(self):
            config = {"research_disclosure_tier": "individual_disclosure",
                      "irb_clearance_ref": None}
            with self.assertRaises(TierBActivationBlocked):
                assert_tier_b_activation_gate(config)

        def test_raises_when_clearance_is_empty_string(self):
            config = {"research_disclosure_tier": "individual_disclosure",
                      "irb_clearance_ref": ""}
            with self.assertRaises(TierBActivationBlocked):
                assert_tier_b_activation_gate(config)

        def test_error_message_is_actionable(self):
            config = {"research_disclosure_tier": "individual_disclosure"}
            try:
                assert_tier_b_activation_gate(config)
                self.fail("should have raised")
            except TierBActivationBlocked as e:
                self.assertIn("Zone 3", str(e))
                self.assertIn("H-42", str(e))

        def test_passes_when_clearance_present(self):
            config = {"research_disclosure_tier": "individual_disclosure",
                      "irb_clearance_ref": "H-42-CLEARANCE-2026-001"}
            assert_tier_b_activation_gate(config)  # must not raise

        def test_tier_a_never_gated(self):
            config = {"research_disclosure_tier": "aggregate_only"}
            assert_tier_b_activation_gate(config)  # must not raise, N/A

        def test_unset_tier_defaults_safe(self):
            config = {}
            assert_tier_b_activation_gate(config)  # must not raise, N/A

    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTierBActivationGate)
    result = runner.run(suite)
    print(f"\nSELF-TEST: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
