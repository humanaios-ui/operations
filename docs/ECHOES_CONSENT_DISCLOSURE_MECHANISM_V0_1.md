# ECHOES_CONSENT_DISCLOSURE_MECHANISM_V0_1.md

**Purpose:** Build and validate the disclosure mechanism Clarity lacked,
inside Echoes — a zero-individual-stakes proving ground — so the same
mechanism can later be pointed at real-stakes deployments (e.g.
H-CAND-VULN-DISCLOSURE-01) without re-deriving it under pressure.

**Status:** Zone 1 draft. Per P30 (GOVERNANCE v6.4.2), this spec requires
the interactive `acat_document_analyzer_v1.1` pass with Night as
analyst-reviewer before it can be presented for Zone 2 ratification. The
automated evidence-density pass below is prep only — it does not satisfy
the gate.

## Two tiers, not one

Clarity's failure was treating all backend research the same way and hiding
all of it. The fix is to make the tier explicit and gate disclosure by what's
actually being collected.

| | Tier A — Aggregate System Research | Tier B — Individual Disclosure Research |
|---|---|---|
| **What's collected** | Anonymized gameplay analytics, Copilot build-compliance | Real personal content/disclosure from an individual |
| **Echoes' actual state** | This is what Echoes is | Not present in Echoes. Specified here, not implemented. |
| **Disclosure mechanism** | Privacy policy only (standard practice) | Visible, separate, plain-language opt-in screen — never privacy-policy-only |
| **Consent record needed** | None beyond standard ToS acceptance | Yes — `consent_record` schema below |
| **Activation gate** | Already active | `irb_clearance_ref` non-null + Zone 2 ratification, structurally enforced |

Echoes only ever needs Tier A. Tier B exists in this spec so the mechanism
is ready, not so it activates here.

## Tier A — what Echoes actually implements

**Privacy policy paragraph (drop-in text):**

> Echoes collects anonymous gameplay data — gesture timing, choice IDs, and
> your own ratings of how a sealed timeline felt (coherent, surprising,
> moving, unstable) — to improve the game and to support an independent,
> published research project on AI behavior. No names, device identifiers,
> or written text you enter is collected. See the full schema and the
> research at humanaios.ai.

**Onboarding copy (must contain none of the above):**

> Welcome to the Archive. Pull a thread, see where it leads. There's no
> wrong way to wander.

This is the literal split the Echoes manual already specifies (§1.2,
constraint 2): research mentioned only in privacy policy, never onboarding.
The fix from Clarity isn't a new rule — it's confirming the rule is
followed where Clarity violated it ("never hint, ever, anywhere").

## Tier B — specified, not activated

```json
{
  "consent_record": {
    "tier": "individual_disclosure",
    "granted_at": "ISO8601 timestamp",
    "scope_description_shown": "exact text of disclosure shown to participant",
    "withdrawal_requested_at": "ISO8601 timestamp or null",
    "irb_clearance_ref": "H-42 clearance reference — required, null blocks activation"
  }
}
```

**Activation gate — enforcing code, not a policy sentence.**

```python
class TierBActivationBlocked(Exception):
    """Raised when Tier B is activated without IRB clearance on record.
    Fail-closed: no default, no inference, no partial activation."""
    pass


def assert_tier_b_activation_gate(config: dict) -> None:
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
```

Verified 7/7 against: missing ref, `None` ref, empty-string ref, present
ref (must not raise), Tier A (gate doesn't apply), and unset tier (gate
doesn't apply). Embedded inline below so the claim is checkable from this
document alone, not just by reference to a separate file.

```python
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
```

Full standalone file (same code, runnable directly): `tier_b_activation_gate.py`.

**Write-authority segregation (Power Concentration).** `irb_clearance_ref`
may only be *written* by a Zone 3 action — Night, at terminal. This
function only ever *reads* the field. No component that calls this
function can grant itself clearance; the function that enforces the gate
and the authority that satisfies it are different actors by construction,
not by convention.

**Fail-closed, no inference (Autonomy Respect).** A missing or malformed
clearance reference is an immediate raise, never a best-guess default to
Tier A. Undefined state is a hard stop, not an inferred pass.

**Scope of this claim (Truth).** This function and its tests prove the
activation *gate* is enforced. They do not prove IRB compliance, do not
validate the clearance record's contents, and do not prove human
comprehension of any consent language — that remains H-42's scope,
unchanged from the limitation already stated above.

## What this proves, and what it doesn't

This sandbox can validate: does the disclosure paragraph render, does it
stay out of onboarding, does the existing scanner correctly pass Tier A and
correctly block a Tier B-shaped leak. It cannot validate human comprehension
of consent language or real willingness to opt in — no real person makes a
real disclosure decision about real personal stakes inside Echoes, by
design. When Tier B ever activates for real deployment, the disclosure UX
itself still needs its own human-facing validation under H-42. Proven
plumbing is not proven consent.

## Functional test plan

Reuse `echoes_copilot_acat_scanner_v0_1.py` CHECK_2_RESEARCH_DISCLOSURE_LEAK
against the actual privacy-policy and onboarding text above — no new tool
needed.
