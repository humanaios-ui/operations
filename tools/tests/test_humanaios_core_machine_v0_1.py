"""Synthetic regressions for HumanAIOS Core Machine v0.1 (issue #810)."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import jsonschema
import pytest


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import humanaios_core_machine_v0_1 as machine
from verified_receipts import build_receipt_chain_for_testing


HEAD = "a" * 40
OLD_HEAD = "b" * 40
AUTH_ISSUER = "github-protected-review-witness"
OBSERVATION_ISSUER = "repository-coordinator-witness"
SCOPE = "issue:810/pr:999"
SUBJECT = f"repo:humanaios-ui/operations@{HEAD}"
SCHEMA_PATH = TOOLS.parent / "schemas" / "humanaios_core_machine_v0_1.schema.json"


def policy() -> dict:
    return {
        "schema_version": "0.3",
        "invariants": [
            "EVALUATION_ADMISSION_IS_NOT_IMPLEMENTATION_ACCEPTANCE",
            "ADMISSION_IS_NOT_MERGE_AUTHORITY",
        ],
        "evaluation_admission": {
            "authorized_actors": ["humanaios-ui"],
            "required_issue_state": "ADMISSION_REQUESTED",
            "authority_effect": "EVALUATION_ONLY",
            "merge_authority": False,
        },
    }


def instructions(*, full: bool = False, challenge_state: str | None = None) -> list[dict]:
    digest = machine.policy_sha256(policy())
    result = [
        {"op": "PIN_CONTEXT", "arg": {
            "program_id": "HCM-TEST", "repository": "humanaios-ui/operations",
            "subject_head_sha": HEAD, "policy_sha256": digest,
            "purpose": "evaluation-admission", "source_issue": 810,
        }},
        {"op": "OBSERVE", "arg": {
            "id": "OBS-1", "source_ref": "github:issue:810",
            "source_sha256": "1" * 64, "epistemic_state": "OBSERVED",
        }},
        {"op": "CLAIM", "arg": {
            "id": "CLAIM-1", "claim_sha256": "2" * 64,
            "evidence_ids": ["OBS-1"], "epistemic_state": "OBSERVED",
        }},
    ]
    if challenge_state is not None:
        result.append({"op": "CHALLENGE", "arg": {
            "id": "CHALLENGE-1", "claim_id": "CLAIM-1",
            "state": challenge_state,
            "evidence_ids": ["OBS-1"] if challenge_state == "RESOLVED" else [],
        }})
    result.append({"op": "WARRANT", "arg": {
        "id": "WARRANT-1", "claim_ids": ["CLAIM-1"],
        "action": "EVALUATION_ADMISSION", "scope": SCOPE,
        "reversible": True,
    }})
    if full:
        result.extend([
            {"op": "IMPORT_AUTHORITY", "arg": {
                "id": "AUTH-BINDING-1", "receipt_id": "AUTH-1",
                "warrant_id": "WARRANT-1", "min_strength": "ATTESTED",
            }},
            {"op": "RECORD_ACTION", "arg": {
                "id": "ACTION-1", "receipt_id": "ACTION-R1",
                "authorization_receipt_id": "AUTH-1", "warrant_id": "WARRANT-1",
            }},
            {"op": "RECORD_OUTCOME", "arg": {
                "id": "OUTCOME-1", "receipt_id": "OUTCOME-R1", "action_id": "ACTION-1",
            }},
        ])
    result.append({"op": "CLOSE", "arg": {}})
    return result


def source(*, full: bool = False, challenge_state: str | None = None) -> dict:
    return {
        "schema": machine.SCHEMA,
        "policy_sha256": machine.policy_sha256(policy()),
        "instructions": instructions(full=full, challenge_state=challenge_state),
    }


def auth_receipt(**changes) -> dict:
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "AUTH-1",
        "receipt_type": "HUMAN_AUTHORIZATION",
        "subject": SUBJECT,
        "action": "EVALUATION_ADMISSION",
        "scope": SCOPE,
        "issuer": AUTH_ISSUER,
        "authority_scope": "EVALUATION_ONLY",
        "verification_status": "VERIFIED",
        "verification_strength": "ATTESTED",
        "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
        "evidence_ref": "github:review:1",
        "one_time": True,
        "actor": "humanaios-ui",
        "review_state": "APPROVED",
        "source_kind": "GITHUB_PULL_REQUEST_REVIEW",
        "issue_state": "ADMISSION_REQUESTED",
        "subject_head_sha": HEAD,
        "warrant_id": "WARRANT-1",
        "merge_authority": False,
    }
    event.update(changes)
    return event


def action_receipt(**changes) -> dict:
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "ACTION-R1",
        "receipt_type": "ACTION_OBSERVATION",
        "subject": SUBJECT,
        "action": "EVALUATION_ADMISSION",
        "scope": SCOPE,
        "issuer": OBSERVATION_ISSUER,
        "authority_scope": "NONE",
        "verification_status": "VERIFIED",
        "verification_strength": "OBSERVED",
        "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
        "evidence_ref": "github:workflow:1",
        "one_time": False,
        "authorization_receipt_id": "AUTH-1",
        "warrant_id": "WARRANT-1",
        "subject_head_sha": HEAD,
        "event_state": "OBSERVED",
    }
    event.update(changes)
    return event


def outcome_receipt(**changes) -> dict:
    event = {
        "type": "RECEIPT_VERIFIED",
        "receipt_id": "OUTCOME-R1",
        "receipt_type": "OUTCOME_OBSERVATION",
        "subject": SUBJECT,
        "action": "EVALUATION_ADMISSION",
        "scope": SCOPE,
        "issuer": OBSERVATION_ISSUER,
        "authority_scope": "NONE",
        "verification_status": "VERIFIED",
        "verification_strength": "OBSERVED",
        "verification_method": "BRIDGE_EVENT_HASH_CHAIN",
        "evidence_ref": "github:workflow:outcome:1",
        "one_time": False,
        "action_receipt_id": "ACTION-R1",
        "action_id": "ACTION-1",
        "subject_head_sha": HEAD,
        "event_state": "OBSERVED",
    }
    event.update(changes)
    return event


def trust(events: list[dict] | None = None, **changes) -> machine.TrustContext:
    chained, head = build_receipt_chain_for_testing(
        events or [auth_receipt(), action_receipt(), outcome_receipt()]
    )
    values = {
        "subject_head_sha": HEAD,
        "policy_document": policy(),
        "receipt_events": tuple(chained),
        "receipt_chain_head": head,
        "authorization_issuer": AUTH_ISSUER,
        "observation_issuer": OBSERVATION_ISSUER,
    }
    values.update(changes)
    return machine.TrustContext(**values)


def compile_source(value: dict | None = None) -> bytes:
    return machine.compile_program(value or source())


def valid_digest_blob(body: bytearray) -> bytes:
    return bytes(body) + sha256(body).digest()


class TestBytecodeFormat:
    def test_source_conforms_to_public_schema(self):
        jsonschema.Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate(source(full=True))

    def test_deterministic_compile_and_round_trip(self):
        program = source()
        first = compile_source(program)
        second = compile_source(deepcopy(program))
        assert first == second
        assert first.startswith(machine.MAGIC)
        assert machine.disassemble_program(first) == program

    def test_tamper_is_rejected(self):
        blob = bytearray(compile_source())
        blob[machine.HEADER.size + 6] ^= 0x01
        with pytest.raises(machine.MachineError, match="BYTECODE_DIGEST_MISMATCH"):
            machine.decode_program(bytes(blob))

    def test_unknown_opcode_with_valid_digest_is_rejected(self):
        blob = compile_source()
        body = bytearray(blob[:-machine.TRAILER_SIZE])
        body[machine.HEADER.size] = 0x11
        with pytest.raises(machine.MachineError, match="UNKNOWN_OPCODE"):
            machine.decode_program(valid_digest_blob(body))

    def test_trailing_data_with_valid_digest_is_rejected(self):
        blob = compile_source()
        body = bytearray(blob[:-machine.TRAILER_SIZE])
        body.extend(b"x")
        with pytest.raises(machine.MachineError, match="BYTECODE_TRAILING_DATA"):
            machine.decode_program(valid_digest_blob(body))

    def test_noncanonical_float_and_raw_payload_are_rejected(self):
        with pytest.raises(machine.MachineError, match="FLOAT_NOT_CANONICAL"):
            machine.canonical_json({"score": 0.5})
        with pytest.raises(machine.MachineError, match="RAW_PAYLOAD_KEY_FORBIDDEN"):
            machine.canonical_json({"text": "sensitive payload"})

    def test_integer_and_decoder_nesting_bounds_are_enforced(self):
        with pytest.raises(machine.MachineError, match="INTEGER_OUT_OF_RANGE"):
            machine.canonical_json({"value": machine.MAX_INTEGER + 1})

        operand = (
            b'{"value":' + (b"[" * 2_000) + b"0" + (b"]" * 2_000) + b"}"
        )
        body = bytearray(
            machine.HEADER.pack(
                machine.MAGIC,
                machine.FORMAT_VERSION,
                0,
                0,
                bytes.fromhex(machine.policy_sha256(policy())),
                1,
            )
        )
        body.extend(
            machine.INSTRUCTION_HEADER.pack(
                int(machine.Opcode.PIN_CONTEXT), len(operand)
            )
        )
        body.extend(operand)
        with pytest.raises(
            machine.MachineError,
            match="JSON_DEPTH_EXCEEDED|INVALID_CANONICAL_JSON",
        ):
            machine.decode_program(valid_digest_blob(body))

    def test_context_policy_mismatch_is_rejected(self):
        program = source()
        program["instructions"][0]["arg"]["policy_sha256"] = "f" * 64
        with pytest.raises(machine.MachineError, match="POLICY_HEADER_CONTEXT_MISMATCH"):
            compile_source(program)

    def test_duplicate_object_identifier_is_rejected(self):
        program = source()
        program["instructions"][2]["arg"]["id"] = "OBS-1"
        with pytest.raises(machine.MachineError, match="DUPLICATE_OBJECT_ID"):
            compile_source(program)

    def test_reference_order_is_enforced(self):
        program = source()
        program["instructions"][1], program["instructions"][2] = (
            program["instructions"][2], program["instructions"][1]
        )
        with pytest.raises(machine.MachineError, match="CLAIM_EVIDENCE_MISSING"):
            compile_source(program)

    def test_instruction_and_string_bounds_are_enforced(self):
        program = source()
        program["instructions"][1]["arg"]["source_ref"] = "x" * (
            machine.MAX_STRING_LENGTH + 1
        )
        with pytest.raises(machine.MachineError, match="STRING_TOO_LONG"):
            compile_source(program)


class TestEpistemicBoundary:
    def test_unknown_claim_cannot_form_warrant(self):
        program = source()
        program["instructions"][2]["arg"]["epistemic_state"] = "UNKNOWN"
        with pytest.raises(machine.MachineError, match="WARRANT_CLAIM_NOT_SUPPORTED"):
            compile_source(program)

    def test_disputed_claim_cannot_form_warrant(self):
        program = source()
        program["instructions"][2]["arg"]["epistemic_state"] = "DISPUTED"
        with pytest.raises(machine.MachineError, match="WARRANT_CLAIM_NOT_SUPPORTED"):
            compile_source(program)

    def test_open_challenge_blocks_warrant(self):
        with pytest.raises(machine.MachineError, match="WARRANT_HAS_OPEN_CHALLENGE"):
            compile_source(source(challenge_state="OPEN"))

    def test_challenge_cannot_bypass_warrant_by_arriving_late(self):
        program = source()
        program["instructions"].insert(
            -1,
            {
                "op": "CHALLENGE",
                "arg": {
                    "id": "CHALLENGE-LATE",
                    "claim_id": "CLAIM-1",
                    "state": "OPEN",
                    "evidence_ids": [],
                },
            },
        )
        with pytest.raises(machine.MachineError, match="OPCODE_OUT_OF_ORDER"):
            compile_source(program)

    def test_resolved_challenge_requires_evidence(self):
        program = source(challenge_state="RESOLVED")
        program["instructions"][3]["arg"]["evidence_ids"] = []
        with pytest.raises(machine.MachineError, match="RESOLVED_CHALLENGE_NEEDS_EVIDENCE"):
            compile_source(program)

    def test_resolved_challenge_allows_warrant(self):
        receipt = machine.run_program(compile_source(source(challenge_state="RESOLVED")))
        assert receipt["status"] == "READY_FOR_EXTERNAL_AUTHORITY"
        assert receipt["counts"]["challenges"] == 1

    def test_action_sequence_requires_authority_instruction(self):
        program = source()
        program["instructions"].insert(-1, {"op": "RECORD_ACTION", "arg": {
            "id": "ACTION-1", "receipt_id": "ACTION-R1",
            "authorization_receipt_id": "AUTH-1", "warrant_id": "WARRANT-1",
        }})
        with pytest.raises(machine.MachineError, match="OPCODE_OUT_OF_ORDER"):
            compile_source(program)


class TestAuthorityBoundary:
    def test_current_repository_policy_drives_the_full_chain(self):
        current = json.loads((TOOLS.parent / "REPOSITORY_COORDINATOR_POLICY.json").read_text())
        program = source(full=True)
        digest = machine.policy_sha256(current)
        program["policy_sha256"] = digest
        program["instructions"][0]["arg"]["policy_sha256"] = digest
        result = machine.run_program(
            compile_source(program), trust(policy_document=current)
        )
        assert result["status"] == "OUTCOME_OBSERVED"

    def test_runtime_pins_are_required_for_authority_import(self):
        result = machine.run_program(compile_source(source(full=True)))
        assert result["status"] == "HALTED"
        assert "RUNTIME_TRUST_CONTEXT_REQUIRED" in result["reason_codes"]

    def test_policy_pin_mismatch_halts(self):
        changed = policy()
        changed["evaluation_admission"]["authorized_actors"] = ["another-actor"]
        result = machine.run_program(
            compile_source(source(full=True)), trust(policy_document=changed)
        )
        assert "POLICY_DIGEST_MISMATCH" in result["reason_codes"]

    def test_runtime_subject_head_mismatch_halts(self):
        result = machine.run_program(
            compile_source(source(full=True)), trust(subject_head_sha=OLD_HEAD)
        )
        assert "SUBJECT_HEAD_MISMATCH" in result["reason_codes"]

    def test_issue_comment_does_not_satisfy_human_review(self):
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(source_kind="GITHUB_ISSUE_COMMENT"),
                   action_receipt(), outcome_receipt()]),
        )
        assert "AUTHORIZATION_BINDING_REJECTED" in result["reason_codes"]

    def test_wrong_actor_is_rejected(self):
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(actor="automation-bot"), action_receipt(), outcome_receipt()]),
        )
        assert "AUTHORIZATION_BINDING_REJECTED" in result["reason_codes"]

    def test_stale_head_receipt_is_rejected(self):
        stale_subject = f"repo:humanaios-ui/operations@{OLD_HEAD}"
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(subject=stale_subject, subject_head_sha=OLD_HEAD),
                   action_receipt(), outcome_receipt()]),
        )
        assert "RECEIPT_REJECTED" in result["reason_codes"]

    def test_wrong_scope_and_warrant_are_rejected(self):
        wrong_scope = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(scope="issue:810/pr:998"), action_receipt(), outcome_receipt()]),
        )
        assert "RECEIPT_REJECTED" in wrong_scope["reason_codes"]
        wrong_warrant = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(warrant_id="WARRANT-X"), action_receipt(), outcome_receipt()]),
        )
        assert "AUTHORIZATION_BINDING_REJECTED" in wrong_warrant["reason_codes"]

    def test_consumed_one_time_authorization_is_rejected(self):
        consumed = {
            "type": "RECEIPT_CONSUMED", "by": "test",
            "receipt_id": "AUTH-1", "subject": SUBJECT,
        }
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(), consumed, action_receipt(), outcome_receipt()]),
        )
        assert "RECEIPT_REJECTED" in result["reason_codes"]

    def test_unsupported_verification_method_is_rejected(self):
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(verification_method="SELF_ASSERTED"),
                   action_receipt(), outcome_receipt()]),
        )
        assert "RECEIPT_REJECTED" in result["reason_codes"]

    def test_policy_authority_expansion_is_rejected_after_recompile(self):
        expanded = policy()
        expanded["evaluation_admission"]["merge_authority"] = True
        program = source(full=True)
        digest = machine.policy_sha256(expanded)
        program["policy_sha256"] = digest
        program["instructions"][0]["arg"]["policy_sha256"] = digest
        result = machine.run_program(
            compile_source(program), trust(policy_document=expanded)
        )
        assert "POLICY_MERGE_AUTHORITY_EXPANDED" in result["reason_codes"]


class TestObservedActionAndOutcome:
    def test_complete_chain_records_outcome_without_gaining_authority(self):
        result = machine.run_program(
            compile_source(source(full=True)), trust()
        )
        assert result["status"] == "OUTCOME_OBSERVED"
        assert result["counts"] == {
            "actions": 1,
            "authorities": 1,
            "challenges": 0,
            "claims": 1,
            "observations": 1,
            "outcomes": 1,
            "warrants": 1,
        }
        assert result["authority_effect"] == "NONE"
        assert result["can_authorize"] is False
        assert result["can_execute"] is False
        assert result["merge_authority"] is False
        assert result["authenticated"] is False
        assert result["trust_anchor_authentication"] == "EXTERNAL_TO_VM"
        jsonschema.Draft202012Validator(json.loads(SCHEMA_PATH.read_text())).validate(result)

    def test_action_observation_must_bind_authority(self):
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(), action_receipt(authorization_receipt_id="AUTH-X"),
                   outcome_receipt()]),
        )
        assert "ACTION_BINDING_REJECTED" in result["reason_codes"]

    def test_outcome_observation_must_bind_action(self):
        result = machine.run_program(
            compile_source(source(full=True)),
            trust([auth_receipt(), action_receipt(),
                   outcome_receipt(action_receipt_id="ACTION-X")]),
        )
        assert "OUTCOME_BINDING_REJECTED" in result["reason_codes"]

    def test_receipt_is_deterministic_and_contains_no_source_payload(self):
        blob = compile_source(source(full=True))
        first = machine.run_program(blob, trust())
        second = machine.run_program(blob, trust())
        assert first == second
        rendered = json.dumps(first, sort_keys=True)
        assert "sensitive payload" not in rendered
        assert set(first["bindings"]) == {
            "action_receipt_id", "authorization_receipt_id",
            "outcome_receipt_id", "warrant_id",
        }

    def test_explicit_halt_emits_non_authoritative_receipt(self):
        program = source()
        program["instructions"][-1] = {"op": "HALT", "arg": {"reason_code": "OPERATOR_STOP"}}
        result = machine.run_program(compile_source(program))
        assert result["status"] == "HALTED"
        assert "OPERATOR_STOP" in result["reason_codes"]
        assert result["authority_effect"] == "NONE"
