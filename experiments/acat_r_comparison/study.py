#!/usr/bin/env python3
"""ACAT-R: GNER-E1 unmodified runtime, fair same-input conventional comparison.

Revision 2 (issue #1081 delegated plan; PR #1082 Copilot + CodeRabbit findings):
  * enforces the ACTIVE rubric digest from rubric_registry.json before P1/P2
    and fails closed on mismatch, recording the predeclared digest too
    (Copilot r4428713850);
  * preserves the complete per-case reconcile() response, requires identical
    record count, id order, per-record hashes and full bytes on replay, and
    fails closed on empty or truncated worker output (Copilot r4428713900);
  * pins tools/gner_notification_e0.py, imported at load time by the runtime,
    beside the runtime and conventional-test blobs (CodeRabbit r4428742324);
  * runs the unchanged 10-case conventional suite FIRST (CodeRabbit r4428742330);
  * carries a per-case evidence class (CONTRACT_EXPLICIT / IMPLEMENTATION_DERIVED
    / PROPOSED_POLICY) from evidence_classes.json so proposed schema cases are
    never counted together with contract-derived ones (CodeRabbit r4428742321);
  * emits the independent oracle decision packet with every reviewer decision
    PENDING. No label is scored as a confirmed defect;
  * refuses to run the runtime at all (exit 2, RUBRIC_BLOCKED.json) until the
    active rubric revision is human-accepted with a named acceptor
    (Copilot r4428945870 on PR #1083).

Expected labels are proposed by the investigator, NOT independently ratified.
All canonical metadata is constructed. No live GitHub API, Gmail or credentials.
The case definitions in build() are byte-for-byte those of PR #1082 head
8481574af8adffee83fdb89250847822485e4c86 (rubric revision 1).
"""
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import unittest
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "tools/gner_verify_e1.py"
IMPORTED = ROOT / "tools/gner_notification_e0.py"
TESTS = ROOT / "tests/test_gner_verify_e1.py"
SOURCE_BLOB = "8290c51cd75c7de78a226770936a8f48766c24f0"
IMPORTED_BLOB = "e8f893a3d433f900b10c101828d1cbb013413fa6"
TEST_BLOB = "8517a93f346e31a392ed7c7234434f37b3e15237"
PINNED_BLOBS = {"tools/gner_verify_e1.py": SOURCE_BLOB,
                "tools/gner_notification_e0.py": IMPORTED_BLOB,
                "tests/test_gner_verify_e1.py": TEST_BLOB}
RUBRIC_REGISTRY = HERE / "rubric_registry.json"
EVIDENCE_CLASSES = HERE / "evidence_classes.json"
ADJUDICATION = HERE / "oracle" / "ADJUDICATION.json"
DECISIONS = ("PENDING", "ACCEPT", "REJECT", "REVISE")
REVIEWER_KINDS = ("HUMAN", "AGENT_REVIEWED_NOT_HUMAN_INDEPENDENT")
EVIDENCE_CLASS_NAMES = ("CONTRACT_EXPLICIT", "IMPLEMENTATION_DERIVED", "PROPOSED_POLICY")
DEFAULT_OUT = ROOT / "acatr-gner-evidence"
WORKER_INPUT_LIMIT = 150000
WORKER_KEYS = ("id", "state", "authority", "execution", "response")


def sha(v):
    return hashlib.sha256(v).hexdigest()


