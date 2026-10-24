from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from tools.verified_receipts import (
    append_receipt_event,
    build_receipt_chain_for_testing,
    read_receipt_events,
)
from tools.vulnops_v0_1 import (
    ACTION_GRANT_TYPE,
    CONTROL_ACTION,
    CONTROL_ATTESTATION_TYPE,
    CONTROL_AUTHORITY_SCOPE,
    CONTROL_SCOPE,
    CONTROL_SUBJECT,
    RUNTIME_OBSERVATION_TYPE,
    ActionContext,
    VulnOpsRefusal,
    WorkloadIdentity,
    absorption_rate,
    assert_distinct_workload_identities,
    build_feed_report,
    composite_priority,
    consume_action_grant,
    parse_cisa_kev,
    parse_epss_csv,
    parse_osv_modified_csv,
    runtime_observation_scope,
    verify_feed_control_attestation,
    verify_runtime_independently,
)


ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 10, 24, 10, 0, tzinfo=timezone.utc)


def identity(role: str, marker: str) -> WorkloadIdentity:
    return WorkloadIdentity(
        identity_id=f"spiffe://humanaios.test/workload/{role.lower()}-{marker}",
        role=role,
        certificate_fingerprint="sha256:" + marker * 64,
        authentication_status="EXTERNALLY_VERIFIED",
        transport_principal=f"github-actions:job:{role.lower()}-{marker}",
    )


def action_context(**overrides) -> ActionContext:
    values = {
        "action": "DEPLOY_REMEDIATION",
        "resource": "service:payments",
        "environment": "staging",
        "head_sha": "1" * 40,
        "artifact_sha256": "sha256:" + "2" * 64,
        "runtime_revision": "payments:revision-42",
        "rollback_ref": "payments:revision-41",
    }
    values.update(overrides)
    return ActionContext(**values)


def grant_event(
    actor: WorkloadIdentity,
    context: ActionContext,
    **overrides,
) -> dict:
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "grant-1",
        "receipt_type": ACTION_GRANT_TYPE,
        "subject": actor.identity_id,
        "subject_role": actor.role,
        "action": context.action,
        "scope": context.scope(),
        "issuer": "spiffe://humanaios.test/control/issuer",
        "authority_scope": context.authority_scope(),
        "verification_status": "VERIFIED",
        "verification_strength": "CRYPTO_VERIFIED",
        "verification_method": "ED25519",
        "evidence_ref": "test:signature:grant-1",
        "issued_at": "2026-10-24T09:55:00Z",
        "not_before": "2026-10-24T09:55:00Z",
        "expires_at": "2026-10-24T10:05:00Z",
        "one_time": True,
    }
    event.update(overrides)
    return event


def consumed_grant(tmp_path: Path):
    actor = identity("DEPLOYER", "a")
    context = action_context()
    path = str(tmp_path / "grant-ledger.jsonl")
    append_receipt_event(path, grant_event(actor, context))
    _, head = read_receipt_events(path)
    consume_action_grant(
        path,
        grant_id="grant-1",
        expected_head_hash=head,
        actor=actor,
        context=context,
        now=NOW,
    )
    events, consumed_head = read_receipt_events(path)
    return actor, context, events, consumed_head


def observation_event(
    verifier: WorkloadIdentity,
    context: ActionContext,
    **overrides,
) -> dict:
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "observation-1",
        "receipt_type": RUNTIME_OBSERVATION_TYPE,
        "subject": context.resource,
        "action": "VERIFY_RUNTIME",
        "scope": runtime_observation_scope(context),
        "issuer": verifier.identity_id,
        "authority_scope": context.authority_scope(),
        "verification_status": "VERIFIED",
        "verification_strength": "CRYPTO_VERIFIED",
        "verification_method": "HARDWARE_ATTESTATION",
        "evidence_ref": "test:runtime:observation-1",
        "one_time": False,
        "observer_role": "VERIFIER",
        "observed_resource": context.resource,
        "observed_environment": context.environment,
        "observed_head_sha": context.head_sha,
        "observed_artifact_sha256": context.artifact_sha256,
        "observed_runtime_revision": context.runtime_revision,
        "rollback_ref": context.rollback_ref,
        "vulnerability_closed": True,
        "health_status": "HEALTHY",
        "observed_at": "2026-10-24T10:00:00Z",
    }
    event.update(overrides)
    return event


