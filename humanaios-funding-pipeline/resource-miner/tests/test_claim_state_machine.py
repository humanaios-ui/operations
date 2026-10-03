import copy
import json
import tempfile
import unittest
from pathlib import Path

from resource_miner.claim_state_machine import (
    claim_asserted_event,
    evidence_recorded_event,
    facet_resolved_event,
    falsifier_evaluated_event,
    reconcile_claim_event_ledger,
    replay_claim_events,
)
from resource_miner.mines import bind_opportunity, stable_mine_id
from resource_miner.models import EvidenceRef, ResourceMine
from resource_miner.normalize import normalize_generic
from resource_miner.opportunity_claim import build_opportunity_claim

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "free_online_certification_claims_2026-10-03.json"


def build_specimen(spec):
    mine = ResourceMine(
        mine_id=stable_mine_id(spec["mine_url"]),
        name=spec["mine_name"],
        mine_kind="PROGRAM_PLATFORM",
        canonical_url=spec["mine_url"],
        resolver="fixture",
        roles=["OPPORTUNITY_SOURCE", "EVIDENCE_SOURCE"],
    )
    first = spec["initial_evidence"]
    candidate = normalize_generic(
        title=spec["title"],
        url=spec["canonical_url"],
        source_name=spec["mine_name"],
        discovery_method="certification_concept_fixture",
        description=spec["description"],
        observed_at=first["observed_at"],
        opportunity_identity=spec["opportunity_identity"],
        opportunity_kind=spec["opportunity_kind"],
        opportunity_source_kind="official_web_fixture",
    )
    candidate.evidence = [EvidenceRef(**first)]
    candidate = bind_opportunity(
        mine,
        candidate,
        opportunity_source_kind="official_web_fixture",
    )
    claim = build_opportunity_claim(candidate)
    claim.claim_text = spec["extracted_claim"]
    history = [
        claim_asserted_event(
            claim,
            actor_type="SYSTEM",
            actor_id="certification-concept-extractor",
            method="concept_decomposition",
        )
    ]

    for event_spec in spec["events"]:
        evidence = EvidenceRef(**event_spec["evidence"])
        common = dict(
            actor_type=event_spec["actor_type"],
            actor_id=event_spec["actor_id"],
            method=event_spec["method"],
            uncertainty=event_spec.get("uncertainty", ""),
            confidence=event_spec.get("confidence"),
        )
        if event_spec["event_type"] == "EVIDENCE_RECORDED":
            event, claim = evidence_recorded_event(
                history,
                claim,
                facet=event_spec["facet"],
                relation=event_spec["relation"],
                evidence=evidence,
                **common,
            )
        elif event_spec["event_type"] == "FALSIFIER_EVALUATED":
            spec_row = next(
                row
                for row in claim.falsifiers
                if row.facet == event_spec["falsifier_facet"]
            )
            event, claim = falsifier_evaluated_event(
                history,
                claim,
                falsifier_id=spec_row.falsifier_id,
                observed=event_spec["observed"],
                evidence=evidence,
                **common,
            )
        else:
            raise AssertionError(f"unsupported fixture event: {event_spec['event_type']}")
        history.append(event)
        replayed = replay_claim_events(history)
        assert replayed.to_dict() == claim.to_dict()

    return history, claim


