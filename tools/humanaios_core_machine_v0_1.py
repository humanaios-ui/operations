#!/usr/bin/env python3
"""HumanAIOS Core Machine v0.1 — deterministic governance bytecode.

Builder v1.7 compliant · validation_tool
HumanAIOS · issue #810

Compiles a bounded instruction stream for the Operations evidence chain:
context -> observation -> claim -> challenge -> warrant -> imported authority
receipt -> observed action -> observed outcome.

The virtual machine has no external-action handler.  It validates and receipts
state transitions that occurred elsewhere.  Runtime trust anchors are supplied
separately from bytecode, so a program cannot package its own sufficient trust.

Usage:
  python3 tools/humanaios_core_machine_v0_1.py --smoke-test
  python3 tools/humanaios_core_machine_v0_1.py compile --input SOURCE.json \
      --output PROGRAM.hcm
  python3 tools/humanaios_core_machine_v0_1.py disassemble --input PROGRAM.hcm
  python3 tools/humanaios_core_machine_v0_1.py run --input PROGRAM.hcm \
      --policy POLICY.json --review-snapshot REVIEWS.json \
      --subject-head SHA --receipt-ledger RECEIPTS.jsonl --receipt-head HASH \
      --authorization-issuer ISSUER --observation-issuer ISSUER
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import IntEnum
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Mapping, Sequence


TOOL_NAME = "humanaios_core_machine"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "issue-810"
TOOL_ZONE = 1

SCHEMA = "humanaios.core-machine.program.v0.1"
RECEIPT_SCHEMA = "humanaios.core-machine.receipt.v0.1"
MAGIC = b"HAIOSMC\x00"
FORMAT_VERSION = 1
HEADER = struct.Struct(">8sBBH32sI")
INSTRUCTION_HEADER = struct.Struct(">BI")
TRAILER_SIZE = 32
MAX_INSTRUCTIONS = 256
MAX_OPERAND_BYTES = 65_536
MAX_BYTECODE_BYTES = 1_048_576
MAX_JSON_DEPTH = 32
MAX_STRING_LENGTH = 8_192
MIN_INTEGER = -(1 << 63)
MAX_INTEGER = (1 << 63) - 1

DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
OPAQUE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/+\-]{0,255}\Z")
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")

FORBIDDEN_RAW_KEYS = frozenset({
    "body", "content", "email", "message", "private", "secret", "text", "token",
})
CLAIM_STATES = frozenset({"OBSERVED", "INFERRED", "UNKNOWN", "DISPUTED"})
EVIDENCE_STATES = frozenset({"OBSERVED", "ATTESTED", "UNKNOWN", "DISPUTED"})
CHALLENGE_STATES = frozenset({"OPEN", "RESOLVED"})
SUPPORTED_ACTIONS = frozenset({"EVALUATION_ADMISSION"})
STRENGTHS = frozenset({"ATTESTED", "CRYPTO_VERIFIED"})
REVIEW_STATES = frozenset({"APPROVED", "CHANGES_REQUESTED", "DISMISSED"})


class SpecLoadFailed(Exception):
    """Raised when source, bytecode, or trust input is malformed."""


class MachineError(ValueError):
    """A fail-closed compiler, decoder, or state-transition error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        suffix = f": {detail}" if detail else ""
        super().__init__(code + suffix)


class Opcode(IntEnum):
    """HumanAIOS Core Machine instruction set v0.1."""

    PIN_CONTEXT = 0x10
    OBSERVE = 0x20
    CLAIM = 0x30
    CHALLENGE = 0x40
    WARRANT = 0x50
    IMPORT_AUTHORITY = 0x60
    RECORD_ACTION = 0x70
    RECORD_OUTCOME = 0x80
    CLOSE = 0x90
    HALT = 0xFF


@dataclass(frozen=True)
class Instruction:
    """One decoded opcode and its canonical JSON operand."""

    opcode: Opcode
    operand: dict[str, Any]


@dataclass(frozen=True)
class DecodedProgram:
    """Integrity-checked bytecode plus header pins."""

    policy_sha256: str
    instructions: tuple[Instruction, ...]
    program_sha256: str


@dataclass(frozen=True)
class TrustContext:
    """Runtime-only pins sourced outside the bytecode under evaluation.

    The VM checks these values for exact binding.  Authentication of the pins'
    delivery channel belongs to the protected caller and is outside this VM.
    """

    subject_head_sha: str
    policy_document: Mapping[str, Any]
    receipt_events: tuple[Mapping[str, Any], ...]
    receipt_chain_head: str
    authorization_issuer: str
    observation_issuer: str
    review_snapshot: Mapping[str, Any] | None = None
    consumption_actor: str | None = None


