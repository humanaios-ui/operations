"""ACAT-R E0: bounded offline P1 -> P2 -> P3 currentness calibration.

Synthetic public URLs only. No network, application, or authority effects.
This test preserves baseline commitments and checks that stale positive evidence
cannot erase a newer contradictory or falsifying observation.
"""
import copy
import unittest

from resource_miner.claim_state_machine import (
    claim_asserted_event,
    evidence_recorded_event,
    facet_resolved_event,
    falsifier_evaluated_event,
    replay_claim_events,
)
from resource_miner.models import EvidenceRef, ResourceCandidate
from resource_miner.opportunity_claim import build_opportunity_claim

SOURCE = "https://example.org/controlled-opportunity"


def observation(kind, observed_at, claim):
    return EvidenceRef(
        url=SOURCE, kind=kind, observed_at=observed_at, claim=claim,
    )


def baseline():
    candidate = ResourceCandidate(
        resource_id="ACAT-R-E0",
        title="Synthetic calibration opportunity",
        source_name="ACAT-R synthetic fixture",
        source_url=SOURCE,
        canonical_url=SOURCE,
        discovery_method="synthetic",
        discovered_at="2026-10-20T10:00:00Z",
        opportunity_id="OPP-ACAT-R-E0",
        opportunity_token="urn:humanaios:resource-opportunity:OPP-ACAT-R-E0",
        opportunity_kind="SYNTHETIC",
        evidence=[observation(
            "mine_observation", "2026-10-20T10:00:00Z",
            "Observed opportunity available on October 20.",
        )],
    )
    initial = build_opportunity_claim(candidate)
    return initial, [claim_asserted_event(initial)]


def state(claim, facet):
    return next(item.state for item in claim.facets if item.name == facet)


class ACATRuntimeCurrentnessPilot(unittest.TestCase):
    def test_p1_commit_is_supported_but_not_an_application_grant(self):
        claim, history = baseline()
        self.assertEqual(state(claim, "CURRENTNESS"), "SUPPORTED")
        self.assertEqual(claim.overall_state, "SUPPORTED")
        self.assertEqual(state(claim, "ELIGIBILITY"), "UNASSESSED")
        self.assertEqual(claim.authorization_state, "NOT_REQUESTED")
        self.assertEqual(claim.authority_effect, "NONE")
        self.assertEqual(replay_claim_events(history).to_dict(), claim.to_dict())

    def test_p2_newer_contradiction_is_contested(self):
        claim, history = baseline()
        event, challenged = evidence_recorded_event(
            history, claim,
            facet="CURRENTNESS", relation="CONTRADICTS",
            evidence=observation(
                "official_status_observation", "2026-10-30T10:00:00Z",
                "Official page contradicts the earlier availability claim.",
            ),
            actor_type="SYSTEM", actor_id="synthetic-verifier",
            method="offline_challenge",
        )
        history.append(event)
        self.assertEqual(state(challenged, "CURRENTNESS"), "CONTRADICTED")
        self.assertEqual(challenged.overall_state, "CONTESTED")
        self.assertEqual(replay_claim_events(history).to_dict(), challenged.to_dict())

    def test_p3_cached_positive_cannot_erase_newer_contradiction(self):
        claim, history = baseline()
        p1 = copy.deepcopy(claim.to_dict())
        challenge, contested = evidence_recorded_event(
            history, claim,
            facet="CURRENTNESS", relation="CONTRADICTS",
            evidence=observation(
                "official_status_observation", "2026-10-30T10:00:00Z",
                "Official page contradicts the old claim.",
            ),
            actor_type="SYSTEM", actor_id="synthetic-verifier",
            method="offline_challenge",
        )
        history.append(challenge)
        stale, reassessed = evidence_recorded_event(
            history, contested,
            facet="CURRENTNESS", relation="SUPPORTS",
            evidence=observation(
                "cached_mine_observation", "2026-10-21T10:00:00Z",
                "Old cached link still has an availability claim.",
            ),
            actor_type="SYSTEM", actor_id="cached-snapshot",
            method="cache_replay",
        )
        history.append(stale)
        # Independent P3 oracle: a stale cache is not fresh source verification.
        self.assertEqual(state(reassessed, "CURRENTNESS"), "CONTRADICTED")
        self.assertEqual(reassessed.overall_state, "CONTESTED")
        self.assertEqual(claim.to_dict(), p1)
        self.assertEqual(len(history), 3)
        self.assertEqual(replay_claim_events(history).to_dict(), reassessed.to_dict())
        self.assertEqual(reassessed.authority_effect, "NONE")

    def test_p3_cached_positive_cannot_resurrect_falsified_opportunity(self):
        claim, history = baseline()
        falsifier = next(f for f in claim.falsifiers if f.facet == "CURRENTNESS")
        challenge, retired = falsifier_evaluated_event(
            history, claim,
            falsifier_id=falsifier.falsifier_id, observed=True,
            evidence=observation(
                "official_status_observation", "2026-10-30T10:00:00Z",
                "Official source reports withdrawal.",
            ),
            actor_type="SYSTEM", actor_id="synthetic-verifier",
            method="offline_challenge",
        )
        history.append(challenge)
        self.assertEqual(retired.overall_state, "RETIRED")
        stale, reassessed = evidence_recorded_event(
            history, retired,
            facet="CURRENTNESS", relation="SUPPORTS",
            evidence=observation(
                "cached_mine_observation", "2026-10-20T10:00:00Z",
                "Original cached availability observation.",
            ),
            actor_type="SYSTEM", actor_id="cached-snapshot",
            method="cache_replay",
        )
        history.append(stale)
        self.assertEqual(state(reassessed, "CURRENTNESS"), "FALSIFIED")
        self.assertEqual(reassessed.overall_state, "RETIRED")
        self.assertEqual(replay_claim_events(history).to_dict(), reassessed.to_dict())

    def test_explicit_resolver_event_preserves_recovery_path(self):
        claim, history = baseline()
        challenge, contested = evidence_recorded_event(
            history, claim,
            facet="CURRENTNESS", relation="CONTRADICTS",
            evidence=observation(
                "official_status_observation", "2026-10-30T10:00:00Z",
                "Official page contests availability.",
            ),
            actor_type="SYSTEM", actor_id="synthetic-verifier",
            method="offline_challenge",
        )
        history.append(challenge)
        resolution, recovered = facet_resolved_event(
            history, contested,
            facet="CURRENTNESS", state="SUPPORTED",
            evidence=observation(
                "official_status_observation", "2026-10-30T11:00:00Z",
                "Synthetic authoritative recheck documents reopening.",
            ),
            actor_type="RESOLVER", actor_id="synthetic-independent-resolver",
            method="explicit_currentness_recheck",
        )
        history.append(resolution)
        self.assertEqual(recovered.overall_state, "SUPPORTED")
        self.assertEqual(replay_claim_events(history).to_dict(), recovered.to_dict())
        self.assertEqual(recovered.authority_effect, "NONE")
        self.assertEqual(state(recovered, "ELIGIBILITY"), "UNASSESSED")


if __name__ == "__main__":
    unittest.main()