class ClaimStateMachineTests(unittest.TestCase):
    def test_event_schema_has_chain_and_transition_fields(self):
        schema = json.loads(
            (ROOT / "schemas" / "claim-evaluation-event.v1.schema.json").read_text()
        )
        required = set(schema["required"])
        for field in [
            "event_id",
            "sequence",
            "previous_event_id",
            "prior_overall_state",
            "resulting_overall_state",
            "payload",
        ]:
            self.assertIn(field, required)
        self.assertEqual(schema["properties"]["authority_effect"]["const"], "NONE")

    def test_free_certification_concept_replays_to_expected_states(self):
        fixture = json.loads(FIXTURE.read_text())
        observed = {}
        for spec in fixture:
            history, claim = build_specimen(spec)
            facets = {row.name: row.state for row in claim.facets}
            expected = spec["expected"]
            self.assertEqual(claim.overall_state, expected["overall_state"])
            for facet, state in expected.items():
                if facet == "overall_state":
                    continue
                self.assertEqual(facets[facet], state, spec["specimen_id"])
            replayed = replay_claim_events([row.to_dict() for row in history])
            self.assertEqual(replayed.to_dict(), claim.to_dict())
            observed[spec["specimen_id"]] = claim.overall_state

        self.assertEqual(
            observed,
            {
                "CERT-GOOGLE-ADS-FOUNDATIONAL": "SUPPORTED",
                "CERT-HUBSPOT-SEO": "RETIRED",
                "CERT-FCC-RWD": "SUPPORTED",
                "CERT-SALESFORCE-OFFICIAL": "CONTESTED",
                "CERT-ALISON-CERTIFICATE": "CONTESTED",
            },
        )

    def test_replay_detects_payload_tampering(self):
        spec = json.loads(FIXTURE.read_text())[0]
        history, _ = build_specimen(spec)
        tampered = [row.to_dict() for row in history]
        tampered[-1] = copy.deepcopy(tampered[-1])
        tampered[-1]["payload"]["evidence"]["claim"] = "tampered claim text"
        with self.assertRaises(ValueError):
            replay_claim_events(tampered)

    def test_replay_detects_broken_chain(self):
        spec = json.loads(FIXTURE.read_text())[0]
        history, _ = build_specimen(spec)
        broken = [row.to_dict() for row in history]
        broken[-1] = copy.deepcopy(broken[-1])
        broken[-1]["previous_event_id"] = "CEV-00000000000000000000"
        with self.assertRaises(ValueError):
            replay_claim_events(broken)

    def test_replay_detects_forged_resulting_state_even_with_rehashed_event_missing(self):
        spec = json.loads(FIXTURE.read_text())[1]
        history, _ = build_specimen(spec)
        broken = [row.to_dict() for row in history]
        broken[-1] = copy.deepcopy(broken[-1])
        broken[-1]["resulting_overall_state"] = "SUPPORTED"
        with self.assertRaises(ValueError):
            replay_claim_events(broken)

    def test_eligibility_resolution_requires_non_system_resolver(self):
        spec = json.loads(FIXTURE.read_text())[0]
        history, claim = build_specimen(spec)
        evidence = EvidenceRef(
            url="https://example.test/eligibility",
            kind="eligibility_resolution",
            observed_at="2026-10-03T15:00:00Z",
            claim="Applicant-specific predicates were evaluated by a resolver.",
        )
        with self.assertRaises(ValueError):
            facet_resolved_event(
                history,
                claim,
                facet="ELIGIBILITY",
                state="SUPPORTED",
                evidence=evidence,
                actor_type="SYSTEM",
                actor_id="resource-miner",
                method="discovery",
            )

        event, updated = facet_resolved_event(
            history,
            claim,
            facet="ELIGIBILITY",
            state="SUPPORTED",
            evidence=evidence,
            actor_type="RESOLVER",
            actor_id="entitlement-resolver",
            method="authoritative_predicate_evaluation",
        )
        history.append(event)
        self.assertEqual(
            next(row.state for row in updated.facets if row.name == "ELIGIBILITY"),
            "SUPPORTED",
        )
        self.assertEqual(replay_claim_events(history).to_dict(), updated.to_dict())

    def test_reconcile_ledger_is_append_only_and_idempotent(self):
        spec = json.loads(FIXTURE.read_text())[0]
        history, claim = build_specimen(spec)
        # Reconcile starts from the current claim as its genesis state.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            first = reconcile_claim_event_ledger(path, [claim])
            self.assertEqual(len(first), 1)
            self.assertEqual(first[0].event_type, "CLAIM_ASSERTED")
            second = reconcile_claim_event_ledger(path, [claim])
            self.assertEqual(second, [])

            replayed = replay_claim_events(
                [
                    json.loads(line)
                    for line in path.read_text().splitlines()
                    if line.strip()
                ]
            )
            self.assertEqual(replayed.to_dict(), claim.to_dict())

            # A later novel observation appends one event rather than replacing history.
            from resource_miner.opportunity_claim import add_claim_evidence

            later = add_claim_evidence(
                claim,
                facet="CURRENTNESS",
                relation="SUPPORTS",
                evidence=EvidenceRef(
                    url=spec["canonical_url"],
                    kind="followup_observation",
                    observed_at="2026-10-04T14:00:00Z",
                    claim="Opportunity surface observed again.",
                ),
            )
            appended = reconcile_claim_event_ledger(path, [later])
            self.assertEqual(len(appended), 1)
            self.assertEqual(appended[0].sequence, 1)
            rows = [
                json.loads(line)
                for line in path.read_text().splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 2)
            self.assertEqual(replay_claim_events(rows).to_dict(), later.to_dict())


if __name__ == "__main__":
    unittest.main()