def _json_value(value: Any, *, path: str = "$", depth: int = 0) -> None:
    """Validate the canonical JSON subset used by bytecode operands."""
    if depth > MAX_JSON_DEPTH:
        raise MachineError("JSON_DEPTH_EXCEEDED", path)
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if value < MIN_INTEGER or value > MAX_INTEGER:
            raise MachineError("INTEGER_OUT_OF_RANGE", path)
        return
    if isinstance(value, float):
        raise MachineError("FLOAT_NOT_CANONICAL", path)
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise MachineError("STRING_TOO_LONG", path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_value(item, path=f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise MachineError("NON_STRING_KEY", path)
            if key.lower() in FORBIDDEN_RAW_KEYS:
                raise MachineError("RAW_PAYLOAD_KEY_FORBIDDEN", f"{path}.{key}")
            _json_value(item, path=f"{path}.{key}", depth=depth + 1)
        return
    raise MachineError("NON_JSON_VALUE", path)


def canonical_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON after validating the bounded subset."""
    _json_value(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def policy_sha256(policy: Mapping[str, Any]) -> str:
    """Digest a policy document using the bytecode canonicalization rules."""
    return sha256(canonical_json(dict(policy))).hexdigest()


def _duplicates_rejected(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MachineError("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _reject_float(value: str) -> None:
    raise MachineError("FLOAT_NOT_CANONICAL", value)


def _load_json_bytes(raw: bytes) -> Any:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicates_rejected,
            parse_float=_reject_float,
            parse_constant=_reject_float,
        )
    except MachineError:
        raise
    except (UnicodeDecodeError, RecursionError, ValueError) as exc:
        raise MachineError("INVALID_CANONICAL_JSON", str(exc)) from exc
    _json_value(value)
    if canonical_json(value) != raw:
        raise MachineError("NON_CANONICAL_JSON")
    return value


def _exact_keys(
    operand: Mapping[str, Any], required: set[str], optional: set[str] | None = None
) -> None:
    optional = optional or set()
    present = set(operand)
    if missing := required - present:
        raise MachineError("OPERAND_FIELD_MISSING", ",".join(sorted(missing)))
    if extra := present - required - optional:
        raise MachineError("OPERAND_FIELD_UNEXPECTED", ",".join(sorted(extra)))


def _opaque(value: Any, field: str) -> str:
    if not isinstance(value, str) or OPAQUE_RE.fullmatch(value) is None:
        raise MachineError("INVALID_OPAQUE_ID", field)
    return value


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or DIGEST_RE.fullmatch(value) is None:
        raise MachineError("INVALID_SHA256", field)
    return value


def _commit(value: Any, field: str) -> str:
    if not isinstance(value, str) or COMMIT_RE.fullmatch(value) is None:
        raise MachineError("INVALID_COMMIT_SHA", field)
    return value


def _id_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise MachineError("NONEMPTY_ID_LIST_REQUIRED", field)
    items = [_opaque(item, field) for item in value]
    if len(items) != len(set(items)):
        raise MachineError("DUPLICATE_ID_REFERENCE", field)
    return items


def _instruction_source(raw: Any) -> Instruction:
    if not isinstance(raw, dict):
        raise MachineError("INSTRUCTION_NOT_OBJECT")
    _exact_keys(raw, {"op", "arg"})
    name, operand = raw["op"], raw["arg"]
    if not isinstance(name, str) or name not in Opcode.__members__:
        raise MachineError("UNKNOWN_OPCODE", str(name))
    if not isinstance(operand, dict):
        raise MachineError("OPERAND_NOT_OBJECT", name)
    _json_value(operand)
    return Instruction(Opcode[name], dict(operand))


def _validate_program(
    policy_digest: str, instructions: Sequence[Instruction]
) -> None:
    """Validate instruction shape, references, order, and terminal state."""
    _digest(policy_digest, "policy_sha256")
    if not instructions or len(instructions) > MAX_INSTRUCTIONS:
        raise MachineError("INSTRUCTION_COUNT_OUT_OF_RANGE")
    if instructions[0].opcode is not Opcode.PIN_CONTEXT:
        raise MachineError("PIN_CONTEXT_MUST_BE_FIRST")
    if instructions[-1].opcode not in {Opcode.CLOSE, Opcode.HALT}:
        raise MachineError("TERMINAL_OPCODE_REQUIRED")

    context: dict[str, Any] | None = None
    observations: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    challenges: dict[str, dict[str, Any]] = {}
    warrant: dict[str, Any] | None = None
    authority: dict[str, Any] | None = None
    action: dict[str, Any] | None = None
    outcome: dict[str, Any] | None = None
    all_ids: set[str] = set()
    terminal_seen = False
    stage = "START"

    allowed_by_stage = {
        "START": {Opcode.PIN_CONTEXT},
        "EVIDENCE": {Opcode.OBSERVE, Opcode.CLAIM, Opcode.HALT},
        "CLAIMS": {Opcode.CLAIM, Opcode.CHALLENGE, Opcode.WARRANT, Opcode.HALT},
        "WARRANT": {Opcode.IMPORT_AUTHORITY, Opcode.CLOSE, Opcode.HALT},
        "AUTHORITY": {Opcode.RECORD_ACTION, Opcode.CLOSE, Opcode.HALT},
        "ACTION": {Opcode.RECORD_OUTCOME, Opcode.CLOSE, Opcode.HALT},
        "OUTCOME": {Opcode.CLOSE, Opcode.HALT},
    }

    def reserve(identifier: str) -> None:
        if identifier in all_ids:
            raise MachineError("DUPLICATE_OBJECT_ID", identifier)
        all_ids.add(identifier)

    for index, instruction in enumerate(instructions):
        op, arg = instruction.opcode, instruction.operand
        if terminal_seen:
            raise MachineError("INSTRUCTION_AFTER_TERMINAL", str(index))
        if op not in allowed_by_stage[stage]:
            raise MachineError(
                "OPCODE_OUT_OF_ORDER", f"{op.name}@{index}:{stage}"
            )

        if op is Opcode.PIN_CONTEXT:
            if index != 0 or context is not None:
                raise MachineError("PIN_CONTEXT_DUPLICATED")
            _exact_keys(
                arg,
                {"program_id", "repository", "subject_head_sha", "policy_sha256", "purpose"},
                {"source_issue"},
            )
            reserve(_opaque(arg["program_id"], "program_id"))
            if not isinstance(arg["repository"], str) or REPOSITORY_RE.fullmatch(arg["repository"]) is None:
                raise MachineError("INVALID_REPOSITORY")
            _commit(arg["subject_head_sha"], "subject_head_sha")
            if _digest(arg["policy_sha256"], "policy_sha256") != policy_digest:
                raise MachineError("POLICY_HEADER_CONTEXT_MISMATCH")
            _opaque(arg["purpose"], "purpose")
            if "source_issue" in arg and (
                isinstance(arg["source_issue"], bool)
                or not isinstance(arg["source_issue"], int)
                or arg["source_issue"] <= 0
            ):
                raise MachineError("INVALID_SOURCE_ISSUE")
            context = arg
            stage = "EVIDENCE"

        elif op is Opcode.OBSERVE:
            _exact_keys(arg, {"id", "source_ref", "source_sha256", "epistemic_state"})
            identifier = _opaque(arg["id"], "observation.id")
            reserve(identifier)
            _opaque(arg["source_ref"], "source_ref")
            _digest(arg["source_sha256"], "source_sha256")
            if arg["epistemic_state"] not in EVIDENCE_STATES:
                raise MachineError("INVALID_EVIDENCE_STATE", identifier)
            observations[identifier] = arg

        elif op is Opcode.CLAIM:
            _exact_keys(arg, {"id", "claim_sha256", "evidence_ids", "epistemic_state"})
            identifier = _opaque(arg["id"], "claim.id")
            reserve(identifier)
            _digest(arg["claim_sha256"], "claim_sha256")
            evidence_ids = _id_list(arg["evidence_ids"], "evidence_ids")
            if missing := set(evidence_ids) - set(observations):
                raise MachineError("CLAIM_EVIDENCE_MISSING", ",".join(sorted(missing)))
            if arg["epistemic_state"] not in CLAIM_STATES:
                raise MachineError("INVALID_CLAIM_STATE", identifier)
            claims[identifier] = arg
            stage = "CLAIMS"

        elif op is Opcode.CHALLENGE:
            _exact_keys(arg, {"id", "claim_id", "state", "evidence_ids"})
            identifier = _opaque(arg["id"], "challenge.id")
            reserve(identifier)
            claim_id = _opaque(arg["claim_id"], "challenge.claim_id")
            if claim_id not in claims:
                raise MachineError("CHALLENGE_CLAIM_MISSING", claim_id)
            if arg["state"] not in CHALLENGE_STATES:
                raise MachineError("INVALID_CHALLENGE_STATE", identifier)
            evidence_ids = arg["evidence_ids"]
            if not isinstance(evidence_ids, list):
                raise MachineError("CHALLENGE_EVIDENCE_LIST_REQUIRED", identifier)
            checked = [_opaque(item, "challenge.evidence_ids") for item in evidence_ids]
            if len(checked) != len(set(checked)):
                raise MachineError("DUPLICATE_ID_REFERENCE", identifier)
            if missing := set(checked) - set(observations):
                raise MachineError("CHALLENGE_EVIDENCE_MISSING", ",".join(sorted(missing)))
            if arg["state"] == "RESOLVED" and not checked:
                raise MachineError("RESOLVED_CHALLENGE_NEEDS_EVIDENCE", identifier)
            challenges[identifier] = arg

        elif op is Opcode.WARRANT:
            if warrant is not None:
                raise MachineError("WARRANT_DUPLICATED")
            _exact_keys(arg, {"id", "claim_ids", "action", "scope", "reversible"})
            identifier = _opaque(arg["id"], "warrant.id")
            reserve(identifier)
            claim_ids = _id_list(arg["claim_ids"], "claim_ids")
            if missing := set(claim_ids) - set(claims):
                raise MachineError("WARRANT_CLAIM_MISSING", ",".join(sorted(missing)))
            blocked = [
                claim_id
                for claim_id in claim_ids
                if claims[claim_id]["epistemic_state"] in {"UNKNOWN", "DISPUTED"}
            ]
            if blocked:
                raise MachineError("WARRANT_CLAIM_NOT_SUPPORTED", ",".join(sorted(blocked)))
            open_claims = {
                challenge["claim_id"]
                for challenge in challenges.values()
                if challenge["state"] == "OPEN"
            }
            if open_claims & set(claim_ids):
                raise MachineError(
                    "WARRANT_HAS_OPEN_CHALLENGE",
                    ",".join(sorted(open_claims & set(claim_ids))),
                )
            if arg["action"] not in SUPPORTED_ACTIONS:
                raise MachineError("ACTION_NOT_SUPPORTED", str(arg["action"]))
            _opaque(arg["scope"], "warrant.scope")
            if not isinstance(arg["reversible"], bool):
                raise MachineError("REVERSIBILITY_BOOLEAN_REQUIRED")
            warrant = arg
            stage = "WARRANT"

        elif op is Opcode.IMPORT_AUTHORITY:
            if warrant is None:
                raise MachineError("AUTHORITY_BEFORE_WARRANT")
            if authority is not None:
                raise MachineError("AUTHORITY_DUPLICATED")
            _exact_keys(arg, {"id", "receipt_id", "warrant_id", "min_strength"})
            identifier = _opaque(arg["id"], "authority.id")
            reserve(identifier)
            _opaque(arg["receipt_id"], "authority.receipt_id")
            if arg["warrant_id"] != warrant["id"]:
                raise MachineError("AUTHORITY_WARRANT_MISMATCH")
            if arg["min_strength"] not in STRENGTHS:
                raise MachineError("AUTHORITY_STRENGTH_UNSUPPORTED")
            authority = arg
            stage = "AUTHORITY"

        elif op is Opcode.RECORD_ACTION:
            if warrant is None or authority is None:
                raise MachineError("ACTION_BEFORE_AUTHORITY")
            if action is not None:
                raise MachineError("ACTION_DUPLICATED")
            _exact_keys(
                arg,
                {"id", "receipt_id", "authorization_receipt_id", "warrant_id"},
            )
            identifier = _opaque(arg["id"], "action.id")
            reserve(identifier)
            _opaque(arg["receipt_id"], "action.receipt_id")
            if arg["authorization_receipt_id"] != authority["receipt_id"]:
                raise MachineError("ACTION_AUTHORITY_RECEIPT_MISMATCH")
            if arg["warrant_id"] != warrant["id"]:
                raise MachineError("ACTION_WARRANT_MISMATCH")
            action = arg
            stage = "ACTION"

        elif op is Opcode.RECORD_OUTCOME:
            if action is None:
                raise MachineError("OUTCOME_BEFORE_ACTION")
            if outcome is not None:
                raise MachineError("OUTCOME_DUPLICATED")
            _exact_keys(arg, {"id", "receipt_id", "action_id"})
            identifier = _opaque(arg["id"], "outcome.id")
            reserve(identifier)
            _opaque(arg["receipt_id"], "outcome.receipt_id")
            if arg["action_id"] != action["id"]:
                raise MachineError("OUTCOME_ACTION_MISMATCH")
            outcome = arg
            stage = "OUTCOME"

        elif op is Opcode.CLOSE:
            _exact_keys(arg, set())
            if warrant is None:
                raise MachineError("CLOSE_BEFORE_WARRANT")
            terminal_seen = True

        elif op is Opcode.HALT:
            _exact_keys(arg, {"reason_code"})
            _opaque(arg["reason_code"], "halt.reason_code")
            terminal_seen = True

        else:  # pragma: no cover - IntEnum construction guards this branch
            raise MachineError("UNKNOWN_OPCODE", str(op))

    if context is None or not terminal_seen:
        raise MachineError("INCOMPLETE_PROGRAM")


def compile_program(source: Mapping[str, Any]) -> bytes:
    """Compile canonical source into deterministic HumanAIOS bytecode."""
    if not isinstance(source, Mapping):
        raise MachineError("PROGRAM_NOT_OBJECT")
    source_dict = dict(source)
    _exact_keys(source_dict, {"schema", "policy_sha256", "instructions"})
    if source_dict["schema"] != SCHEMA:
        raise MachineError("PROGRAM_SCHEMA_MISMATCH")
    digest = _digest(source_dict["policy_sha256"], "policy_sha256")
    raw_instructions = source_dict["instructions"]
    if not isinstance(raw_instructions, list):
        raise MachineError("INSTRUCTIONS_NOT_LIST")
    instructions = tuple(_instruction_source(item) for item in raw_instructions)
    _validate_program(digest, instructions)

    body = bytearray(
        HEADER.pack(
            MAGIC,
            FORMAT_VERSION,
            0,
            0,
            bytes.fromhex(digest),
            len(instructions),
        )
    )
    for instruction in instructions:
        operand = canonical_json(instruction.operand)
        if len(operand) > MAX_OPERAND_BYTES:
            raise MachineError("OPERAND_TOO_LARGE", instruction.opcode.name)
        body.extend(INSTRUCTION_HEADER.pack(int(instruction.opcode), len(operand)))
        body.extend(operand)
    if len(body) + TRAILER_SIZE > MAX_BYTECODE_BYTES:
        raise MachineError("BYTECODE_TOO_LARGE")
    body.extend(sha256(body).digest())
    return bytes(body)


def decode_program(bytecode: bytes) -> DecodedProgram:
    """Verify and decode HumanAIOS bytecode."""
    if not isinstance(bytecode, bytes):
        raise MachineError("BYTECODE_NOT_BYTES")
    if len(bytecode) > MAX_BYTECODE_BYTES:
        raise MachineError("BYTECODE_TOO_LARGE")
    if len(bytecode) < HEADER.size + TRAILER_SIZE:
        raise MachineError("BYTECODE_TRUNCATED")
    body, trailer = bytecode[:-TRAILER_SIZE], bytecode[-TRAILER_SIZE:]
    if sha256(body).digest() != trailer:
        raise MachineError("BYTECODE_DIGEST_MISMATCH")

    magic, version, flags, reserved, policy_raw, count = HEADER.unpack_from(body, 0)
    if magic != MAGIC:
        raise MachineError("BYTECODE_MAGIC_MISMATCH")
    if version != FORMAT_VERSION:
        raise MachineError("BYTECODE_VERSION_UNSUPPORTED", str(version))
    if flags != 0 or reserved != 0:
        raise MachineError("BYTECODE_RESERVED_BITS_SET")
    if count == 0 or count > MAX_INSTRUCTIONS:
        raise MachineError("INSTRUCTION_COUNT_OUT_OF_RANGE")

    offset = HEADER.size
    instructions: list[Instruction] = []
    for _ in range(count):
        if offset + INSTRUCTION_HEADER.size > len(body):
            raise MachineError("INSTRUCTION_HEADER_TRUNCATED")
        opcode_value, operand_length = INSTRUCTION_HEADER.unpack_from(body, offset)
        offset += INSTRUCTION_HEADER.size
        if operand_length > MAX_OPERAND_BYTES:
            raise MachineError("OPERAND_TOO_LARGE")
        end = offset + operand_length
        if end > len(body):
            raise MachineError("OPERAND_TRUNCATED")
        try:
            opcode = Opcode(opcode_value)
        except ValueError as exc:
            raise MachineError("UNKNOWN_OPCODE", hex(opcode_value)) from exc
        operand = _load_json_bytes(body[offset:end])
        if not isinstance(operand, dict):
            raise MachineError("OPERAND_NOT_OBJECT", opcode.name)
        instructions.append(Instruction(opcode, operand))
        offset = end
    if offset != len(body):
        raise MachineError("BYTECODE_TRAILING_DATA")

    policy_digest = policy_raw.hex()
    _validate_program(policy_digest, instructions)
    return DecodedProgram(policy_digest, tuple(instructions), trailer.hex())


def disassemble_program(bytecode: bytes) -> dict[str, Any]:
    """Return canonical source reconstructed from verified bytecode."""
    program = decode_program(bytecode)
    return {
        "schema": SCHEMA,
        "policy_sha256": program.policy_sha256,
        "instructions": [
            {"op": instruction.opcode.name, "arg": instruction.operand}
            for instruction in program.instructions
        ],
    }


def _warrant_closure_sha256(program: DecodedProgram) -> str:
    """Digest the warrant and the complete evidence closure that supports it."""
    observations = {
        item.operand["id"]: item.operand
        for item in program.instructions
        if item.opcode is Opcode.OBSERVE
    }
    claims = {
        item.operand["id"]: item.operand
        for item in program.instructions
        if item.opcode is Opcode.CLAIM
    }
    challenges = [
        item.operand
        for item in program.instructions
        if item.opcode is Opcode.CHALLENGE
    ]
    warrants = [
        item.operand
        for item in program.instructions
        if item.opcode is Opcode.WARRANT
    ]
    if len(warrants) != 1:
        raise MachineError("WARRANT_CLOSURE_UNAVAILABLE")
    warrant = warrants[0]
    cited_claims = [claims[identifier] for identifier in warrant["claim_ids"]]
    evidence_ids = {
        identifier
        for claim in cited_claims
        for identifier in claim["evidence_ids"]
    }
    cited_challenges = [
        challenge
        for challenge in challenges
        if challenge["claim_id"] in warrant["claim_ids"]
    ]
    closure = {
        "observations": sorted(
            (observations[identifier] for identifier in evidence_ids),
            key=lambda item: item["id"],
        ),
        "claims": sorted(cited_claims, key=lambda item: item["id"]),
        "challenges": sorted(cited_challenges, key=lambda item: item["id"]),
        "warrant": warrant,
    }
    return sha256(canonical_json(closure)).hexdigest()


def warrant_sha256(bytecode: bytes) -> str:
    """Return the evidence-closure digest an authorization receipt must bind."""
    return _warrant_closure_sha256(decode_program(bytecode))


def _receipt_module() -> tuple[Any, Any]:
    """Load the existing pinned receipt resolver from the tools directory."""
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    from verified_receipts import ReceiptRequirement, VerifiedReceiptResolver
    return ReceiptRequirement, VerifiedReceiptResolver


def _base_receipt(
    program: DecodedProgram,
    context: Mapping[str, Any],
    *,
    status: str,
    reason_codes: Sequence[str],
    counts: Mapping[str, int],
    bindings: Mapping[str, Any] | None = None,
    receipt_chain_head: str | None = None,
    review_snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "program_id": context["program_id"],
        "repository": context["repository"],
        "subject_head_sha": context["subject_head_sha"],
        "policy_sha256": program.policy_sha256,
        "program_sha256": program.program_sha256,
        "status": status,
        "reason_codes": sorted(set(reason_codes)),
        "counts": dict(sorted(counts.items())),
        "bindings": dict(sorted((bindings or {}).items())),
        "trust_anchor_authentication": "EXTERNAL_TO_VM",
        "authority_effect": "NONE",
        "can_authorize": False,
        "can_execute": False,
        "merge_authority": False,
        "authenticated": False,
    }
    if receipt_chain_head is not None:
        body["receipt_chain_head"] = receipt_chain_head
    if review_snapshot_sha256 is not None:
        body["review_snapshot_sha256"] = review_snapshot_sha256
    body["receipt_id"] = "HCM-" + sha256(canonical_json(body)).hexdigest()[:24]
    return body


def _policy_inputs(policy: Mapping[str, Any]) -> tuple[set[str], str, str]:
    """Extract the exact evaluation-admission boundary from policy v0.3+ shape."""
    try:
        raw_invariants = policy["invariants"]
        evaluation = policy["evaluation_admission"]
        raw_actors = evaluation["authorized_actors"]
        issue_state = evaluation["required_issue_state"]
        authority_effect = evaluation["authority_effect"]
        merge_authority = evaluation["merge_authority"]
    except (KeyError, TypeError) as exc:
        raise MachineError("POLICY_SHAPE_UNSUPPORTED") from exc
    if not isinstance(raw_invariants, list) or not all(
        isinstance(item, str) for item in raw_invariants
    ):
        raise MachineError("POLICY_SHAPE_UNSUPPORTED", "invariants")
    if not isinstance(raw_actors, list) or not all(
        isinstance(item, str) for item in raw_actors
    ):
        raise MachineError("POLICY_SHAPE_UNSUPPORTED", "authorized_actors")
    invariants = set(raw_invariants)
    actors = set(raw_actors)
    required_invariants = {
        "EVALUATION_ADMISSION_IS_NOT_IMPLEMENTATION_ACCEPTANCE",
        "ADMISSION_IS_NOT_MERGE_AUTHORITY",
    }
    if not required_invariants <= invariants:
        raise MachineError("POLICY_INVARIANT_MISSING")
    if not actors or any(not isinstance(actor, str) for actor in actors):
        raise MachineError("POLICY_AUTHORIZED_ACTORS_INVALID")
    if merge_authority is not False:
        raise MachineError("POLICY_MERGE_AUTHORITY_EXPANDED")
    if issue_state != "ADMISSION_REQUESTED" or authority_effect != "EVALUATION_ONLY":
        raise MachineError("POLICY_EVALUATION_BOUNDARY_CHANGED")
    return actors, issue_state, authority_effect


def _review_snapshot_inputs(
    snapshot: Mapping[str, Any] | None,
    *,
    repository: str,
    subject_head_sha: str,
) -> tuple[str, dict[str, dict[str, Any]]]:
    """Validate a protected latest-review snapshot and return its digest/state."""
    if not isinstance(snapshot, Mapping):
        raise MachineError("REVIEW_SNAPSHOT_REQUIRED")
    snapshot_dict = dict(snapshot)
    _exact_keys(snapshot_dict, {"repository", "subject_head_sha", "reviews"})
    if snapshot_dict["repository"] != repository:
        raise MachineError("REVIEW_SNAPSHOT_REPOSITORY_MISMATCH")
    if snapshot_dict["subject_head_sha"] != subject_head_sha:
        raise MachineError("REVIEW_SNAPSHOT_HEAD_MISMATCH")
    reviews = snapshot_dict["reviews"]
    if not isinstance(reviews, list):
        raise MachineError("REVIEW_SNAPSHOT_REVIEWS_NOT_LIST")

    latest: dict[str, tuple[tuple[str, str], dict[str, Any]]] = {}
    review_ids: set[str] = set()
    for index, raw in enumerate(reviews):
        if not isinstance(raw, dict):
            raise MachineError("REVIEW_SNAPSHOT_ENTRY_NOT_OBJECT", str(index))
        _exact_keys(raw, {"review_id", "actor", "state", "submitted_at"})
        review_id = _opaque(raw["review_id"], "review_id")
        if review_id in review_ids:
            raise MachineError("REVIEW_SNAPSHOT_DUPLICATE_ID", review_id)
        review_ids.add(review_id)
        actor = _opaque(raw["actor"], "review.actor")
        if not isinstance(raw["state"], str) or raw["state"] not in REVIEW_STATES:
            raise MachineError("REVIEW_SNAPSHOT_STATE_INVALID", review_id)
        submitted_at = raw["submitted_at"]
        if not isinstance(submitted_at, str) or TIMESTAMP_RE.fullmatch(submitted_at) is None:
            raise MachineError("REVIEW_SNAPSHOT_TIMESTAMP_INVALID", review_id)
        candidate = (submitted_at, review_id)
        prior = latest.get(actor)
        if prior is None or candidate >= prior[0]:
            latest[actor] = (candidate, dict(raw))

    digest = sha256(canonical_json(snapshot_dict)).hexdigest()
    return digest, {actor: item for actor, (_, item) in latest.items()}


def _resolve_receipt(
    trust: TrustContext,
    *,
    receipt_id: str,
    receipt_type: str,
    subject: str,
    action: str,
    scope: str,
    min_strength: str,
    issuer: str,
    authority_scope: str,
    consumption_state: str = "UNCONSUMED",
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    Requirement, Resolver = _receipt_module()
    requirement = Requirement(
        receipt_type=receipt_type,
        subject=subject,
        action=action,
        scope=scope,
        min_strength=min_strength,
        issuer=issuer,
        authority_scope=authority_scope,
        consumption_state=consumption_state,
    )
    try:
        resolution = Resolver(trust.receipt_events, trust.receipt_chain_head).resolve(
            receipt_id, requirement
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise MachineError("RECEIPT_LEDGER_INVALID", type(exc).__name__) from exc
    if not resolution.valid:
        raise MachineError("RECEIPT_REJECTED", resolution.reason or "UNKNOWN")
    receipt = dict(resolution.receipt or {})
    consumption = (
        dict(resolution.consumption) if resolution.consumption is not None else None
    )
    return receipt, consumption


def run_program(bytecode: bytes, trust: TrustContext | None = None) -> dict[str, Any]:
    """Replay bytecode and emit a deterministic, non-authoritative receipt."""
    program = decode_program(bytecode)
    context = program.instructions[0].operand
    counts = {
        "observations": 0,
        "claims": 0,
        "challenges": 0,
        "warrants": 0,
        "authorities": 0,
        "actions": 0,
        "outcomes": 0,
    }
    bindings: dict[str, Any] = {}
    warrant: dict[str, Any] | None = None
    warrant_digest: str | None = None
    authority: dict[str, Any] | None = None
    authority_consumption: dict[str, Any] | None = None
    action_record: dict[str, Any] | None = None
    trusted_chain_head: str | None = None
    review_snapshot_digest: str | None = None
    latest_reviews: dict[str, dict[str, Any]] = {}
    imports_authority = any(
        item.opcode is Opcode.IMPORT_AUTHORITY for item in program.instructions
    )
    records_action = any(
        item.opcode is Opcode.RECORD_ACTION for item in program.instructions
    )

    def halted(code: str, detail: str = "") -> dict[str, Any]:
        reasons = [code]
        if detail:
            reasons.append("DETAIL_" + sha256(detail.encode("utf-8")).hexdigest()[:16])
        return _base_receipt(
            program,
            context,
            status="HALTED",
            reason_codes=reasons,
            counts=counts,
            bindings=bindings,
            receipt_chain_head=trusted_chain_head,
            review_snapshot_sha256=review_snapshot_digest,
        )

    if trust is not None:
        if not isinstance(trust.policy_document, Mapping):
            return halted("POLICY_DOCUMENT_INVALID")
        if not isinstance(trust.subject_head_sha, str):
            return halted("SUBJECT_HEAD_INVALID")
        if COMMIT_RE.fullmatch(trust.subject_head_sha) is None:
            return halted("SUBJECT_HEAD_INVALID")
        if not isinstance(trust.receipt_chain_head, str):
            return halted("RECEIPT_HEAD_INVALID")
        if DIGEST_RE.fullmatch(trust.receipt_chain_head) is None:
            return halted("RECEIPT_HEAD_INVALID")
        trusted_chain_head = trust.receipt_chain_head
        if not isinstance(trust.authorization_issuer, str):
            return halted("AUTHORIZATION_ISSUER_INVALID")
        if OPAQUE_RE.fullmatch(trust.authorization_issuer) is None:
            return halted("AUTHORIZATION_ISSUER_INVALID")
        if not isinstance(trust.observation_issuer, str):
            return halted("OBSERVATION_ISSUER_INVALID")
        if OPAQUE_RE.fullmatch(trust.observation_issuer) is None:
            return halted("OBSERVATION_ISSUER_INVALID")
        if not isinstance(trust.receipt_events, (list, tuple)) or any(
            not isinstance(event, Mapping) for event in trust.receipt_events
        ):
            return halted("RECEIPT_EVENTS_INVALID")
        try:
            trusted_policy_digest = policy_sha256(trust.policy_document)
        except (MachineError, TypeError, ValueError) as exc:
            if isinstance(exc, MachineError):
                return halted(exc.code, exc.detail)
            return halted("POLICY_DOCUMENT_INVALID", type(exc).__name__)
        if trusted_policy_digest != program.policy_sha256:
            return halted("POLICY_DIGEST_MISMATCH")
        if trust.subject_head_sha != context["subject_head_sha"]:
            return halted("SUBJECT_HEAD_MISMATCH")
        if imports_authority:
            try:
                review_snapshot_digest, latest_reviews = _review_snapshot_inputs(
                    trust.review_snapshot,
                    repository=context["repository"],
                    subject_head_sha=context["subject_head_sha"],
                )
            except MachineError as exc:
                return halted(exc.code, exc.detail)
        if records_action:
            if not isinstance(trust.consumption_actor, str):
                return halted("CONSUMPTION_ACTOR_INVALID")
            if OPAQUE_RE.fullmatch(trust.consumption_actor) is None:
                return halted("CONSUMPTION_ACTOR_INVALID")
        elif trust.consumption_actor is not None and (
            not isinstance(trust.consumption_actor, str)
            or OPAQUE_RE.fullmatch(trust.consumption_actor) is None
        ):
            return halted("CONSUMPTION_ACTOR_INVALID")

    for instruction in program.instructions[1:]:
        op, arg = instruction.opcode, instruction.operand
        if op is Opcode.OBSERVE:
            counts["observations"] += 1
        elif op is Opcode.CLAIM:
            counts["claims"] += 1
        elif op is Opcode.CHALLENGE:
            counts["challenges"] += 1
        elif op is Opcode.WARRANT:
            counts["warrants"] += 1
            warrant = arg
            warrant_digest = _warrant_closure_sha256(program)
            bindings["warrant_id"] = arg["id"]
            bindings["warrant_sha256"] = warrant_digest
        elif op is Opcode.IMPORT_AUTHORITY:
            if trust is None or warrant is None or warrant_digest is None:
                return halted("RUNTIME_TRUST_CONTEXT_REQUIRED")
            if review_snapshot_digest is None:
                return halted("REVIEW_SNAPSHOT_REQUIRED")
            try:
                actors, issue_state, authority_effect = _policy_inputs(
                    trust.policy_document
                )
                subject = f"repo:{context['repository']}@{context['subject_head_sha']}"
                consumption_state = "CONSUMED" if records_action else "UNCONSUMED"
                receipt, consumption = _resolve_receipt(
                    trust,
                    receipt_id=arg["receipt_id"],
                    receipt_type="HUMAN_AUTHORIZATION",
                    subject=subject,
                    action=warrant["action"],
                    scope=warrant["scope"],
                    min_strength=arg["min_strength"],
                    issuer=trust.authorization_issuer,
                    authority_scope=authority_effect,
                    consumption_state=consumption_state,
                )
                actor = receipt.get("actor")
                latest = latest_reviews.get(actor) if isinstance(actor, str) else None
                checks = {
                    "actor": isinstance(actor, str) and actor in actors,
                    "review_state": receipt.get("review_state") == "APPROVED",
                    "review_is_latest": receipt.get("review_is_latest") is True,
                    "latest_review_state": (
                        latest is not None and latest.get("state") == "APPROVED"
                    ),
                    "latest_review_id": (
                        latest is not None
                        and receipt.get("review_id") == latest.get("review_id")
                    ),
                    "latest_review_time": (
                        latest is not None
                        and receipt.get("review_submitted_at")
                        == latest.get("submitted_at")
                    ),
                    "review_snapshot_sha256": (
                        receipt.get("review_snapshot_sha256")
                        == review_snapshot_digest
                    ),
                    "source_kind": (
                        receipt.get("source_kind")
                        == "GITHUB_PULL_REQUEST_REVIEW"
                    ),
                    "issue_state": receipt.get("issue_state") == issue_state,
                    "subject_head_sha": (
                        receipt.get("subject_head_sha")
                        == context["subject_head_sha"]
                    ),
                    "warrant_id": receipt.get("warrant_id") == warrant["id"],
                    "warrant_sha256": (
                        receipt.get("warrant_sha256") == warrant_digest
                    ),
                    "one_time": receipt.get("one_time") is True,
                    "merge_authority": receipt.get("merge_authority") is False,
                }
                if records_action:
                    checks.update(
                        {
                            "consumption_present": consumption is not None,
                            "consumption_actor": (
                                consumption is not None
                                and consumption.get("by") == trust.consumption_actor
                            ),
                            "consumption_subject": (
                                consumption is not None
                                and consumption.get("subject") == subject
                            ),
                            "consumption_after_receipt": (
                                consumption is not None
                                and isinstance(consumption.get("seq"), int)
                                and not isinstance(consumption.get("seq"), bool)
                                and isinstance(receipt.get("seq"), int)
                                and not isinstance(receipt.get("seq"), bool)
                                and consumption["seq"] > receipt["seq"]
                            ),
                        }
                    )
                failed = sorted(key for key, value in checks.items() if not value)
                if failed:
                    raise MachineError(
                        "AUTHORIZATION_BINDING_REJECTED", ",".join(failed)
                    )
            except MachineError as exc:
                return halted(exc.code, exc.detail)
            counts["authorities"] += 1
            authority = arg
            authority_consumption = consumption
            bindings["authorization_receipt_id"] = arg["receipt_id"]
            bindings["authorization_consumption"] = consumption_state
            bindings["review_snapshot_sha256"] = review_snapshot_digest
        elif op is Opcode.RECORD_ACTION:
            if trust is None or warrant is None or authority is None:
                return halted("BOUND_AUTHORITY_REQUIRED_FOR_ACTION_RECORD")
            if warrant_digest is None or authority_consumption is None:
                return halted("AUTHORIZATION_CONSUMPTION_REQUIRED")
            try:
                subject = f"repo:{context['repository']}@{context['subject_head_sha']}"
                receipt, _ = _resolve_receipt(
                    trust,
                    receipt_id=arg["receipt_id"],
                    receipt_type="ACTION_OBSERVATION",
                    subject=subject,
                    action=warrant["action"],
                    scope=warrant["scope"],
                    min_strength="OBSERVED",
                    issuer=trust.observation_issuer,
                    authority_scope="NONE",
                )
                checks = {
                    "authorization_receipt_id": (
                        receipt.get("authorization_receipt_id")
                        == authority["receipt_id"]
                    ),
                    "warrant_id": receipt.get("warrant_id") == warrant["id"],
                    "warrant_sha256": (
                        receipt.get("warrant_sha256") == warrant_digest
                    ),
                    "subject_head_sha": (
                        receipt.get("subject_head_sha")
                        == context["subject_head_sha"]
                    ),
                    "event_state": receipt.get("event_state") == "OBSERVED",
                    "action_after_consumption": (
                        isinstance(receipt.get("seq"), int)
                        and not isinstance(receipt.get("seq"), bool)
                        and isinstance(authority_consumption.get("seq"), int)
                        and not isinstance(authority_consumption.get("seq"), bool)
                        and receipt["seq"] > authority_consumption["seq"]
                    ),
                }
                failed = sorted(key for key, value in checks.items() if not value)
                if failed:
                    raise MachineError("ACTION_BINDING_REJECTED", ",".join(failed))
            except MachineError as exc:
                return halted(exc.code, exc.detail)
            counts["actions"] += 1
            action_record = arg
            bindings["action_receipt_id"] = arg["receipt_id"]
        elif op is Opcode.RECORD_OUTCOME:
            if trust is None or warrant is None or action_record is None:
                return halted("ACTION_RECORD_REQUIRED_FOR_OUTCOME")
            try:
                subject = f"repo:{context['repository']}@{context['subject_head_sha']}"
                receipt, _ = _resolve_receipt(
                    trust,
                    receipt_id=arg["receipt_id"],
                    receipt_type="OUTCOME_OBSERVATION",
                    subject=subject,
                    action=warrant["action"],
                    scope=warrant["scope"],
                    min_strength="OBSERVED",
                    issuer=trust.observation_issuer,
                    authority_scope="NONE",
                )
                checks = {
                    "action_receipt_id": (
                        receipt.get("action_receipt_id")
                        == action_record["receipt_id"]
                    ),
                    "action_id": receipt.get("action_id") == action_record["id"],
                    "subject_head_sha": (
                        receipt.get("subject_head_sha")
                        == context["subject_head_sha"]
                    ),
                    "event_state": receipt.get("event_state") == "OBSERVED",
                }
                failed = sorted(key for key, value in checks.items() if not value)
                if failed:
                    raise MachineError("OUTCOME_BINDING_REJECTED", ",".join(failed))
            except MachineError as exc:
                return halted(exc.code, exc.detail)
            counts["outcomes"] += 1
            bindings["outcome_receipt_id"] = arg["receipt_id"]
        elif op is Opcode.HALT:
            return halted(arg["reason_code"])
        elif op is Opcode.CLOSE:
            if counts["outcomes"]:
                status = "OUTCOME_OBSERVED"
            elif counts["actions"]:
                status = "ACTION_OBSERVED"
            elif counts["authorities"]:
                status = "AUTHORIZATION_RECEIPT_BOUND"
            else:
                status = "READY_FOR_EXTERNAL_AUTHORITY"
            return _base_receipt(
                program,
                context,
                status=status,
                reason_codes=["DETERMINISTIC_REPLAY_COMPLETE"],
                counts=counts,
                bindings=bindings,
                receipt_chain_head=trusted_chain_head,
                review_snapshot_sha256=review_snapshot_digest,
            )
    return halted("TERMINAL_OPCODE_NOT_REACHED")


def write_report(output: Mapping[str, Any], destination: str | Path) -> None:
    """Write a canonical JSON receipt for an explicit CLI destination."""
    Path(destination).write_bytes(canonical_json(dict(output)) + b"\n")


def _sample_policy() -> dict[str, Any]:
    return {
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


def _sample_source(policy: Mapping[str, Any], head: str) -> dict[str, Any]:
    pd = policy_sha256(policy)
    return {
        "schema": SCHEMA,
        "policy_sha256": pd,
        "instructions": [
            {"op": "PIN_CONTEXT", "arg": {
                "program_id": "HCM-SMOKE", "repository": "humanaios-ui/operations",
                "subject_head_sha": head, "policy_sha256": pd,
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
            {"op": "WARRANT", "arg": {
                "id": "WARRANT-1", "claim_ids": ["CLAIM-1"],
                "action": "EVALUATION_ADMISSION", "scope": "issue:810/pr:999",
                "reversible": True,
            }},
            {"op": "CLOSE", "arg": {}},
        ],
    }


def run_smoke_test() -> bool:
    """Exercise deterministic compilation, tamper refusal, and safe replay."""
    try:
        policy = _sample_policy()
        source = _sample_source(policy, "a" * 40)
        first = compile_program(source)
        second = compile_program(source)
        assert first == second
        decoded = decode_program(first)
        assert decoded.policy_sha256 == policy_sha256(policy)
        assert disassemble_program(first) == source
        receipt = run_program(first)
        assert receipt["status"] == "READY_FOR_EXTERNAL_AUTHORITY"
        assert receipt["authority_effect"] == "NONE"
        assert receipt["can_authorize"] is False
        assert receipt["can_execute"] is False
        damaged = bytearray(first)
        damaged[HEADER.size] ^= 0x01
        try:
            decode_program(bytes(damaged))
        except MachineError as exc:
            assert exc.code == "BYTECODE_DIGEST_MISMATCH"
        else:
            raise AssertionError("tampered bytecode was accepted")
        print("humanaios-core-machine smoke: deterministic compile and safe replay OK")
        return True
    except Exception as exc:
        print(f"humanaios-core-machine smoke failed: {exc}", file=sys.stderr)
        return False


def _read_json(path: str) -> Any:
    try:
        return _load_json_bytes(Path(path).read_bytes())
    except OSError as exc:
        raise SpecLoadFailed(str(exc)) from exc


def _read_events(path: str) -> tuple[Mapping[str, Any], ...]:
    try:
        lines = Path(path).read_bytes().splitlines()
    except OSError as exc:
        raise SpecLoadFailed(str(exc)) from exc
    events: list[Mapping[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        event = _load_json_bytes(line)
        if not isinstance(event, dict):
            raise SpecLoadFailed("receipt ledger row is not an object")
        events.append(event)
    return tuple(events)


def _selected_path(positional: str | None, option: str | None, field: str) -> str:
    """Resolve one positional-or-option path without accepting ambiguity."""
    if positional and option:
        raise SpecLoadFailed(f"{field} supplied more than once")
    selected = option or positional
    if not selected:
        raise SpecLoadFailed(f"{field} is required")
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line compiler, disassembler, and pure replay interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("source", nargs="?")
    compile_parser.add_argument("destination", nargs="?")
    compile_parser.add_argument("--input", dest="input_path")
    compile_parser.add_argument("--output", dest="output_path")

    disassemble_parser = sub.add_parser("disassemble")
    disassemble_parser.add_argument("bytecode", nargs="?")
    disassemble_parser.add_argument("--input", dest="input_path")

    run_parser = sub.add_parser("run")
    run_parser.add_argument("bytecode", nargs="?")
    run_parser.add_argument("--input", dest="input_path")
    run_parser.add_argument("--policy", required=True)
    run_parser.add_argument("--review-snapshot")
    run_parser.add_argument("--subject-head", required=True)
    run_parser.add_argument("--receipt-ledger", required=True)
    run_parser.add_argument("--receipt-head", required=True)
    run_parser.add_argument("--authorization-issuer", required=True)
    run_parser.add_argument("--observation-issuer", required=True)
    run_parser.add_argument("--consumption-actor")
    run_parser.add_argument("--output")

    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    try:
        if args.command == "compile":
            source_path = _selected_path(args.source, args.input_path, "input")
            output_path = _selected_path(
                args.destination, args.output_path, "output"
            )
            source = _read_json(source_path)
            Path(output_path).write_bytes(compile_program(source))
            return 0
        if args.command == "disassemble":
            bytecode_path = _selected_path(
                args.bytecode, args.input_path, "input"
            )
            print(
                json.dumps(
                    disassemble_program(Path(bytecode_path).read_bytes()), indent=2
                )
            )
            return 0
        if args.command == "run":
            bytecode_path = _selected_path(
                args.bytecode, args.input_path, "input"
            )
            policy = _read_json(args.policy)
            if not isinstance(policy, dict):
                raise SpecLoadFailed("policy is not an object")
            review_snapshot = None
            if args.review_snapshot:
                review_snapshot = _read_json(args.review_snapshot)
                if not isinstance(review_snapshot, dict):
                    raise SpecLoadFailed("review snapshot is not an object")
            trust = TrustContext(
                subject_head_sha=args.subject_head,
                policy_document=policy,
                receipt_events=_read_events(args.receipt_ledger),
                receipt_chain_head=args.receipt_head,
                authorization_issuer=args.authorization_issuer,
                observation_issuer=args.observation_issuer,
                review_snapshot=review_snapshot,
                consumption_actor=args.consumption_actor,
            )
            result = run_program(Path(bytecode_path).read_bytes(), trust)
            if args.output:
                write_report(result, args.output)
            else:
                print(json.dumps(result, indent=2, sort_keys=True))
            return 0 if result["status"] != "HALTED" else 1
        parser.print_help()
        return 2
    except (MachineError, SpecLoadFailed, OSError) as exc:
        print(f"core-machine error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
