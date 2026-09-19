#!/usr/bin/env python3
"""
ACAT Merkle Auditor — v2.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-062026 (SSI/W3C Verifiable Credentials integration)

Extends v1.0 (verbatim — all three original checks unchanged):
  1. Merkle root — recomputes from phase1/phase3/corpus_state blocks
  2. Phase 1 commitment — SHA-256(session_id + sorted scores)
  3. Score integrity — flat p1_* fields vs phase1 block (D-04)

Adds in v2.0:
  4. Identity issuance — a per-instrument identifier
  5. Verifiable Credential issuance — W3C-shaped credential wrapping the
     Merkle/commitment/score-integrity result
  6. Verifiable Credential verification — re-derive and check the proof

SCOPE NOTE — read before treating this as final:
Built against the most natural reading of the ratified SSI/W3C VC
integration (referenced in HumanAIOS planning as Z2-SSI-01 through
Z2-SSI-04, migration_009, "acat_merkle_auditor_v2_0.py build scope
ratified"). The exact ratification text was NOT located in available
project knowledge at build time despite three targeted searches. This
is a best-effort implementation, not a confirmed-against-spec one.
Reconcile against the actual ratified scope before pushing to
production or treating any of the below as locked.

CRYPTOGRAPHY NOTE — the honesty constraint this file is built around:
If the `cryptography` package is importable, this issues a real Ed25519
keypair, a spec-compliant did:key identifier (multicodec 0xed01,
base58btc, per the W3C did:key method), and a real `Ed25519Signature2020`
proof. If `cryptography` is NOT available — no third-party dependency is
assumed by default, matching every other tool in this suite — this falls
back to an honestly-named, NON-standard `HumanAIOSHmacSha256Proof-v1`
proof: an HMAC-SHA256 keyed-hash, not a digital signature. The fallback
identifier is deliberately NOT formatted as a did:key string, because
the did:key multicodec prefix for Ed25519 (0xed01) asserts "this decodes
to a real Ed25519 public key" — using that prefix over non-Ed25519 data
would be a format-level overclaim, the exact failure mode this whole
instrument exists to catch elsewhere. The fallback mode is loud about
what it is not: it prints a warning, and the credential itself carries
a `non_standard_warning` field and `verification_mode: "hmac_fallback"`
so it can never be silently mistaken for cryptographic non-repudiation
it does not provide.

Usage:
  python acat_merkle_auditor_v2_0.py --input session_record.json
  python acat_merkle_auditor_v2_0.py --input session_record.json --issue-vc
  python acat_merkle_auditor_v2_0.py --smoke-test
  python acat_merkle_auditor_v2_0.py --vc-smoke-test
"""

import hashlib, hmac, json, os, sys, argparse, tempfile
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "acat_merkle_auditor"
TOOL_VERSION = "2.0.0"
CORE_6 = ["truth", "service", "harm", "autonomy", "value", "humility"]
FLAT_P1 = {"p1_truth": "truth", "p1_service": "service", "p1_harm": "harm",
           "p1_autonomy": "autonomy", "p1_value": "value", "p1_humility": "humility"}

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from cryptography.exceptions import InvalidSignature
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False


class SpecLoadFailed(Exception):
    pass


# ── v1.0 — unchanged ─────────────────────────────────────────────────────────

def load_record(path):
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SpecLoadFailed("Must be JSON object")
        return data
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"JSON error: {e}")