def control_attestation(**overrides):
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "control-1",
        "receipt_type": CONTROL_ATTESTATION_TYPE,
        "subject": CONTROL_SUBJECT,
        "action": CONTROL_ACTION,
        "scope": CONTROL_SCOPE,
        "issuer": "spiffe://humanaios.test/control/operator",
        "authority_scope": CONTROL_AUTHORITY_SCOPE,
        "verification_status": "VERIFIED",
        "verification_strength": "CRYPTO_VERIFIED",
        "verification_method": "ED25519",
        "evidence_ref": "test:control-signature",
        "one_time": False,
        "issued_at": "2026-10-24T09:00:00Z",
        "not_before": "2026-10-24T09:00:00Z",
        "expires_at": "2026-10-25T09:00:00Z",
        "gates": {
            "exact_head_admission_repaired": True,
            "distinct_workload_identities": True,
            "one_use_action_grants": True,
            "independent_runtime_verification": True,
        },
        "evidence_refs": {
            "exact_head_admission_repaired": "github:pr:1005:head:full-sha",
            "distinct_workload_identities": "test:identity-separation",
            "one_use_action_grants": "test:atomic-consumption",
            "independent_runtime_verification": "test:runtime-observation",
        },
    }
    event.update(overrides)
    return build_receipt_chain_for_testing([event])


KEV = """{
  "catalogVersion": "2026.10.24",
  "vulnerabilities": [
    {
      "cveID": "CVE-2026-0001",
      "vendorProject": "Example",
      "product": "Widget",
      "vulnerabilityName": "Example flaw",
      "dateAdded": "2026-10-23",
      "dueDate": "2026-11-01",
      "knownRansomwareCampaignUse": "Known",
      "requiredAction": "Apply update"
    }
  ]
}"""

EPSS = """#model_version:v2026.10.01,score_date:2026-10-24
cve,epss,percentile
CVE-2026-0001,0.900000000,0.990000000
CVE-2026-0002,0.050000000,0.600000000
"""

OSV = """2026-10-24T09:30:00Z,NVD/CVE-2026-0001
2026-10-24T09:00:00Z,GitHub Actions/GHSA-AAAA-BBBB-CCCC
"""


def verified_controls():
    events, head = control_attestation()
    return verify_feed_control_attestation(
        events,
        pinned_head_hash=head,
        receipt_id="control-1",
        issuer="spiffe://humanaios.test/control/operator",
        now=NOW,
    )


def test_workload_identities_are_distinct_from_transport_and_each_other():
    result = assert_distinct_workload_identities(
        [identity("DISCOVERY", "a"), identity("VERIFIER", "b")],
        required_roles=["DISCOVERY", "VERIFIER"],
    )
    assert result["status"] == "DISTINCT"
    assert result["transport_principals_authoritative"] is False


def test_duplicate_workload_identity_or_certificate_fails_closed():
    first = identity("DEPLOYER", "a")
    with pytest.raises(VulnOpsRefusal, match="DUPLICATE_WORKLOAD_IDENTITY"):
        assert_distinct_workload_identities([first, first])
    second = WorkloadIdentity(
        "spiffe://humanaios.test/workload/verifier-b",
        "VERIFIER",
        first.certificate_fingerprint,
        "EXTERNALLY_VERIFIED",
        "github-actions:job:verifier-b",
    )
    with pytest.raises(VulnOpsRefusal, match="DUPLICATE_WORKLOAD_CERTIFICATE"):
        assert_distinct_workload_identities([first, second])