def encoded(v):
    return (json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate(cond, msg):
    if not cond:
        raise ValueError(msg)


# --------------------------------------------------------------------------- cases
def build():
    """Thirty predeclared cases. DO NOT EDIT without appending a rubric revision."""
    rows = []

    def add(n, expected, lead=None, canonical=None):
        l = {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": "humanaios-ui/operations",
             "run_id": 41085749811, "sha_prefix": "8ec744a", "workflow": "quality-baseline",
             "kind": "WORKFLOW_FAILURE_LEAD", "pr": None}
        c = {"id": 41085749811, "repository": {"full_name": "humanaios-ui/operations"},
             "head_sha": "8ec744a1cba7e7fad79b8589829fd460f4527f33",
             "name": "quality-baseline", "event": "pull_request", "status": "completed",
             "conclusion": "failure", "pull_requests": []}
        l.update(lead or {})
        c.update(canonical or {})
        rows.append({"id": n, "expected": expected, "lead": l, "canonical": c})
    add("valid_failure", "CANONICAL_VERIFIED")
    add("wrong_repo", "CONFLICT", canonical={"repository": {"full_name": "other/repo"}})
    add("wrong_run", "CONFLICT", canonical={"id": 5})
    add("wrong_sha", "CONFLICT", lead={"sha_prefix": "deadbee"})
    add("nonterminal", "ABSTAIN", canonical={"status": "in_progress", "conclusion": None})
    add("wrong_workflow", "CONFLICT", lead={"workflow": "fake-gate"})
    add("failure_claim_vs_success", "CONFLICT", canonical={"conclusion": "success"})
    add("unknown_pr", "ABSTAIN", lead={"pr": 765})
    add("valid_success", "CANONICAL_VERIFIED", lead={"kind": "NOTIFICATION_LEAD"}, canonical={"conclusion": "success"})
    add("valid_review", "CANONICAL_VERIFIED", lead={"kind": "REVIEW_LEAD", "pr": 765}, canonical={"pull_requests": [{"number": 765}]})
    add("invalid_lead_state", "CONFLICT", lead={"state": "VERIFIED"})
    add("invalid_lead_repo", "CONFLICT", lead={"repository": "forged/org"})
    add("invalid_missing_run", "ABSTAIN", lead={"run_id": None})
    add("invalid_zero_run", "ABSTAIN", lead={"run_id": 0})
    add("invalid_negative_run", "ABSTAIN", lead={"run_id": -5})
    add("invalid_canonical_sha", "CONFLICT", canonical={"head_sha": "x" * 40})
    add("invalid_canonical_repo", "CONFLICT", canonical={"repository": {}})
    add("unsupported_event", "CONFLICT", canonical={"event": "fork"})
    add("missing_workflow", "CONFLICT", canonical={"name": None})
    add("missing_prs", "ABSTAIN", lead={"pr": 765}, canonical={"pull_requests": None})
    add("other_pr", "ABSTAIN", lead={"pr": 765}, canonical={"pull_requests": [{"number": 764}]})
    add("skip_terminal", "CANONICAL_VERIFIED", lead={"kind": "NOTIFICATION_LEAD"}, canonical={"conclusion": "skipped"})
    add("neutral_terminal", "CANONICAL_VERIFIED", lead={"kind": "NOTIFICATION_LEAD"}, canonical={"conclusion": "neutral"})
    add("invalid_status", "ABSTAIN", canonical={"status": "queued"})
    add("unsupported_conclusion", "ABSTAIN", canonical={"conclusion": "action_required"})
    add("unknown_run_id_as_str", "ABSTAIN", lead={"run_id": "41085749811"})
    add("type_canonical_bool_id", "CONFLICT", lead={"run_id": 1}, canonical={"id": True})
    add("type_lead_bool_id", "ABSTAIN", lead={"run_id": True}, canonical={"id": 1})
    add("type_boolean_pr_in_canonical", "ABSTAIN", lead={"pr": 1}, canonical={"pull_requests": [{"number": True}]})
    add("type_lead_bool_pr", "ABSTAIN", lead={"pr": True}, canonical={"pull_requests": [{"number": 1}]})
    validate(len(rows) == 30 and len({c["id"] for c in rows}) == 30, "case count")
    return rows


# ------------------------------------------------------------------ frozen inputs
def load_registry(path=RUBRIC_REGISTRY):
    registry = json.loads(pathlib.Path(path).read_text())
    revisions = {r["revision"]: r for r in registry["revisions"]}
    validate(len(revisions) == len(registry["revisions"]), "duplicate rubric revision numbers")
    validate(registry["active_revision"] in revisions, "active rubric revision not in registry")
    for r in registry["revisions"]:
        validate(isinstance(r.get("human_accepted"), bool),
                 f"revision {r['revision']}: human_accepted must be a JSON boolean, got {r.get('human_accepted')!r}")
        if r["human_accepted"]:
            validate(isinstance(r.get("accepted_by"), str) and r["accepted_by"].strip()
                     and isinstance(r.get("accepted_at"), str) and r["accepted_at"].strip(),
                     f"revision {r['revision']} is marked accepted without accepted_by/accepted_at")
    return registry


def active_revision(registry):
    return next(r for r in registry["revisions"] if r["revision"] == registry["active_revision"])


def predeclared_revision(registry):
    return min(registry["revisions"], key=lambda r: r["revision"])


def enforce_rubric(rubric_bytes, registry):
    """Fail closed unless the computed digest equals the ACTIVE registered digest."""
    computed = sha(rubric_bytes)
    active = active_revision(registry)
    predeclared = predeclared_revision(registry)
    record = {"computed_rubric_sha256": computed,
              "active_revision": active["revision"],
              "active_rubric_sha256": active["rubric_sha256"],
              "active_revision_status": active["status"],
              "active_human_accepted": active.get("human_accepted") is True,
              "predeclared_revision": predeclared["revision"],
              "predeclared_rubric_sha256": predeclared["rubric_sha256"],
              "active_accepted_by": active.get("accepted_by"),
              "active_accepted_at": active.get("accepted_at"),
              "predeclared_digest_matches": computed == predeclared["rubric_sha256"],
              "active_digest_matches": computed == active["rubric_sha256"]}
    if not record["active_digest_matches"]:
        record["block_reason"] = "BLOCKED_RUBRIC_DIGEST_MISMATCH"
    elif not record["active_human_accepted"]:
        record["block_reason"] = "BLOCKED_RUBRIC_NOT_HUMAN_ACCEPTED"
    else:
        record["block_reason"] = None
    record["runtime_permitted"] = record["block_reason"] is None
    return record


def load_evidence_classes(cases, path=EVIDENCE_CLASSES):
    manifest = json.loads(pathlib.Path(path).read_text())
    classes = manifest["cases"]
    ids = [c["id"] for c in cases]
    validate(sorted(classes) == sorted(ids), "evidence class manifest must cover exactly the 30 case ids")
    for cid, row in classes.items():
        validate(row.get("evidence_class") in EVIDENCE_CLASS_NAMES, f"unknown evidence class for {cid}")
        validate(isinstance(row.get("source_ref"), str) and row["source_ref"], f"missing source_ref for {cid}")
        validate(isinstance(row.get("rationale"), str) and row["rationale"], f"missing rationale for {cid}")
    return manifest


def check_pins(root=ROOT, runner=subprocess.run):
    observed = {}
    for rel in PINNED_BLOBS:
        p = runner(["git", "hash-object", str(root / rel)], cwd=root, capture_output=True, text=True, check=True)
        observed[rel] = p.stdout.strip()
    mismatched = {k: v for k, v in observed.items() if v != PINNED_BLOBS[k]}
    validate(not mismatched, "pinned original source changed: " + json.dumps(mismatched, sort_keys=True))
    return observed


# ------------------------------------------------------------------- runtime calls
def worker():
    sys.path.insert(0, str(ROOT / "tools"))
    from gner_verify_e1 import reconcile
    data = sys.stdin.buffer.read(WORKER_INPUT_LIMIT + 1)
    if len(data) > WORKER_INPUT_LIMIT:
        raise SystemExit("worker input exceeds limit")
    cases = json.loads(data)
    results = []
    for c in cases:
        try:
            r = reconcile(c["lead"], c["canonical"])
            results.append({"id": c["id"], "state": r.get("state"), "authority": r.get("authority"),
                            "execution": r.get("execution"), "response": r})
        except Exception as exc:  # the runtime raising is itself an observation
            results.append({"id": c["id"], "state": "EXCEPTION", "authority": None,
                            "execution": None, "response": None, "error": type(exc).__name__})
    sys.stdout.buffer.write(encoded(results))


def parse_worker_output(stdout, cases):
    """Fail closed on empty, truncated, reordered, duplicated or incomplete output."""
    validate(isinstance(stdout, (bytes, bytearray)) and len(stdout) > 0, "empty worker output")
    validate(stdout.endswith(b"\n"), "truncated worker output (missing terminator)")
    try:
        rows = json.loads(stdout)
    except ValueError as exc:
        raise ValueError(f"unparseable worker output: {type(exc).__name__}") from None
    validate(isinstance(rows, list), "worker output is not a list")
    expected_ids = [c["id"] for c in cases]
    observed_ids = [r.get("id") if isinstance(r, dict) else None for r in rows]
    validate(observed_ids == expected_ids, "record count, ids or order differ from input")
    for r in rows:
        validate(all(k in r for k in WORKER_KEYS), f"record {r.get('id')} missing fields")
        if r["state"] != "EXCEPTION":
            validate(isinstance(r["response"], dict) and r["response"].get("state") == r["state"],
                     f"record {r['id']} response not preserved")
    return rows


def run_phase(cases, runner=subprocess.run):
    p = runner([sys.executable, "-I", "-S", str(pathlib.Path(__file__).resolve()), "--worker"],
               input=encoded(cases), capture_output=True, timeout=12)
    validate(p.returncode == 0, "runtime subprocess failed: " + p.stderr.decode(errors="replace")[:300])
    rows = parse_worker_output(p.stdout, cases)
    return SimpleNamespace(raw=p.stdout, rows=rows, input_hash=sha(encoded(cases)), output_hash=sha(p.stdout),
                           record_hashes=[sha(encoded(r)) for r in rows],
                           stderr_bytes=len(p.stderr), stderr_sha256=sha(p.stderr))


def assess(cases, output, classes):
    indexed = {r["id"]: r for r in output.rows}
    bad = []
    for c in cases:
        r = indexed[c["id"]]
        if r["state"] != c["expected"] or r["authority"] != "NONE" or r["execution"] != "DISABLED":
            bad.append({"id": c["id"], "expected": c["expected"],
                        "evidence_class": classes["cases"][c["id"]]["evidence_class"],
                        "observed": {"state": r["state"], "authority": r["authority"], "execution": r["execution"],
                                     "reason": (r["response"] or {}).get("reason"), "error": r.get("error")}})
    return bad


def baseline(out, root=ROOT, runner=subprocess.run):
    p = runner([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_gner_verify_e1.py", "-v"],
               cwd=root, capture_output=True, text=True, timeout=40)
    log = (p.stdout or "") + (p.stderr or "")
    (out / "conventional_existing_10.log").write_text(log)
    validate(p.returncode == 0, "pre-existing standard tests not passing")
    return {"preexisting_cases": 10, "passed": p.returncode == 0, "returncode": p.returncode,
            "log_sha256": sha(log.encode()), "ran_before_P1": True}


def fair_conventional(cases, rows, out):
    seen = {r["id"]: r for r in rows}
    cls = type("EqualWorkloadConventional", (unittest.TestCase,), {})
    for c in cases:
        def check(self, x=c):
            r = seen[x["id"]]
            self.assertEqual(r["state"], x["expected"])
            self.assertEqual(r["authority"], "NONE")
            self.assertEqual(r["execution"], "DISABLED")
        setattr(cls, "test_" + c["id"], check)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    (out / "conventional_equal_30.log").write_text(stream.getvalue())
    return sorted(t._testMethodName[5:] for t, _ in result.failures + result.errors)


# ---------------------------------------------------------------- adjudication
def load_adjudication(cases, rubric_record, path=ADJUDICATION):
    """Human decisions live here, separate from the generated PENDING template.

    Decisions are bound to one rubric: the file must name the enforced revision and the
    computed digest, so decisions recorded for an older rubric can never score a newer one
    (Copilot r4429077705).
    """
    adj = json.loads(pathlib.Path(path).read_text())
    validate(adj.get("rubric_revision") == rubric_record["active_revision"],
             f"adjudication is for rubric revision {adj.get('rubric_revision')!r}, "
             f"enforced revision is {rubric_record['active_revision']}")
    validate(adj.get("rubric_sha256") == rubric_record["computed_rubric_sha256"],
             "adjudication rubric_sha256 does not match the computed rubric digest")
    decisions = adj["decisions"]
    validate(sorted(decisions) == sorted(c["id"] for c in cases), "adjudication must cover exactly the 30 case ids")
    for cid, d in decisions.items():
        validate(d.get("decision") in DECISIONS, f"{cid}: unknown decision {d.get('decision')!r}")
        if d["decision"] != "PENDING":
            for field in ("rationale", "reviewer_identity", "contract_citation"):
                validate(isinstance(d.get(field), str) and d[field].strip(), f"{cid}: {d['decision']} requires {field}")
            validate(d.get("reviewer_kind") in REVIEWER_KINDS, f"{cid}: reviewer_kind must be one of {REVIEWER_KINDS}")
            if d["decision"] == "REVISE":
                validate(isinstance(d.get("proposed_expected_state"), str) and d["proposed_expected_state"],
                         f"{cid}: REVISE requires proposed_expected_state")
    return adj


def score_adjudication(disagreements, adjudication):
    """confirmed_defects = disagreements whose label a HUMAN reviewer ACCEPTed."""
    decisions = adjudication["decisions"]
    flagged = {x["id"] for x in disagreements}
    summary = {"decided": 0, "pending": 0, "accept_human": [], "accept_agent_only": [], "reject": [], "revise": [],
               "confirmed_defects": [], "disagreements_pending": []}
    for cid, d in sorted(decisions.items()):
        if d["decision"] == "PENDING":
            summary["pending"] += 1
            if cid in flagged:
                summary["disagreements_pending"].append(cid)
            continue
        summary["decided"] += 1
        if d["decision"] == "ACCEPT":
            key = "accept_human" if d["reviewer_kind"] == "HUMAN" else "accept_agent_only"
            summary[key].append(cid)
            if cid in flagged and key == "accept_human":
                summary["confirmed_defects"].append(cid)
        else:
            summary[d["decision"].lower()].append(cid)
    return summary


# ---------------------------------------------------------------- oracle packet
def oracle_rows(cases, output, classes, rubric_record):
    indexed = {r["id"]: r for r in output.rows}
    rows = []
    for n, c in enumerate(cases, 1):
        r = indexed[c["id"]]
        meta = classes["cases"][c["id"]]
        rows.append({"n": n, "id": c["id"],
                     "source_ref": meta["source_ref"], "contract_ref": meta.get("contract_ref"),
                     "input_sha256": sha(encoded({"lead": c["lead"], "canonical": c["canonical"]})),
                     "expected_state": c["expected"], "observed_state": r["state"],
                     "observed_reason": (r["response"] or {}).get("reason"),
                     "match": r["state"] == c["expected"],
                     "evidence_class": meta["evidence_class"], "classification_rationale": meta["rationale"],
                     "reviewer_decision": "PENDING", "reviewer_rationale": "", "reviewer_identity": "",
                     "label_review_state": "NOT_INDEPENDENTLY_REVIEWED",
                     "rubric_revision": rubric_record["active_revision"],
                     "rubric_sha256": rubric_record["active_rubric_sha256"]})
    return rows


def render_oracle_markdown(rows, meta):
    lines = ["# Independent oracle decision packet: GNER-E1 equal-workload study (issue #1081)", "",
             "Every `reviewer_decision` below is **PENDING**. The referee (human, or an agent explicitly marked",
             "AGENT_REVIEWED / NOT_HUMAN_INDEPENDENT) records ACCEPT, REJECT or REVISE per case with a contract",
             "citation **in `oracle/ADJUDICATION.json`**, not in this generated file, which is regenerated as a PENDING",
             "template by every run. A label that is not ACCEPTed by a HUMAN reviewer is never scored as a confirmed",
             "defect. Changing any label requires a new revision in `rubric_registry.json`; this packet pins the",
             "revision it was built from.", "",
             f"- Rubric revision: {meta['active_revision']} (`{meta['active_rubric_sha256']}`), status {meta['active_revision_status']}, human_accepted={meta['active_human_accepted']}",
             f"- Predeclared digest (revision {meta['predeclared_revision']}): `{meta['predeclared_rubric_sha256']}`; matches computed rubric: {meta['predeclared_digest_matches']}",
             "- Pinned sources: " + ", ".join(f"`{k}`@`{v[:12]}`" for k, v in sorted(PINNED_BLOBS.items())),
             "- Evidence classes: CONTRACT_EXPLICIT = documented or pinned by an unchanged test; IMPLEMENTATION_DERIVED = read from unchanged source only; PROPOSED_POLICY = stricter than source, not documented.", "",
             "| # | Case | Expected | Observed | Match | Evidence class | Source ref | Contract ref | Input sha256 | Decision |",
             "|--:|------|----------|----------|:-----:|----------------|------------|--------------|--------------|----------|"]
    for r in rows:
        lines.append(f"| {r['n']} | `{r['id']}` | {r['expected_state']} | {r['observed_state']} | {'yes' if r['match'] else '**NO**'} | "
                     f"{r['evidence_class']} | `{r['source_ref']}` | {('`' + r['contract_ref'] + '`') if r['contract_ref'] else 'none'} | "
                     f"`{r['input_sha256'][:16]}` | {r['reviewer_decision']} |")
    lines += ["", "## Individual decisions required (disagreements and boundary cases)", ""]
    for r in rows:
        if not r["match"] or r["evidence_class"] == "PROPOSED_POLICY" or r["id"] == "unsupported_conclusion":
            lines += [f"### {r['n']}. `{r['id']}`", "",
                      f"- Expected `{r['expected_state']}`, observed `{r['observed_state']}` (reason: {r['observed_reason']}).",
                      f"- Evidence class: **{r['evidence_class']}**. Source: `{r['source_ref']}`. Contract: {('`' + r['contract_ref'] + '`') if r['contract_ref'] else 'none cited'}.",
                      f"- Classification rationale: {r['classification_rationale']}",
                      "- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).", ""]
    lines += ["## Scoring rule", "",
              "confirmed_defects = disagreements whose label the referee ACCEPTed with a contract citation. At this",
              "revision that number is 0 because no label has been accepted. Proposed-policy disagreements are",
              "reported separately and are never added to contract-derived counts.", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------------ main
def main(out_dir=DEFAULT_OUT, registry_path=None):
    out = pathlib.Path(out_dir)
    pins = check_pins()
    registry = load_registry(registry_path or RUBRIC_REGISTRY)  # resolved at call time, not def time
    cases = build()
    rubric = encoded(cases)
    rubric_record = enforce_rubric(rubric, registry)
    classes = load_evidence_classes(cases)
    out.mkdir(exist_ok=False)
    if not rubric_record["runtime_permitted"]:
        # Issue #1081 plan: a rubric that is not the human-accepted reference blocks execution.
        blocked = dict(rubric_record, schema="humanaios.acat-r.rubric-blocked.v0.1",
                       status=rubric_record["block_reason"], pinned_git_blobs=pins,
                       evidence_class_sha256=sha(EVIDENCE_CLASSES.read_bytes()),
                       runtime_calls_made=0, conventional_suite_run=False,
                       unblock="human referee sets human_accepted=true with accepted_by/accepted_at on the active "
                               "revision in rubric_registry.json, or appends a new accepted revision",
                       authority_effect="NONE", admission="HOLD")
        (out / "RUBRIC_BLOCKED.json").write_bytes(encoded(blocked))
        print(json.dumps({"status": blocked["status"], "computed_rubric_sha256": blocked["computed_rubric_sha256"],
                          "active_rubric_sha256": blocked["active_rubric_sha256"],
                          "predeclared_rubric_sha256": blocked["predeclared_rubric_sha256"],
                          "active_human_accepted": blocked["active_human_accepted"],
                          "runtime_calls_made": 0, "admission": "HOLD"}, sort_keys=True))
        return blocked
    # adjudication is read only on the permitted path and must be bound to this exact rubric
    adjudication = load_adjudication(cases, rubric_record)
    # 1. unchanged conventional 10-case suite FIRST
    conventional_baseline = baseline(out)
    # 2. commitment before any case is sent to the runtime
    (out / "reference_proposed.json").write_bytes(rubric)
    classes_bytes = EVIDENCE_CLASSES.read_bytes()
    (out / "evidence_classes.json").write_bytes(classes_bytes)
    commitment = {"source_sha256": sha(SOURCE.read_bytes()), "imported_module_sha256": sha(IMPORTED.read_bytes()),
                  "conventional_test_sha256": sha(TESTS.read_bytes()), "pinned_git_blobs": pins,
                  "rubric_sha256": rubric_record["computed_rubric_sha256"],
                  "rubric_revision": rubric_record["active_revision"],
                  "predeclared_rubric_sha256": rubric_record["predeclared_rubric_sha256"],
                  "evidence_classes_sha256": sha(classes_bytes),
                  "P1_input_sha256": sha(encoded(cases[:8])),
                  "authority_effect": "NONE", "label_state": "PENDING_INDEPENDENT_REVIEW"}
    (out / "P1_COMMIT.json").write_bytes(encoded(commitment))
    # 3. P1, P2, P3
    p1 = run_phase(cases[:8])
    (out / "P1_stdout.json").write_bytes(p1.raw)
    p2 = run_phase(cases)
    (out / "P2_stdout.json").write_bytes(p2.raw)
    p3 = run_phase(cases)
    (out / "P3_stdout.json").write_bytes(p3.raw)
    replay = {"cases": 30, "output_sha256": p3.output_hash,
              "byte_identical": p2.raw == p3.raw,
              "record_hashes_identical": p2.record_hashes == p3.record_hashes,
              "id_order_identical": [r["id"] for r in p2.rows] == [r["id"] for r in p3.rows],
              "record_count": len(p3.rows)}
    validate(replay["byte_identical"] and replay["record_hashes_identical"] and replay["id_order_identical"],
             "same-input replay mismatch")
    # 4. equal-workload comparison
    acatr = assess(cases, p2, classes)
    conv = fair_conventional(cases, p2.rows, out)
    flags = sorted(x["id"] for x in acatr)
    validate(flags == conv, "fair comparison divergence")
    by_class = {name: sorted(x["id"] for x in acatr if x["evidence_class"] == name) for name in EVIDENCE_CLASS_NAMES}
    false_promotions = [x["id"] for x in acatr if x["expected"] != "CANONICAL_VERIFIED"
                        and x["observed"]["state"] == "CANONICAL_VERIFIED"]
    class_counts = {name: sum(1 for c in classes["cases"].values() if c["evidence_class"] == name)
                    for name in EVIDENCE_CLASS_NAMES}
    # 5. oracle packet
    rows = oracle_rows(cases, p2, classes, rubric_record)
    packet = {"schema": "humanaios.acat-r.oracle-decision-packet.v0.1", "issue": 1081,
              "rubric": rubric_record, "pinned_git_blobs": pins, "label_review_state": "NOT_INDEPENDENTLY_REVIEWED",
              "confirmed_defects": 0, "cases": rows}
    (out / "oracle_packet.json").write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    (out / "ORACLE_REVIEW_PACKET.md").write_text(render_oracle_markdown(rows, rubric_record))
    scored = score_adjudication(acatr, adjudication)
    adjudicated_rows = []
    for r in rows:
        d = adjudication["decisions"][r["id"]]
        adjudicated_rows.append(dict(r, reviewer_decision=d["decision"], reviewer_rationale=d["rationale"],
                                     reviewer_identity=d["reviewer_identity"], reviewer_kind=d.get("reviewer_kind"),
                                     contract_citation=d.get("contract_citation"),
                                     proposed_expected_state=d.get("proposed_expected_state"),
                                     label_review_state=("NOT_INDEPENDENTLY_REVIEWED" if d["decision"] == "PENDING"
                                                         else d.get("reviewer_kind"))))
    (out / "oracle_adjudicated.json").write_text(json.dumps(
        {"schema": "humanaios.acat-r.oracle-adjudicated.v0.1", "adjudication_sha256": sha(ADJUDICATION.read_bytes()),
         "rubric": rubric_record, "summary": scored, "cases": adjudicated_rows}, indent=2, sort_keys=True) + "\n")
    confirmed = len(scored["confirmed_defects"])
    # 6. report
    result = {
        "schema": "humanaios.acat-r.equal-workload.v0.2",
        "status": "PROVISIONAL_REFERENCE_LABELS_NEED_INDEPENDENT_REVIEW",
        "target": "Unmodified GNER-E1 reconcile (offline pure function)",
        "pinned_git_blobs": pins, "source_git_blob": SOURCE_BLOB, "conventional_blob": TEST_BLOB,
        "imported_module_blob": IMPORTED_BLOB, "source_sha256": commitment["source_sha256"],
        "imported_module_sha256": commitment["imported_module_sha256"],
        "rubric_sha256": rubric_record["computed_rubric_sha256"],
        "rubric_revision": rubric_record["active_revision"],
        "rubric_revision_status": rubric_record["active_revision_status"],
        "rubric_human_accepted": rubric_record["active_human_accepted"],
        "rubric_accepted_by": rubric_record["active_accepted_by"],
        "rubric_accepted_at": rubric_record["active_accepted_at"],
        "predeclared_rubric_sha256": rubric_record["predeclared_rubric_sha256"],
        "predeclared_digest_matches": rubric_record["predeclared_digest_matches"],
        "evidence_classes_sha256": commitment["evidence_classes_sha256"],
        "evidence_class_counts": class_counts,
        "execution_order": ["pin_check", "rubric_enforcement", "conventional_existing_10", "P1_commit", "P1", "P2", "P3",
                            "equal_workload_comparison", "oracle_packet"],
        "P1": {"cases": 8, "nonconformances": assess(cases[:8], p1, classes), "output_sha256": p1.output_hash,
               "stderr_bytes": p1.stderr_bytes},
        "P2": {"cases": 30, "nonconformances": acatr, "output_sha256": p2.output_hash, "stderr_bytes": p2.stderr_bytes,
               "record_hashes": p2.record_hashes},
        "P3": replay,
        "conventional_baseline": conventional_baseline,
        "conventional_equal": {"cases": 30, "detected": conv},
        "acatr_equal": {"cases": 30, "detected": flags},
        "disagreements_by_evidence_class": by_class,
        "contract_derived_disagreements": by_class["CONTRACT_EXPLICIT"] + by_class["IMPLEMENTATION_DERIVED"],
        "proposed_policy_disagreements": by_class["PROPOSED_POLICY"],
        "suspected_type_schema_false_promotions": false_promotions,
        "confirmed_defects": confirmed,
        "confirmed_defects_basis": "disagreements whose label a HUMAN reviewer ACCEPTed in oracle/ADJUDICATION.json; "
                                   "agent-only acceptances are listed but never counted",
        "adjudication_summary": scored,
        "adjudication_sha256": sha(ADJUDICATION.read_bytes()),
        "acatr_detection_advantage_on_equal_inputs": len(set(flags) - set(conv)),
        "measured_false_alarm_rate": "UNDETERMINED: oracle labels not independently approved",
        "captures_real_github_data": False, "auth_path_tested": False,
        "auth_path_note": "verify_lead() is exercised separately by live_probe.py under a human-held read-only credential; its receipts are not part of this offline run",
        "authority_effect": "NONE", "can_authorize": False, "admission": "HOLD",
        "limitations": [
            "Constructed canonical metadata; the authenticated verify_lead entry point was not tested in this run.",
            "Boolean-ID cases are proposed stricter schema checks, not proven GitHub API inputs.",
            "Reference labels written by investigator; require independent adjudication before publishing bug counts.",
            "Both methods share the same source, observations and expected labels; added detection is zero.",
            "P3 is repeated input with unchanged code, not correction, recovery or learning.",
            "The predeclared revision-0 rubric digest cannot be reproduced; revision 1 is enforced and awaits human acceptance.",
        ]}
    (out / "report.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "P1": 8, "P2": 30, "P3": 30,
                      "rubric_revision": result["rubric_revision"],
                      "predeclared_digest_matches": result["predeclared_digest_matches"],
                      "same_workload_flags": flags, "fair_conventional_flags": conv,
                      "proposed_policy_disagreements": by_class["PROPOSED_POLICY"],
                      "contract_derived_disagreements": result["contract_derived_disagreements"],
                      "false_promotions": false_promotions, "replay": replay["byte_identical"],
                      "detection_advantage": result["acatr_detection_advantage_on_equal_inputs"],
                      "confirmed_defects": confirmed, "adjudication_pending": scored["pending"],
                      "admission": "HOLD"}, sort_keys=True))
    return result


def cli(argv):
    if argv == ["--worker"]:
        worker()
        return 0
    if argv[:1] == ["--run-owned-offline"]:
        rest = argv[1:]
        out = DEFAULT_OUT
        if rest[:1] == ["--out"] and len(rest) == 2:
            out = pathlib.Path(rest[1])
        elif rest:
            raise SystemExit("Use --run-owned-offline [--out DIR] or --worker")
        result = main(out)
        return 2 if result.get("runtime_permitted") is False else 0
    raise SystemExit("Use --run-owned-offline [--out DIR] or --worker")


if __name__ == "__main__":
    raise SystemExit(cli(sys.argv[1:]))