def _hash_block(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _merkle_root(leaves):
    nodes = list(leaves)
    if not nodes:
        return hashlib.sha256(b"empty").hexdigest()
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        parents = []
        for i in range(0, len(nodes), 2):
            parents.append(hashlib.sha256((nodes[i] + nodes[i + 1]).encode()).hexdigest())
        nodes = parents
    return nodes[0]


def verify_merkle(record):
    p1 = record.get("phase1") or {}
    p3 = record.get("phase3") or {}
    st = record.get("corpus_state") or {}
    lp1, lp3, lst = _hash_block(p1), _hash_block(p3), _hash_block(st)
    computed = _merkle_root([lp1, lp3, lst])
    stored_receipt = record.get("merkle_receipt") or {}
    stored = stored_receipt.get("merkle_root")
    if stored is None:
        return {"checked": False, "status": "NO_STORED_RECEIPT", "computed_root": computed,
                "leaf_phase1": lp1, "leaf_phase3": lp3, "leaf_state": lst,
                "note": "No merkle_receipt — use this root as baseline"}
    match = computed == stored
    return {"checked": True, "valid": match, "status": "PASS" if match else "FAIL",
             "computed_root": computed, "stored_root": stored,
             "leaf_phase1": lp1, "leaf_phase3": lp3, "leaf_state": lst,
             "failure": None if match else
                 "MERKLE_ROOT_MISMATCH: block may have been altered (D-04)."}


def _recompute_commitment(scores, session_id):
    payload = json.dumps({"session_id": session_id, "scores": dict(sorted(scores.items()))}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_commitment(record):
    sid = record.get("session_id", "")
    stored = record.get("phase1_commitment")
    p1 = record.get("phase1") or {}
    if not stored:
        return {"checked": False, "status": "NO_STORED_COMMITMENT",
                "note": "phase1_commitment absent — predates MCP v1.2"}
    scores = {}
    for d in CORE_6:
        val = p1.get(d)
        if val is not None:
            try:
                scores[d] = float(val)
            except (ValueError, TypeError):
                pass
    if len(scores) < 6:
        return {"checked": False, "status": "INSUFFICIENT_SCORES",
                "failure": f"COMMITMENT_UNVERIFIABLE: {len(scores)}/6 Core 6 scores"}
    computed = _recompute_commitment(scores, sid)
    match = computed == stored
    return {"checked": True, "valid": match, "status": "PASS" if match else "FAIL",
            "session_id": sid, "stored": stored[:16] + "...", "computed": computed[:16] + "...",
            "failure": None if match else "COMMITMENT_MISMATCH: scores altered after session open."}


def verify_score_integrity(record):
    p1 = record.get("phase1") or {}
    failures = []
    for flat, dim in FLAT_P1.items():
        fv = record.get(flat)
        bv = p1.get(dim)
        if fv is None and bv is None:
            continue
        if fv is None or bv is None:
            failures.append(f"D04_SCORE_ABSENT: {flat} vs phase1.{dim}")
            continue
        try:
            if abs(float(fv) - float(bv)) > 0.01:
                failures.append(f"D04_SCORE_MISMATCH: {flat}={fv} vs phase1.{dim}={bv}")
        except (ValueError, TypeError):
            failures.append(f"D04_SCORE_INVALID: {flat}='{fv}'")
    return {"checked": True, "valid": not failures, "status": "PASS" if not failures else "FAIL",
            "failures": failures}


def aggregate(merkle, commitment, score_integrity, session_id):
    hard = []
    if merkle.get("failure"): hard.append(merkle["failure"])
    if commitment.get("failure"): hard.append(commitment["failure"])
    hard.extend(score_integrity.get("failures", []))
    checks = [merkle, commitment, score_integrity]
    any_fail = any(c.get("status") == "FAIL" for c in checks)
    any_unc = any(not c.get("checked", True) for c in checks)
    overall = "FAIL" if any_fail else ("PARTIAL" if any_unc else "PASS")
    return {"result": overall, "status": overall, "tool": TOOL_NAME, "version": TOOL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(), "session_id": session_id,
            "hard_failures": hard, "merkle_verification": merkle,
            "commitment_verification": commitment, "score_integrity": score_integrity}


# ── v2.0 — new: base58btc (pure stdlib, no crypto needed for encoding itself) ─

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ED25519_MULTICODEC_PREFIX = bytes([0xed, 0x01])


def _base58btc_encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    chars = []
    while n > 0:
        n, rem = divmod(n, 58)
        chars.append(_B58_ALPHABET[rem])
    n_leading_zeros = len(data) - len(data.lstrip(b"\x00"))
    body = "".join(reversed(chars)) if chars else ""
    return (_B58_ALPHABET[0] * n_leading_zeros) + body


def _base58btc_decode(s: str, expected_length: int = None) -> bytes:
    n = 0
    for ch in s:
        if ch not in _B58_ALPHABET:
            raise ValueError(f"Invalid base58btc character: {ch!r}")
        n = n * 58 + _B58_ALPHABET.index(ch)
    n_leading = len(s) - len(s.lstrip(_B58_ALPHABET[0]))
    body_length = expected_length - n_leading if expected_length else (n.bit_length() + 7) // 8
    body = n.to_bytes(max(body_length, 0), "big") if n > 0 else b""
    data = (b"\x00" * n_leading) + body
    if expected_length and len(data) != expected_length:
        data = data.rjust(expected_length, b"\x00")
    return data


# ── v2.0 — new: identity issuance ────────────────────────────────────────────

def generate_identity():
    """
    Real Ed25519 + spec-compliant did:key when `cryptography` is available.
    Otherwise an honestly-non-standard placeholder identifier -- never a
    did:key string, because that would assert an Ed25519 public key this
    mode does not have.
    """
    if HAVE_CRYPTO:
        priv = Ed25519PrivateKey.generate()
        pub_bytes = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        multicodec = ED25519_MULTICODEC_PREFIX + pub_bytes
        did = "did:key:z" + _base58btc_encode(multicodec)
        return {"id": did, "id_scheme": "did:key (Ed25519, W3C did:key method)",
                "mode": "ed25519", "private_key": priv, "public_key_bytes": pub_bytes}
    else:
        salt = os.urandom(32)
        placeholder = hashlib.sha256(salt).hexdigest()[:32]
        ident = f"urn:humanaios:acat-instrument-id:{placeholder}"
        return {"id": ident,
                "id_scheme": "HumanAIOS placeholder URN — NOT did:key, NOT a public key",
                "mode": "hmac_fallback", "private_key": salt, "public_key_bytes": None}


# ── v2.0 — new: Verifiable Credential issuance + verification ──────────────

def issue_credential(session_id, aggregate_result, identity):
    subject = {
        "session_id": session_id,
        "merkle_root": aggregate_result["merkle_verification"].get("computed_root"),
        "merkle_status": aggregate_result["merkle_verification"].get("status"),
        "commitment_status": aggregate_result["commitment_verification"].get("status"),
        "score_integrity_status": aggregate_result["score_integrity"].get("status"),
        "overall_result": aggregate_result["result"],
    }
    issuance_date = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(subject, sort_keys=True).encode("utf-8")

    if identity["mode"] == "ed25519":
        signature = identity["private_key"].sign(payload)
        proof = {
            "type": "Ed25519Signature2020",
            "verificationMethod": identity["id"],
            "created": issuance_date,
            "proofValue": "z" + _base58btc_encode(signature),
        }
        verification_mode = "ed25519"
    else:
        mac = hmac.new(identity["private_key"], payload, hashlib.sha256).hexdigest()
        proof = {
            "type": "HumanAIOSHmacSha256Proof-v1",
            "verificationMethod": identity["id"],
            "created": issuance_date,
            "proofValue": mac,
            "non_standard_warning": (
                "This is an HMAC keyed-hash, not a digital signature. It proves the "
                "credential matches what was issued under this locally-held key "
                "material. It does NOT provide third-party-verifiable non-repudiation "
                "the way a real asymmetric signature (e.g. Ed25519Signature2020) would. "
                "Only the holder of the original key material can verify this proof."
            ),
        }
        verification_mode = "hmac_fallback"

    return {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", "ACATSessionIntegrityCredential"],
        "issuer": identity["id"],
        "issuanceDate": issuance_date,
        "credentialSubject": subject,
        "proof": proof,
        "verification_mode": verification_mode,
    }


def verify_credential(vc, private_key_for_hmac=None, public_key_for_ed25519=None):
    proof = vc.get("proof", {})
    proof_type = proof.get("type")
    payload = json.dumps(vc.get("credentialSubject", {}), sort_keys=True).encode("utf-8")

    if proof_type == "Ed25519Signature2020":
        if not HAVE_CRYPTO:
            return {"checked": False, "status": "UNVERIFIABLE",
                    "reason": "cryptography package not available in this environment; "
                              "cannot verify an Ed25519Signature2020 proof here."}
        if public_key_for_ed25519 is None:
            return {"checked": False, "status": "UNVERIFIABLE",
                    "reason": "No public key supplied for verification."}
        try:
            sig_b58 = proof["proofValue"]
            sig_b58 = sig_b58[1:] if sig_b58.startswith("z") else sig_b58
            signature = _base58btc_decode(sig_b58, expected_length=64)
            public_key_for_ed25519.verify(signature, payload)
            return {"checked": True, "status": "PASS"}
        except InvalidSignature:
            return {"checked": True, "status": "FAIL", "reason": "Ed25519 signature did not verify."}
        except Exception as e:
            return {"checked": True, "status": "FAIL", "reason": f"Verification error: {e}"}

    elif proof_type == "HumanAIOSHmacSha256Proof-v1":
        if private_key_for_hmac is None:
            return {"checked": False, "status": "UNVERIFIABLE",
                    "reason": "HMAC verification requires the original key material, which "
                              "by design only the issuer holds. Not supplied here."}
        expected = hmac.new(private_key_for_hmac, payload, hashlib.sha256).hexdigest()
        match = hmac.compare_digest(expected, proof.get("proofValue", ""))
        return {"checked": True, "status": "PASS" if match else "FAIL",
                "failure": None if match else "HMAC_PROOF_MISMATCH: credential subject altered "
                                               "after issuance, or wrong key material supplied."}
    else:
        return {"checked": False, "status": "UNVERIFIABLE", "reason": f"Unrecognized proof type: {proof_type!r}"}


# ── Reporting ─────────────────────────────────────────────────────────────────

def write_report(output, output_dir):
    p = Path(output_dir); p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sid = str(output.get("session_id", "unknown")).replace("/", "-")
    path = p / f"merkle_audit_v2_{sid}_{ts}.json"
    path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    return str(path)


def print_summary(output, vc=None):
    b = "=" * 60
    print(f"\n{b}")
    print(f" ACAT Merkle Auditor · {TOOL_VERSION}")
    print(f" Session: {output.get('session_id', 'unknown')}")
    print(f" Result:  {output['result']}")
    print(b)

    def sym(r):
        return "✓" if r.get("status") == "PASS" else ("–" if not r.get("checked", True) else "✗")

    mk = output["merkle_verification"]; cm = output["commitment_verification"]; si = output["score_integrity"]
    cr = mk.get("computed_root", "")[:12] + "..." if mk.get("computed_root") else ""
    print(f"  {sym(mk)} Merkle root    : {mk['status']}  {cr}")
    print(f"  {sym(cm)} Commitment     : {cm['status']}")
    print(f"  {sym(si)} Score integrity: {si['status']}")
    if output["hard_failures"]:
        print(f"\n  FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"]:
            print(f"  ✗ {f[:80]}")
    if vc is not None:
        mode = vc.get("verification_mode")
        marker = "🔐 Ed25519Signature2020 (real signature)" if mode == "ed25519" \
            else "⚠ HumanAIOSHmacSha256Proof-v1 (NOT a digital signature — see non_standard_warning)"
        print(f"\n  Credential issued · {marker}")
        print(f"  Issuer: {vc.get('issuer')}")
    print(f"\n{b}\n")


# ── Smoke tests ───────────────────────────────────────────────────────────────

def run_smoke_test():
    """v1.0's original smoke test, unchanged, run against this file's own functions."""
    p1_scores = {"truth": 84.0, "service": 86.0, "harm": 85.0, "autonomy": 87.0, "value": 85.0, "humility": 83.0}
    sid = "S-062026-smoke"
    commitment = _recompute_commitment(p1_scores, sid)
    p1b = dict(p1_scores); p1b["li"] = 0.85
    p3b = {"truth": 86.0, "service": 87.0, "harm": 86.0, "autonomy": 88.0, "value": 86.0, "humility": 84.0, "li": 1.01}
    stb = {"n_total": 629, "n_phase1": 516, "mean_li": 0.8632}
    root = _merkle_root([_hash_block(p1b), _hash_block(p3b), _hash_block(stb)])
    record = {"session_id": sid, "phase1_commitment": commitment, "phase1": p1b, "phase3": p3b,
              "corpus_state": stb, "merkle_receipt": {"merkle_root": root},
              "p1_truth": 84.0, "p1_service": 86.0, "p1_harm": 85.0,
              "p1_autonomy": 87.0, "p1_value": 85.0, "p1_humility": 83.0}
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(record, f); tmp = f.name
        loaded = load_record(tmp); os.unlink(tmp)
        mk = verify_merkle(loaded); cm = verify_commitment(loaded); si = verify_score_integrity(loaded)
        out = aggregate(mk, cm, si, sid)
        assert out["result"] == "PASS", out["hard_failures"]
        print("✓ Smoke test (v1.0 checks) PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test (v1.0 checks) FAILED: {e}")
        return False


def run_vc_smoke_test():
    """New in v2.0: validates identity issuance + credential issue/verify, both modes,
    against synthetic known-good and known-bad fixtures. Run before trusting any
    credential this tool issues."""
    print(f"\nacat_merkle_auditor v{TOOL_VERSION} — VC layer self-test")
    print(f"cryptography package available: {HAVE_CRYPTO}\n")
    all_ok = True

    def report(name, ok):
        nonlocal all_ok
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    fake_aggregate = {
        "result": "PASS",
        "merkle_verification": {"computed_root": "abc123", "status": "PASS"},
        "commitment_verification": {"status": "PASS"},
        "score_integrity": {"status": "PASS"},
    }

    # base58btc round-trip — pure encoding correctness, independent of crypto availability
    for test_bytes in (b"\x00\x01\x02hello world", os.urandom(64), b"\x00\x00\x00"):
        encoded = _base58btc_encode(test_bytes)
        decoded = _base58btc_decode(encoded, expected_length=len(test_bytes))
        report(f"base58btc round-trip ({len(test_bytes)} bytes)", decoded == test_bytes)

    # HMAC fallback path — always exercised regardless of cryptography availability,
    # since the fallback must work correctly on its own.
    hmac_identity = {"id": "urn:humanaios:acat-instrument-id:testfixture",
                      "id_scheme": "test", "mode": "hmac_fallback",
                      "private_key": b"fixed-test-key-material", "public_key_bytes": None}
    vc_hmac = issue_credential("S-test-hmac", fake_aggregate, hmac_identity)
    report("HMAC credential has non-standard proof type (not falsely Ed25519Signature2020)",
           vc_hmac["proof"]["type"] == "HumanAIOSHmacSha256Proof-v1")
    res = verify_credential(vc_hmac, private_key_for_hmac=hmac_identity["private_key"])
    report("HMAC credential verifies PASS with correct key", res["status"] == "PASS")

    tampered = json.loads(json.dumps(vc_hmac))
    tampered["credentialSubject"]["overall_result"] = "FAIL"
    res = verify_credential(tampered, private_key_for_hmac=hmac_identity["private_key"])
    report("HMAC credential detects tampered subject", res["status"] == "FAIL")

    res = verify_credential(vc_hmac, private_key_for_hmac=b"wrong-key-material")
    report("HMAC credential fails with wrong key", res["status"] == "FAIL")

    res = verify_credential(vc_hmac)  # no key supplied at all
    report("HMAC credential is UNVERIFIABLE with no key supplied (not a false PASS)",
           res["status"] == "UNVERIFIABLE")

    # Ed25519 path — only exercised if the real library is present. Honest skip otherwise.
    if HAVE_CRYPTO:
        ed_identity = generate_identity()
        report("Identity issuance produces a real did:key when cryptography is available",
               ed_identity["mode"] == "ed25519" and ed_identity["id"].startswith("did:key:z"))
        vc_ed = issue_credential("S-test-ed25519", fake_aggregate, ed_identity)
        report("Ed25519 credential correctly typed as Ed25519Signature2020",
               vc_ed["proof"]["type"] == "Ed25519Signature2020")
        res = verify_credential(vc_ed, public_key_for_ed25519=ed_identity["private_key"].public_key())
        report("Ed25519 credential verifies PASS with correct public key", res["status"] == "PASS")

        tampered_ed = json.loads(json.dumps(vc_ed))
        tampered_ed["credentialSubject"]["overall_result"] = "FAIL"
        res = verify_credential(tampered_ed, public_key_for_ed25519=ed_identity["private_key"].public_key())
        report("Ed25519 credential detects tampered subject", res["status"] == "FAIL")

        other_identity = generate_identity()
        res = verify_credential(vc_ed, public_key_for_ed25519=other_identity["private_key"].public_key())
        report("Ed25519 credential fails verification against the wrong public key",
               res["status"] == "FAIL")
    else:
        print("  [SKIP] Ed25519 path — `cryptography` not installed in this environment.")
        ident = generate_identity()
        report("Identity issuance correctly falls back to a non-did:key placeholder URN",
               ident["mode"] == "hmac_fallback" and not ident["id"].startswith("did:key"))

    print(f"\nVC self-test {'PASSED' if all_ok else 'FAILED'}")
    return all_ok


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ACAT Merkle Auditor v2.0 (+ SSI/VC layer)")
    parser.add_argument("--input", "-i")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--issue-vc", action="store_true",
                         help="Also issue a Verifiable Credential wrapping the audit result.")
    parser.add_argument("--smoke-test", action="store_true", help="Run v1.0's original three-check smoke test.")
    parser.add_argument("--vc-smoke-test", action="store_true", help="Run the new VC-layer self-test.")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if args.vc_smoke_test:
        sys.exit(0 if run_vc_smoke_test() else 1)
    if not args.input:
        parser.print_help(); sys.exit(1)

    try:
        record = load_record(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr); sys.exit(2)

    mk = verify_merkle(record); cm = verify_commitment(record); si = verify_score_integrity(record)
    out = aggregate(mk, cm, si, record.get("session_id", "unknown"))

    vc = None
    if args.issue_vc:
        if not HAVE_CRYPTO:
            print("WARNING: `cryptography` package not available — issuing credential with a "
                  "non-standard HMAC proof, NOT a real digital signature. Install `cryptography` "
                  "for a spec-compliant did:key identifier and Ed25519Signature2020 proof.",
                  file=sys.stderr)
        identity = generate_identity()
        vc = issue_credential(out["session_id"], out, identity)
        out["verifiable_credential"] = vc
        if identity["mode"] == "hmac_fallback":
            out["_hmac_key_material_hex_DO_NOT_COMMIT"] = identity["private_key"].hex()

    rp = write_report(out, args.output)
    print_summary(out, vc=vc)
    print(f"Report: {rp}")
    sys.exit(0 if out["result"] in ("PASS", "PARTIAL") else 1)


if __name__ == "__main__":
    main()