def test_identity_must_be_externally_verified_and_not_transport_identity():
    candidate = identity("DEPLOYER", "a")
    unverified = WorkloadIdentity(
        candidate.identity_id,
        candidate.role,
        candidate.certificate_fingerprint,
        "SELF_ASSERTED",
        candidate.transport_principal,
    )
    with pytest.raises(VulnOpsRefusal, match="NOT_EXTERNALLY_VERIFIED"):
        unverified.validate()
    collapsed = WorkloadIdentity(
        candidate.identity_id,
        candidate.role,
        candidate.certificate_fingerprint,
        "EXTERNALLY_VERIFIED",
        candidate.identity_id,
    )
    with pytest.raises(VulnOpsRefusal, match="TRANSPORT_PRINCIPAL"):
        collapsed.validate()


def test_action_scope_changes_with_exact_head_and_target():
    original = action_context()
    assert original.scope() != action_context(head_sha="3" * 40).scope()
    assert original.scope() != action_context(resource="service:ledger").scope()


def test_one_use_grant_is_consumed_atomically_and_cannot_replay(tmp_path):
    actor = identity("DEPLOYER", "a")
    context = action_context()
    path = str(tmp_path / "ledger.jsonl")
    append_receipt_event(path, grant_event(actor, context))
    _, original_head = read_receipt_events(path)
    result = consume_action_grant(
        path,
        grant_id="grant-1",
        expected_head_hash=original_head,
        actor=actor,
        context=context,
        now=NOW,
    )
    assert result["status"] == "CONSUMED"
    assert result["can_execute"] is False

    with pytest.raises(VulnOpsRefusal, match="STALE_RECEIPT_HEAD"):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=original_head,
            actor=actor,
            context=context,
            now=NOW,
        )
    _, current_head = read_receipt_events(path)
    with pytest.raises(VulnOpsRefusal, match="RECEIPT_ALREADY_CONSUMED"):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=current_head,
            actor=actor,
            context=context,
            now=NOW,
        )


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"issuer": "spiffe://humanaios.test/workload/deployer-a"}, "SELF_ISSUED"),
        ({"expires_at": "2026-10-24T09:59:59Z"}, "GRANT_EXPIRED"),
        ({"one_time": False}, "ACTION_GRANT_MUST_BE_ONE_TIME"),
        ({"subject_role": "VERIFIER"}, "GRANT_SUBJECT_ROLE_MISMATCH"),
        ({"verification_method": "EXTERNAL_SHA256"}, "METHOD_NOT_CRYPTOGRAPHIC"),
    ],
)
def test_invalid_action_grants_are_refused_without_consumption(tmp_path, overrides, reason):
    actor = identity("DEPLOYER", "a")
    context = action_context()
    path = str(tmp_path / "ledger.jsonl")
    append_receipt_event(path, grant_event(actor, context, **overrides))
    before, head = read_receipt_events(path)
    with pytest.raises(VulnOpsRefusal, match=reason):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=head,
            actor=actor,
            context=context,
            now=NOW,
        )
    after, _ = read_receipt_events(path)
    assert after == before


def test_action_grant_is_exact_role_and_exact_scope(tmp_path):
    actor = identity("DEPLOYER", "a")
    context = action_context()
    path = str(tmp_path / "ledger.jsonl")
    append_receipt_event(path, grant_event(actor, context))
    _, head = read_receipt_events(path)
    with pytest.raises(VulnOpsRefusal, match="SCOPE_MISMATCH"):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=head,
            actor=actor,
            context=action_context(head_sha="4" * 40),
            now=NOW,
        )
    wrong_role = identity("VERIFIER", "b")
    with pytest.raises(VulnOpsRefusal, match="ROLE_MISMATCH"):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=head,
            actor=wrong_role,
            context=context,
            now=NOW,
        )


def test_duplicate_verified_grant_id_is_refused(tmp_path):
    actor = identity("DEPLOYER", "a")
    context = action_context()
    path = str(tmp_path / "ledger.jsonl")
    append_receipt_event(path, grant_event(actor, context))
    append_receipt_event(path, grant_event(actor, context))
    _, head = read_receipt_events(path)
    with pytest.raises(VulnOpsRefusal, match="VERIFIED_RECEIPT_CARDINALITY:2"):
        consume_action_grant(
            path,
            grant_id="grant-1",
            expected_head_hash=head,
            actor=actor,
            context=context,
            now=NOW,
        )


def test_independent_runtime_verification_matches_consumed_grant(tmp_path):
    actor, context, grant_events, grant_head = consumed_grant(tmp_path)
    verifier = identity("VERIFIER", "b")
    observations, observation_head = build_receipt_chain_for_testing([
        observation_event(verifier, context)
    ])
    result = verify_runtime_independently(
        grant_events=grant_events,
        grant_head_hash=grant_head,
        grant_id="grant-1",
        observation_events=observations,
        observation_head_hash=observation_head,
        observation_id="observation-1",
        actor=actor,
        verifier=verifier,
        context=context,
        now=NOW,
    )
    assert result["status"] == "VERIFIED"
    assert result["can_authorize"] is False
    assert result["can_execute"] is False


def test_actor_cannot_verify_own_runtime(tmp_path):
    actor, context, grant_events, grant_head = consumed_grant(tmp_path)
    observations, observation_head = build_receipt_chain_for_testing([
        observation_event(actor, context, issuer=actor.identity_id)
    ])
    with pytest.raises(VulnOpsRefusal, match="ROLE_MISMATCH|DUPLICATE_WORKLOAD"):
        verify_runtime_independently(
            grant_events=grant_events,
            grant_head_hash=grant_head,
            grant_id="grant-1",
            observation_events=observations,
            observation_head_hash=observation_head,
            observation_id="observation-1",
            actor=actor,
            verifier=actor,
            context=context,
            now=NOW,
        )


def test_runtime_mismatch_is_contradicted_not_verified(tmp_path):
    actor, context, grant_events, grant_head = consumed_grant(tmp_path)
    verifier = identity("VERIFIER", "b")
    observations, observation_head = build_receipt_chain_for_testing([
        observation_event(verifier, context, vulnerability_closed=False)
    ])
    result = verify_runtime_independently(
        grant_events=grant_events,
        grant_head_hash=grant_head,
        grant_id="grant-1",
        observation_events=observations,
        observation_head_hash=observation_head,
        observation_id="observation-1",
        actor=actor,
        verifier=verifier,
        context=context,
        now=NOW,
    )
    assert result["status"] == "CONTRADICTED"
    assert "VULNERABILITY_CLOSED_MISMATCH" in result["reasons"]


def test_stale_runtime_observation_is_contradicted(tmp_path):
    actor, context, grant_events, grant_head = consumed_grant(tmp_path)
    verifier = identity("VERIFIER", "b")
    observations, observation_head = build_receipt_chain_for_testing([
        observation_event(verifier, context, observed_at="2026-10-24T09:30:00Z")
    ])
    result = verify_runtime_independently(
        grant_events=grant_events,
        grant_head_hash=grant_head,
        grant_id="grant-1",
        observation_events=observations,
        observation_head_hash=observation_head,
        observation_id="observation-1",
        actor=actor,
        verifier=verifier,
        context=context,
        now=NOW,
    )
    assert result["status"] == "CONTRADICTED"
    assert "OBSERVATION_STALE" in result["reasons"]


def test_unconsumed_grant_cannot_support_runtime_verification():
    actor = identity("DEPLOYER", "a")
    verifier = identity("VERIFIER", "b")
    context = action_context()
    grants, grant_head = build_receipt_chain_for_testing([grant_event(actor, context)])
    observations, observation_head = build_receipt_chain_for_testing([
        observation_event(verifier, context)
    ])
    result = verify_runtime_independently(
        grant_events=grants,
        grant_head_hash=grant_head,
        grant_id="grant-1",
        observation_events=observations,
        observation_head_hash=observation_head,
        observation_id="observation-1",
        actor=actor,
        verifier=verifier,
        context=context,
        now=NOW,
    )
    assert result["status"] == "UNVERIFIED"
    assert "RECEIPT_NOT_CONSUMED" in result["reasons"][0]


def test_feed_control_attestation_requires_every_gate_and_evidence():
    result = verified_controls()
    assert result["status"] == "CONTROLS_ATTESTED"
    assert result["underlying_signature_verified_by_this_tool"] is False

    bad, bad_head = control_attestation(gates={
        "exact_head_admission_repaired": True,
        "distinct_workload_identities": True,
        "one_use_action_grants": True,
        "independent_runtime_verification": False,
    })
    with pytest.raises(VulnOpsRefusal, match="independent_runtime_verification"):
        verify_feed_control_attestation(
            bad,
            pinned_head_hash=bad_head,
            receipt_id="control-1",
            issuer="spiffe://humanaios.test/control/operator",
            now=NOW,
        )


def test_official_feed_formats_normalize_without_granting_action():
    kev = parse_cisa_kev(KEV)
    epss, metadata = parse_epss_csv(EPSS)
    osv = parse_osv_modified_csv(OSV)
    assert kev["CVE-2026-0001"]["known_exploited"] is True
    assert epss["CVE-2026-0001"]["probability"] == 0.9
    assert metadata["score_date"] == "2026-10-24"
    assert osv["GHSA-AAAA-BBBB-CCCC"] == {
        "modified_at": "2026-10-24T09:00:00Z",
        "record_path": "GitHub Actions/GHSA-AAAA-BBBB-CCCC",
    }

    report = build_feed_report(
        kev_text=KEV,
        epss_text=EPSS,
        osv_text=OSV,
        control_attestation=verified_controls(),
        generated_at="2026-10-24T10:00:00Z",
    )
    assert report["finding_count"] == 3
    assert report["can_execute"] is False
    assert all(item["action_allowed"] is False for item in report["findings"])
    cve = next(item for item in report["findings"] if item["vulnerability_id"] == "CVE-2026-0001")
    assert cve["priority"]["status"] == "UNASSESSED_NO_ASSET_CONTEXT"
    assert cve["priority"]["score"] is None

    schema = json.loads(
        (ROOT / "schemas/vulnops_feed_report_v0_1.schema.json").read_text()
    )
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(report),
        key=lambda error: list(error.path),
    )
    assert errors == []


def test_composite_priority_requires_asset_context_and_uses_multiple_signals():
    assert composite_priority(
        kev=True,
        epss_probability=0.9,
        known_ransomware_use="Known",
        asset_context=None,
    )["score"] is None
    assessed = composite_priority(
        kev=True,
        epss_probability=0.9,
        known_ransomware_use="Known",
        asset_context={"exposure": "INTERNET", "live_threat_activity": True},
    )
    assert assessed == {"status": "ASSESSED", "score": 97.0, "band": "CRITICAL"}


def test_feed_report_refuses_unattested_controls():
    with pytest.raises(VulnOpsRefusal, match="EXTERNAL_FEED_INTAKE_BLOCKED"):
        build_feed_report(
            kev_text=KEV,
            epss_text=EPSS,
            osv_text=OSV,
            control_attestation={"status": "SELF_ASSERTED"},
            generated_at="2026-10-24T10:00:00Z",
        )


def test_absorption_rate_is_explicit_and_handles_zero_intake():
    assert absorption_rate(resolved=12, created=10) == 1.2
    assert absorption_rate(resolved=0, created=0) is None
    with pytest.raises(VulnOpsRefusal, match="NONNEGATIVE"):
        absorption_rate(resolved=-1, created=1)


def test_feed_workflow_is_read_only_and_gates_network_after_control_proof():
    workflow = (ROOT / ".github/workflows/vulnops-intake.yml").read_text()
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "issues: write" not in workflow
    assert "pull-requests: write" not in workflow
    assert "VULNOPS_CONTROL_LEDGER_B64" in workflow
    assert "verify-controls" in workflow
    assert "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json" in workflow
    assert "https://epss.empiricalsecurity.com/epss_scores-current.csv.gz" in workflow
    assert "https://storage.googleapis.com/osv-vulnerabilities/modified_id.csv" in workflow
    assert workflow.index("verify-controls") < workflow.index("curl --fail")
    assert "ingest-feeds" in workflow
    assert "actions/upload-artifact" in workflow
    assert "deploy" not in workflow.lower()
