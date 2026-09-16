#!/usr/bin/env python3
"""intent_os_test_harness — run every check the Intent-OS control surface rests on, and say which held.
Builder v1.7 compliant · validation_tool
HumanAIOS · S-091626-01

The board (ui/intent-os-humanaios-v3_3.html) has one rule: a step turns green when a fetch verified it,
not when someone says it is done. This harness applies the same rule to the *system* the board sits on.
It runs a fixed registry of commands — tool self-tests, governance integrity checks, a real HTTP round
trip through tools/decision_relay.py, the CI unit suites, and the cross-repo registry checks — records
exit code, duration and output tail for each, and writes one JSON receipt. The dashboard
(ui/intent-os-test-dashboard-v1_0.html) renders only from that receipt; it cannot turn anything green
on its own.

Tiers (docs/INTENT_OS_TEST_PATHWAY.md):
  T0  self-tests          every tool proves its own classifications fire (--self-test / --smoke-test)
  T1  governance          live integrity: inbox, signatures, manifests, document control, board seals
  T2  board + relay       board script parses; relay answers a signed /decide → /ratify over a socket;
                          a browser keeps taps across reload
  T3  ci gates            the unit suites and type-check CI runs (skipped here when a dep is absent)
  T4  cross-repo          zone registry, planned repos, and the repository index name real paths

Statuses: PASS · FAIL · SKIP (a named requirement is absent; listed, never counted green) · TIMEOUT · ERROR.
Verdict GREEN only if at least one check PASSED and none FAILED / TIMED OUT / ERRORED. An empty or
all-SKIP run is RED — "nothing checked" must never read as green.

Usage:
  python3 tools/intent_os_test_harness_v1_0.py                 # run everything, table, write receipt
  python3 tools/intent_os_test_harness_v1_0.py --tier T0 T1    # subset
  python3 tools/intent_os_test_harness_v1_0.py --list          # the registry
  python3 tools/intent_os_test_harness_v1_0.py --render        # run + inject the receipt into the dashboard
  python3 tools/intent_os_test_harness_v1_0.py --json          # receipt to stdout
  python3 tools/intent_os_test_harness_v1_0.py --self-test

Exit 0 = GREEN. Exit 2 = RED. No network. Writes only outputs/intent_os_test_results.json and, with
--render, the RESULTS block of the dashboard. Deps: git on PATH; pyyaml; optional pytest/mypy/playwright.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as _dt
import hashlib
import hmac
import importlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

TOOL_NAME = "intent_os_test_harness"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "S-091626-01"
TOOL_ZONE = 1  # 1=execute, 2=ratify, 3=night

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join("ui", "intent-os-humanaios-v3_3.html")
DASHBOARD = os.path.join("ui", "intent-os-test-dashboard-v1_0.html")
CHECKER = os.path.join("tools", "intent_os_board_check_v1_0.py")
RELAY = os.path.join("tools", "decision_relay.py")
RECEIPT = os.path.join("outputs", "intent_os_test_results.json")
SCHEMA = "intentos/test_results_v1"
BAD = {"FAIL", "TIMEOUT", "ERROR"}

TIERS = [
    ("T0", "self-tests", "every tool proves its own classifications fire"),
    ("T1", "governance integrity", "inbox, signatures, manifests, document control, board seals — live"),
    ("T2", "board + relay", "script parses; signed /decide → /ratify over a socket; taps survive reload"),
    ("T3", "ci gates", "the unit suites, lint and type-check the workflows block on"),
    ("T4", "cross-repo", "zone registry, planned repos, repository index name real paths"),
]

PY = sys.executable or "python3"


def _py(*args: str) -> list[str]:
    return [PY, *args]


# ---------------------------------------------------------------------------------------------------
# registry — every entry is a command or a native check; `proves` names diagram nodes on the dashboard
# ---------------------------------------------------------------------------------------------------
def registry() -> list[dict]:
    T = []

    def add(id, tier, area, name, cmd=None, *, expect=0, timeout=120, requires=(), needs_cmd=(),
            env=None, kind="cmd", proves=(), note=""):
        T.append(dict(id=id, tier=tier, area=area, name=name, cmd=cmd, expect=expect, timeout=timeout,
                      requires=list(requires), needs_cmd=list(needs_cmd), env=env or {}, kind=kind,
                      proves=list(proves), note=note))

    # T0 — self-tests
    add("t0-board-check", "T0", "board", "board seal checker self-test", _py(CHECKER, "--self-test"), proves=["W1", "W8"])
    add("t0-relay", "T0", "relay", "decision relay self-test (DRY_RUN)", _py(RELAY, "--self-test"), env={"DRY_RUN": "1"}, proves=["W2", "W4", "Z3"])
    add("t0-z1-validate", "T0", "governance", ".z1-control/validate.py smoke", _py(".z1-control/validate.py", "--smoke-test"), proves=["G1"])
    add("t0-z1-render", "T0", "governance", ".z1-control/render.py smoke", _py(".z1-control/render.py", "--smoke-test"), proves=["W6"])
    add("t0-z1-ratify", "T0", "governance", ".z1-control/ratify.py smoke", _py(".z1-control/ratify.py", "--smoke-test"), proves=["G2", "W5"])
    add("t0-tc-scan", "T0", "tools", ".tool-control/scan.py smoke", _py(".tool-control/scan.py", "--smoke-test"), proves=["G3"])
    add("t0-tc-validate", "T0", "tools", ".tool-control/validate.py smoke", _py(".tool-control/validate.py", "--smoke-test"), proves=["G3"])
    add("t0-tc-render", "T0", "tools", ".tool-control/render.py smoke", _py(".tool-control/render.py", "--smoke-test"), proves=["G3"])
    add("t0-tc-selftest", "T0", "tools", ".tool-control/selftest.py smoke", _py(".tool-control/selftest.py", "--smoke-test"), proves=["G3"])
    add("t0-dc-render", "T0", "docs", ".doc-control/render.py smoke", _py(".doc-control/render.py", "--smoke-test"), proves=["G3"])
    add("t0-dc-review", "T0", "docs", ".doc-control/review.py smoke", _py(".doc-control/review.py", "--smoke-test"), proves=["G3"])
    add("t0-doc-lifecycle", "T0", "docs", "doc_lifecycle_lint self-test", _py("tools/doc_lifecycle_lint.py", "--self-test"), proves=["G3"])
    add("t0-cascade-guard", "T0", "governance", "cascade_guard self-test", _py("tools/cascade_guard.py", "--self-test"), proves=["G1"])
    add("t0-jester", "T0", "governance", "jester_invariants self-test", _py("tools/jester_invariants.py", "--self-test"), proves=["G1"])
    add("t0-echoes", "T0", "tools", "echoes copilot/ACAT scanner self-test", _py("tools/echoes_copilot_acat_scanner_v0_1.py", "--self-test"))
    add("t0-behavioral", "T0", "ci", "behavioral_compliance_gate smoke", _py("tools/behavioral_compliance_gate_v1_0.py", "--smoke-test"), proves=["G4"])
    add("t0-findings-validator", "T0", "governance", "registered_findings_validator smoke", _py("tools/registered_findings_validator_v1_0.py", "--smoke-test"), proves=["G1"])

    # T1 — governance integrity (live)
    add("t1-board-holds", "T1", "board", "board seals HOLD against the tree", _py(CHECKER), proves=["W1", "W8"])
    add("t1-z1-inbox", "T1", "governance", "z1-inbox/INDEX.yaml integrity (z2 gate ERROR step)", _py(".z1-control/validate.py"), proves=["Z1", "G1", "W6"])
    add("t1-z1-render-sync", "T1", "governance", "Z1_INBOX_INDEX.md in sync (z2 gate ERROR step)", _py(".z1-control/render.py", "--check"), proves=["W6"])
    add("t1-signatures", "T1", "governance", "recorded Z2 signatures still match their candidates", _py(".z1-control/ratify.py", "--verify"), proves=["Z2", "G2", "W5"])
    add("t1-manifest-fresh", "T1", "tools", "tool manifest up to date", _py(".tool-control/scan.py", "--check"), proves=["G3"])
    add("t1-manifest-valid", "T1", "tools", "tool manifest rules hold", _py(".tool-control/validate.py"), proves=["G3"])
    add("t1-manifest-rendered", "T1", "tools", "TOOLS_MANIFEST.md in sync", _py(".tool-control/render.py", "--check"), proves=["G3"])
    add("t1-blocking-conditions", "T1", "tools", ".tool-control/selftest.py (31 blocking conditions)", _py(".tool-control/selftest.py"), proves=["G3"])
    add("t1-doc-registry", "T1", "docs", "document registry rules hold", _py(".doc-control/validate.py"), proves=["G3"])
    add("t1-doc-rendered", "T1", "docs", "CONTROLLED_DOCUMENTS.md in sync", _py(".doc-control/render.py", "--check"), proves=["G3"])
    add("t1-doc-review", "T1", "docs", "review schedule derives its own due dates", _py(".doc-control/review.py", "--check"), proves=["G3"])
    add("t1-yaml", "T1", "governance", "INDEX.yaml · tools-manifest.yaml · document-registry.yaml parse", kind="yaml", proves=["G1", "G3"])
    add("t1-graph", "T1", "governance", "system_graph.json: every edge endpoint is a node", kind="graph")
    add("t1-molt", "T1", "governance", "molt_cycle read-only pass over the NF ledger", _py("molt_cycle.py", "--read-only", "--nf", "ledgers/NF_LEDGER.jsonl"))
    add("t1-repo-health", "T1", "ci", "repo_health --strict (quality-baseline step)", _py("tools/repo_health.py", "--strict"), proves=["G4"])
    add("t1-findings-registry", "T1", "governance", "REGISTERED.md integrity (findings-registry-gate ERROR step)", kind="findings", timeout=300, proves=["G1"])
    add("t1-ic-scope-refuses", "T1", "governance", "ic_scope_check refuses without a signing secret (fail-closed)", _py("tools/ic_scope_check.py", "intake_template.jsonl"), expect=2,
        env={"IC_SCOPE_SECRET": ""}, note="exit 2 is the correct answer: no $IC_SCOPE_SECRET → REFUSE (the variable is cleared for this row)")

    # T2 — board + relay end to end
    add("t2-board-script", "T2", "board", "board <script> parses (node --check)", kind="node_check", needs_cmd=["node"], proves=["W1"])
    add("t2-dashboard-script", "T2", "board", "dashboard <script> parses (node --check)", kind="node_check_dashboard", needs_cmd=["node"], proves=["W1"])
    add("t2-relay-roundtrip", "T2", "relay", "signed /decide → PENDING hash → /ratify → signature, over HTTP (DRY_RUN)", kind="relay_roundtrip", timeout=60,
        proves=["W2", "W3", "W4", "W5", "W6", "Z3"])
    add("t2-browser-persist", "T2", "board", "headless Chromium: board renders; a tap survives reload (localStorage)", kind="browser", timeout=90,
        requires=["playwright"], proves=["W1"])

    # T3 — CI gates (what the workflows run)
    # MUST match the pytest step in .github/workflows/quality-baseline.yml, in
    # content if not in order. This list had already drifted from it once —
    # missing both suites added by PR #343 — which made the harness report a
    # pass CI would not have given. tools/tests/test_ci_suite_enumeration.py
    # now asserts the two agree, and that every file under tools/tests/ is on
    # them; add to both places or that guard goes red.
    baseline = ["tools/tests/test_assess_router_structure.py",
                "tools/tests/test_behavioral_compliance_gate.py",
                "tools/tests/test_ci_suite_enumeration.py",
                "tools/tests/test_clone_sync_health.py",
                "tools/tests/test_intake_schema_v0_2.py",
                "tools/tests/test_orchestrator_molt.py",
                "tools/tests/test_pre_push_gate.py",
                "tools/tests/test_registry_site_generator.py",
                "tools/tests/test_tool_gap_scaffolds.py",
                "test_specimen_intake_evaluator.py",
                "test_specimen_intake_nf_ledger.py", "tools/tests/test_molt_cycle_nf_read.py",
                "test_resource_economics.py", "tools/tests/test_builder_compliance_scanner.py",
                "tools/tests/test_molt_tier_classifier.py",
                "tools/tests/test_ratify_index_write.py",
                "tools/tests/test_smag_predict_lint.py", "tools/tests/test_smag_feedback.py",
                "tools/tests/test_nf_ledger_cli.py", "tools/tests/test_ci_predict.py",
                "tools/tests/test_lifecycle_predict.py", "tools/tests/test_dimension_attribution.py",
                "tools/tests/test_tool_trace_hook.py", "tools/tests/test_tool_trace_reader.py",
                "tools/tests/test_copilot_acat_scanner.py", "acat/tests/test_tool_trace_schema.py"]
    pyt = ["-m", "pytest", "-q", "--no-header", "-p", "no:cacheprovider"]
    add("t3-pytest-baseline", "T3", "ci", "pytest baseline suites (quality-baseline blocking step)", _py(*pyt, *baseline), timeout=600,
        requires=["pytest", "cryptography.hazmat.primitives.hashes"], proves=["G4"])
    add("t3-pytest-research", "T3", "ci", "pytest tests/ (research scenarios)", _py(*pyt, "tests"), timeout=600, requires=["pytest"], proves=["G4"])
    add("t3-pytest-tools", "T3", "ci", "pytest tools/tests/", _py(*pyt, "tools/tests"), timeout=600,
        requires=["pytest", "cryptography.hazmat.primitives.hashes"], proves=["G4"])
    add("t3-pytest-acat", "T3", "ci", "pytest acat/tests/", _py(*pyt, "acat/tests"), timeout=600,
        requires=["pytest", "fastapi", "jsonschema"], proves=["G4"])
    add("t3-mypy", "T3", "ci", "python3 -m mypy src/humanaios_operations (quality-baseline blocking step)",
        _py("-m", "mypy", "src/humanaios_operations", "--ignore-missing-imports"), timeout=600, requires=["mypy"], proves=["G4"])
    add("t3-ruff", "T3", "ci", "python3 -m ruff check --select=E9,F63,F7,F82 (quality-baseline blocking step)",
        _py("-m", "ruff", "check", "--select=E9,F63,F7,F82", "src/humanaios_operations", "acat/api/services", "tools/tests", "tests"),
        timeout=300, requires=["ruff"], proves=["G4"])

    # T4 — cross-repo scale-out
    add("t4-zone-registry", "T4", "registry", "ZONE_REGISTRY.md: tables populated; operations registered ACTIVE", kind="zones", proves=["R1"])
    add("t4-planned-repos", "T4", "registry", "PLANNED_REPOS.md present with ≥1 planned row", kind="planned", proves=["R1"])
    add("t4-repo-index", "T4", "registry", "REPOSITORY_STRUCTURE.md: every path it names exists", kind="repo_index", proves=["R2"])
    return T


# ---------------------------------------------------------------------------------------------------
# native checks
# ---------------------------------------------------------------------------------------------------
def _ok(lines: list[str], cond: bool, label: str) -> bool:
    lines.append(f"  {label:<62} {'OK' if cond else 'FAIL'}")
    return bool(cond)


def check_yaml(root: str) -> tuple[bool, str]:
    import yaml  # noqa: E402
    out, ok = [], True
    for p in ("z1-inbox/INDEX.yaml", "tools-manifest.yaml", "document-registry.yaml"):
        try:
            yaml.safe_load(open(os.path.join(root, p), encoding="utf-8"))
            ok &= _ok(out, True, p)
        except Exception as e:  # noqa: BLE001
            ok &= _ok(out, False, f"{p}: {e}")
    return ok, "\n".join(out)


def check_graph(root: str) -> tuple[bool, str]:
    """system_graph.json v0.2 keeps `nodes` as {id: node} and edges as {source, target}; accept a list
    of nodes and from/to as well so a regenerated graph with either shape is still checked."""
    g = json.load(open(os.path.join(root, "system_graph.json"), encoding="utf-8"))
    nodes = g.get("nodes", {})
    ids = set(nodes.keys()) if isinstance(nodes, dict) else {n.get("id") for n in nodes}
    edges = g.get("edges", [])
    ends = [(e.get("source", e.get("from")), e.get("target", e.get("to"))) for e in edges]
    dangling = [f"{a}→{b}" for a, b in ends if a not in ids or b not in ids]
    out = [f"  nodes={len(ids)} edges={len(edges)} dangling={len(dangling)}"] + [f"    DANGLING {d}" for d in dangling[:20]]
    return (len(ids) > 0 and len(edges) > 0 and not dangling), "\n".join(out)


def check_findings(root: str, timeout: int) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(_py("tools/registered_findings_validator_v1_0.py", "--input", "REGISTERED.md", "--output", td),
                           cwd=root, capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def extract_script(html_path: str) -> str:
    src = open(html_path, encoding="utf-8").read()
    m = re.search(r"<script>(.*?)</script>", src, re.S)
    if not m:
        raise ValueError("no <script> block")
    return m.group(1)


def check_node(root: str, rel: str, timeout: int) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as td:
        js = os.path.join(td, "script.js")
        open(js, "w", encoding="utf-8").write(extract_script(os.path.join(root, rel)))
        r = subprocess.run(["node", "--check", js], capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, (r.stdout + r.stderr).strip() or f"  {rel}: script parses"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


MIN_INDEX = ('---\nversion: 1\ngenerated: "2026-09-14"\ndecision_window_days: 2\ncounts: {candidates: 1, records: 0}\n'
             'ratifiers: [Night]\n\ncandidates:\n  - q_id: Q-BOARD-RULING-06\n    title: "Board ruling d6"\n'
             '    path: "z1-inbox/2026-09-14/Q-BOARD-RULING-06.md"\n    submitted: "2026-09-14"\n    status: awaiting_z2\n'
             '    falsifier_waiver: "question"\n\nrecords:\nexcluded: []\n')
MIN_CAND = ("# Ruling request Q-BOARD-RULING-06\n\n## Question\n\nbatch source?\n\n## Ruling\n\nchoice:\nby:\nat:\n"
            "status: OPEN\n\n## Z2 Review Checklist\n\n- [ ] batch source?\n")


def relay_roundtrip(root: str, timeout: int) -> tuple[bool, str]:
    """Start the real relay (DRY_RUN) on a loopback port over a fixture inbox and drive the board's
    exact request shapes through the socket: preflight, bad signature, /decide, replay, wrong hash,
    /ratify, second /ratify. Then verify the signature with .z1-control/ratify.py --verify."""
    td = tempfile.mkdtemp(prefix="intentos_relay_rt_")
    lines, ok, proc = [], True, None
    try:
        os.makedirs(os.path.join(td, "tools"))
        shutil.copy(os.path.join(root, RELAY), os.path.join(td, "tools", "decision_relay.py"))
        shutil.copytree(os.path.join(root, ".z1-control"), os.path.join(td, ".z1-control"))
        os.makedirs(os.path.join(td, "z1-inbox", "2026-09-14"))
        real = os.path.join(root, "z1-inbox", "2026-09-14", "Q-BOARD-RULING-06.md")
        cand = open(real, encoding="utf-8").read() if os.path.isfile(real) else MIN_CAND
        open(os.path.join(td, "z1-inbox", "2026-09-14", "Q-BOARD-RULING-06.md"), "w", encoding="utf-8").write(cand)
        open(os.path.join(td, "z1-inbox", "INDEX.yaml"), "w", encoding="utf-8").write(MIN_INDEX)
        lines.append(f"  fixture: {'real' if cand is not MIN_CAND else 'minimal'} Q-BOARD-RULING-06 · minimal INDEX.yaml · real .z1-control/")

        secret = hashlib.sha256(os.urandom(16)).hexdigest()[:24]
        port = _free_port()
        env = {**os.environ, "DRY_RUN": "1", "RELAY_SECRET": secret, "RELAY_RATIFIER": "Night", "GITHUB_TOKEN": ""}
        proc = subprocess.Popen(_py(os.path.join(td, "tools", "decision_relay.py"), str(port)), cwd=td, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        base = f"http://127.0.0.1:{port}"

        def req(method: str, path: str, body: dict | None = None, sig: str | None = None):
            data = json.dumps(body).encode() if body is not None else None
            r = urllib.request.Request(base + path, data=data, method=method)
            if data is not None:
                r.add_header("Content-Type", "application/json")
                r.add_header("X-Sig", sig if sig is not None else hmac.new(secret.encode(), data, hashlib.sha256).hexdigest())
            try:
                with urllib.request.urlopen(r, timeout=10) as resp:
                    raw = resp.read()
                    return resp.status, dict(resp.headers), (json.loads(raw) if raw else {})
            except urllib.error.HTTPError as e:
                raw = e.read()
                try:
                    return e.code, dict(e.headers), json.loads(raw)
                except Exception:  # noqa: BLE001
                    return e.code, dict(e.headers), {"raw": raw.decode(errors="replace")}

        deadline = time.time() + 15
        up = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            try:
                code, _, j = req("GET", "/")
                up = code == 200 and j.get("relay") == "ok"
                if up:
                    break
            except Exception:  # noqa: BLE001
                time.sleep(0.15)
        if not up:
            log = proc.stdout.read() if proc.stdout else ""
            return False, "\n".join(lines + ["  relay did not come up", log[-800:]])
        ok &= _ok(lines, j.get("dry") is True and "z1-inbox" in str(j.get("lands_in")), f"GET / → relay ok · dry · lands_in {j.get('lands_in')}")
        ok &= _ok(lines, j.get("signs_as") == "Night", "signs_as comes from the relay's own environment (Night)")

        code, hdr, _ = req("OPTIONS", "/decide")
        allow = {k.lower(): v for k, v in hdr.items()}.get("access-control-allow-headers", "")
        ok &= _ok(lines, code == 204 and "authorization" in allow.lower(), f"OPTIONS /decide → {code}; Allow-Headers carries Authorization (browser preflight)")

        d = {"id": "d6", "q": "batch source?", "choice": "own postings", "tagline": "Night", "project": "HumanAIOS",
             "epoch": time.time(), "nonce": "n-" + os.urandom(6).hex()}
        code, _, j = req("POST", "/decide", d, sig="00")
        ok &= _ok(lines, code == 401 and j.get("status") == "REFUSED", f"POST /decide bad X-Sig → {code} {j.get('status')}")
        code, _, j = req("POST", "/decide", d)
        ok &= _ok(lines, code == 200 and j.get("status") == "PENDING" and re.fullmatch(r"[0-9a-f]{64}", j.get("hash", "") or ""),
                  f"POST /decide signed → {code} {j.get('status')} · hash {str(j.get('hash', ''))[:16]}")
        pend = j
        code, _, j = req("POST", "/decide", d)
        ok &= _ok(lines, code == 409, f"replay of the same nonce → {code} {j.get('status')}")
        landed = os.path.join(td, "relay_out", pend.get("path", ""))
        ok &= _ok(lines, os.path.isfile(landed) and "status: PENDING" in open(landed, encoding="utf-8").read(),
                  f"choice written into {pend.get('path')} as PENDING (local copy, repo untouched)")
        ok &= _ok(lines, not os.path.exists(os.path.join(root, "relay_out")), "no relay_out/ created under the repository")

        r = {**d, "expected_hash": pend.get("hash"), "branch": pend.get("branch"), "epoch": time.time(), "nonce": "n-" + os.urandom(6).hex(), "hash": "deadbeef"}
        code, _, j = req("POST", "/ratify", r)
        ok &= _ok(lines, j.get("status") == "REFUSED", f"POST /ratify wrong hash → {j.get('status')}")
        r = {**r, "epoch": time.time(), "nonce": "n-" + os.urandom(6).hex(), "hash": pend.get("hash")}
        code, _, j = req("POST", "/ratify", r)
        ok &= _ok(lines, code == 200 and j.get("status") == "RATIFIED" and re.fullmatch(r"[0-9a-f]{64}", j.get("signature", "") or ""),
                  f"POST /ratify echoed hash → {j.get('status')} · signature {str(j.get('signature', ''))[:16]}")
        rat = j
        out = os.path.join(td, "relay_out")
        idx = open(os.path.join(out, "z1-inbox", "INDEX.yaml"), encoding="utf-8").read() if os.path.isfile(os.path.join(out, "z1-inbox", "INDEX.yaml")) else ""
        ruling_p = os.path.join(out, rat.get("ruling", "") or "x")
        ruling = open(ruling_p, encoding="utf-8").read() if os.path.isfile(ruling_p) else ""
        ok &= _ok(lines, "status: ratified" in idx and rat.get("signature", "") in idx, "INDEX.yaml: candidate ratified, signature recorded")
        ok &= _ok(lines, rat.get("signature", "") in ruling, f"{rat.get('ruling')}: signature appended")
        ok &= _ok(lines, os.path.isfile(os.path.join(out, "Z1_INBOX_INDEX.md")), "Z1_INBOX_INDEX.md regenerated")
        # the same verifier the z2 gate runs, over the landed copy
        if not os.path.isdir(os.path.join(out, ".z1-control")):
            shutil.copytree(os.path.join(td, ".z1-control"), os.path.join(out, ".z1-control"))
        v = subprocess.run(_py(os.path.join(out, ".z1-control", "ratify.py"), "--verify"), cwd=out, capture_output=True, text=True, timeout=30)
        ok &= _ok(lines, v.returncode == 0, f".z1-control/ratify.py --verify on the landed copy → {(v.stdout + v.stderr).strip().splitlines()[-1][:60] if (v.stdout + v.stderr).strip() else 'rc ' + str(v.returncode)}")
        r = {**r, "epoch": time.time(), "nonce": "n-" + os.urandom(6).hex()}

        def snapshot() -> dict[str, bytes]:
            """Every file under the landed copy, so a refusal that touches anything is caught."""
            s = {}
            for dp, _, fns in os.walk(out):
                for fn in fns:
                    fp = os.path.join(dp, fn)
                    s[os.path.relpath(fp, out)] = open(fp, "rb").read()
            return s
        before = snapshot()
        code, _, j = req("POST", "/ratify", r)
        after = snapshot()
        ok &= _ok(lines, j.get("status") == "REFUSED" and before == after, f"second /ratify → {j.get('status')}, {len(after)} landed files byte-identical")
    except Exception as e:  # noqa: BLE001
        ok = False
        lines.append(f"  exception: {type(e).__name__}: {e}")
    finally:
        if proc is not None:
            proc.kill()
            with contextlib.suppress(Exception):
                proc.wait(timeout=5)
        shutil.rmtree(td, ignore_errors=True)
    return ok, "\n".join(lines)


def browser_persist(root: str, timeout: int) -> tuple[bool, str]:
    from playwright.sync_api import sync_playwright  # noqa: E402
    lines, ok = [], True
    url = "file://" + os.path.abspath(os.path.join(root, BOARD))
    with sync_playwright() as p:
        browser = None
        for kw in ({}, {"executable_path": "/opt/pw-browsers/chromium"}):
            try:
                browser = p.chromium.launch(**kw)
                break
            except Exception as e:  # noqa: BLE001
                lines.append(f"  launch {kw or 'default'} failed: {str(e).splitlines()[0][:90]}")
        if browser is None:
            return False, "\n".join(lines)
        ctx = browser.new_context()
        page = ctx.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_selector("#rail .block", timeout=timeout * 1000)
        n = page.locator("#rail .block").count()
        ok &= _ok(lines, n >= 1, f"board renders: {n} pipeline steps")
        ok &= _ok(lines, not errors, f"no page errors ({len(errors)})")
        note = page.locator("#persistnote").inner_text()
        ok &= _ok(lines, "local" in note, f"persistence note: {note[:60]}")
        # as a person would: tap the last step on the rail (opens its card), then its checkbox
        step = page.locator("#rail .block").last
        step.click(timeout=10000)
        did = page.locator(".card.open input[data-d]").first.get_attribute("data-d")
        cb = page.locator(f'input[data-d="{did}"]')
        was = cb.is_checked()
        cb.click(timeout=10000)
        page.reload()
        page.wait_for_selector("#rail .block", timeout=timeout * 1000)
        now = page.locator(f'input[data-d="{did}"]').is_checked()
        ok &= _ok(lines, now != was, f"step {did} tap survives reload ({was} → {now})")
        ok &= _ok(lines, page.locator("#rail .block").last.get_attribute("class").split()[-1] == ("done" if now else page.locator("#rail .block").last.get_attribute("class").split()[-1]),
                  f"rail step {did} shows {'green (done)' if now else 'its own state'} after reload")
        page.locator("#rail .block").last.click(timeout=10000)
        page.locator(f'input[data-d="{did}"]').click(timeout=10000)  # restore the tap
        ok &= _ok(lines, page.locator(f'input[data-d="{did}"]').is_checked() == was, "tap restored; nothing left behind in localStorage")
        durl = "file://" + os.path.abspath(os.path.join(root, DASHBOARD))
        if os.path.isfile(os.path.join(root, DASHBOARD)):
            errors.clear()
            page.goto(durl)
            page.wait_for_selector("#verdict", timeout=timeout * 1000)
            v = page.locator("#verdict").inner_text()
            ok &= _ok(lines, bool(v.strip()) and not errors, f"dashboard renders · verdict badge '{v.strip()[:20]}' · errors {len(errors)}")
        ctx.close()
        browser.close()
    return ok, "\n".join(lines)


def _md_tables(md: str) -> dict[str, list[list[str]]]:
    """{section heading: rows} for every pipe table under a '## ' heading (header + separator dropped)."""
    out: dict[str, list[list[str]]] = {}
    head, rows = None, []
    for ln in md.splitlines():
        if ln.startswith("## "):
            if head is not None:
                out[head] = rows
            head, rows = ln[3:].strip(), []
        elif head is not None and ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) or not any(cells):
                continue
            rows.append(cells)
    if head is not None:
        out[head] = rows
    return out


def check_zones(root: str) -> tuple[bool, str]:
    md = open(os.path.join(root, "ZONE_REGISTRY.md"), encoding="utf-8").read()
    t = _md_tables(md)
    lines, ok = [], True

    def rows(prefix: str) -> list[list[str]]:
        for k, v in t.items():
            if k.lower().startswith(prefix):
                return v[1:] if v and v[0] and v[0][0].lower().startswith("zone id") else v
        return []
    active, limited, ro, planned = rows("active"), rows("limited"), rows("read-only"), rows("planned")
    ok &= _ok(lines, len(active) >= 1, f"active zones table: {len(active)} rows")
    ok &= _ok(lines, len(limited) >= 1, f"limited-cap table: {len(limited)} rows")
    ok &= _ok(lines, len(ro) >= 1, f"read-only table: {len(ro)} rows")
    ok &= _ok(lines, len(planned) >= 1, f"planned table: {len(planned)} rows")
    ops = [r for r in active if len(r) > 1 and r[1] == "operations"]
    # whole-word token: "✅ ACTIVE" passes, "INACTIVE" does not
    ok &= _ok(lines, bool(ops) and "ACTIVE" in re.findall(r"[A-Z]+", " ".join(ops[0])), "operations is registered in the active table as ACTIVE")
    ids = [r[0] for r in active + limited + ro if r]
    ok &= _ok(lines, len(ids) == len(set(ids)), f"zone ids unique across tables ({len(ids)})")
    return ok, "\n".join(lines)


def check_planned(root: str) -> tuple[bool, str]:
    p = os.path.join(root, "PLANNED_REPOS.md")
    if not os.path.isfile(p):
        return False, "  PLANNED_REPOS.md: missing"
    t = _md_tables(open(p, encoding="utf-8").read())
    rows = [r for v in t.values() for r in v[1:]]
    planned = [r for r in rows if "PLANNED" in re.findall(r"[A-Z]+", " ".join(r))]
    return len(planned) >= 1, f"  PLANNED_REPOS.md: {len(t)} table(s), {len(rows)} rows, {len(planned)} marked PLANNED"


# A backticked token is a path claim when it looks like one: starts with a letter, digit or dot, contains
# only path characters, and has a "/" or a "." somewhere — so `.github/CODEOWNERS`, `ui/registry_viewer.jsx`
# and `.gitignore` are claims; `--self-test`, `Q-ID`, `python3` and anything with spaces or `<…>` are not.
PATH_RE = re.compile(r"`([A-Za-z0-9.][A-Za-z0-9_./-]*)`")


def index_path_claims(src: str) -> list[str]:
    out = set()
    for m in PATH_RE.finditer(src):
        n = m.group(1)
        if ("/" in n or "." in n) and not n.endswith(".") and not n.startswith(("http", "sha256")) and n not in (".", ".."):
            out.add(n)
    return sorted(out)


def check_repo_index(root: str) -> tuple[bool, str]:
    p = os.path.join(root, "REPOSITORY_STRUCTURE.md")
    if not os.path.isfile(p):
        return False, "  REPOSITORY_STRUCTURE.md: missing"
    src = open(p, encoding="utf-8").read()
    names = index_path_claims(src)
    missing = [n for n in names if not os.path.exists(os.path.join(root, n))]
    lines = [f"  paths named in backticks: {len(names)} · exist: {len(names) - len(missing)} · missing: {len(missing)}"]
    lines += [f"    MISSING {m}" for m in missing[:40]]
    return not missing and len(names) > 0, "\n".join(lines)


# ---------------------------------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------------------------------
def _have_module(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:  # noqa: BLE001
        return False


def run_one(t: dict, root: str) -> dict:
    res = {k: t[k] for k in ("id", "tier", "area", "name", "expect", "kind", "proves", "note")}
    res["cmd"] = " ".join(t["cmd"]) if t.get("cmd") else f"<native:{t['kind']}>"
    missing = [m for m in t["requires"] if not _have_module(m)] + [c for c in t["needs_cmd"] if not shutil.which(c)]
    if missing:
        res.update(status="SKIP", rc=None, duration_s=0.0, tail="", reason="requires " + ", ".join(missing))
        return res
    t0 = time.time()
    try:
        if t["kind"] == "cmd":
            r = subprocess.run(t["cmd"], cwd=root, env={**os.environ, **t["env"]}, capture_output=True, text=True, timeout=t["timeout"])
            rc, out = r.returncode, (r.stdout + r.stderr)
            status = "PASS" if rc == t["expect"] else "FAIL"
        else:
            fn = {"yaml": lambda: check_yaml(root), "graph": lambda: check_graph(root),
                  "findings": lambda: check_findings(root, t["timeout"]),
                  "node_check": lambda: check_node(root, BOARD, t["timeout"]),
                  "node_check_dashboard": lambda: check_node(root, DASHBOARD, t["timeout"]),
                  "relay_roundtrip": lambda: relay_roundtrip(root, t["timeout"]),
                  "browser": lambda: browser_persist(root, t["timeout"]),
                  "zones": lambda: check_zones(root), "planned": lambda: check_planned(root),
                  "repo_index": lambda: check_repo_index(root)}[t["kind"]]
            good, out = fn()
            rc, status = (0 if good else 2), ("PASS" if good else "FAIL")
    except subprocess.TimeoutExpired as e:
        rc, status, out = None, "TIMEOUT", f"timed out after {t['timeout']}s\n" + ((e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""))
    except FileNotFoundError as e:
        rc, status, out = None, "ERROR", f"could not launch: {e}"
    except Exception as e:  # noqa: BLE001
        rc, status, out = None, "ERROR", f"{type(e).__name__}: {e}"
    tail = "\n".join(out.strip().splitlines()[-12:])
    res.update(status=status, rc=rc, duration_s=round(time.time() - t0, 2), tail=tail[-2400:], reason="")
    return res


def worktree_tree_hash(root: str) -> str | None:
    """Tree hash of the working tree as git would commit it, with the dashboard and outputs/ removed —
    the two files a run itself rewrites. Rerunning on the commit that carries a receipt reproduces this
    value iff the rest of the tree is the same, which is what makes a receipt from an uncommitted tree
    checkable after the fact."""
    try:
        with tempfile.TemporaryDirectory() as td:
            env = {**os.environ, "GIT_INDEX_FILE": os.path.join(td, "index")}
            subprocess.run(["git", "read-tree", "HEAD"], cwd=root, env=env, check=True, capture_output=True)
            subprocess.run(["git", "add", "-A", "--", "."], cwd=root, env=env, check=True, capture_output=True)
            subprocess.run(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", DASHBOARD, "outputs"],
                           cwd=root, env=env, check=True, capture_output=True)
            r = subprocess.run(["git", "write-tree"], cwd=root, env=env, check=True, capture_output=True, text=True)
            return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def git_info(root: str) -> dict:
    def g(*a: str) -> str:
        r = subprocess.run(["git", *a], cwd=root, capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""
    head = g("rev-parse", "HEAD")
    return {"head": head, "short": head[:7], "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(g("status", "--porcelain")), "commit_count": int(g("rev-list", "--count", "HEAD") or 0),
            "tree_hash": worktree_tree_hash(root), "tree_hash_excludes": [DASHBOARD, "outputs/"]}


HUMANAIOS_RE = re.compile(r"const\s+HUMANAIOS\s*=\s*\{(.*?)\n\};", re.S)
_S = r'"((?:[^"\\]|\\.)*)"'
BLOCK_RE = re.compile(r'^\s*\{id:' + _S + r',\s*name:' + _S + r',\s*state:"(\w+)"(?:,\s*role:' + _S + r')?', re.M)
PRED_RE = re.compile(r'^\s*\{id:"(C\d+)",\s*text:' + _S + r',\s*confidence:([\d.]+),\s*resolves:' + _S, re.M)
RULE_RE = re.compile(r'^\s*\{id:"(d\d+)",\s*(ruled:true,\s*)?(?:qid:"([^"]+)",\s*)?(?:path:"([^"]+)",\s*)?q:' + _S + r'(?:,\s*s:' + _S + r')?', re.M)
GAUGE_RE = re.compile(r'^\s*\{label:' + _S + r',\s*base:([\d.]+),\s*prev:([\d.]+),\s*target:([\d.]+)(?:,\s*scale:' + _S + r')?', re.M)


def _u(s: str | None) -> str:
    return (s or "").replace('\\"', '"')


def board_snapshot(root: str) -> dict:
    """Facts the dashboard shows next to the results: seals via the checker, and the board's own
    steps / predictions / rulings / gauges, read from the HUMANAIOS block (never from memory)."""
    snap: dict = {"path": BOARD}
    try:
        r = subprocess.run(_py(CHECKER, "--json"), cwd=root, capture_output=True, text=True, timeout=60)
        rep = json.loads(r.stdout)
        snap.update(verdict=rep.get("verdict"), counts=rep.get("counts"), read_against=rep.get("read_against"),
                    seals=[{k: s.get(k) for k in ("artifact", "sha", "path", "status", "observed")} for s in rep.get("seals", [])])
    except Exception as e:  # noqa: BLE001
        snap.update(verdict="UNREAD", error=f"{type(e).__name__}: {e}")
    try:
        src = open(os.path.join(root, BOARD), encoding="utf-8").read()
        m = HUMANAIOS_RE.search(src)
        blk = m.group(1) if m else ""
        rev = re.search(r'\brev\s*:\s*"([^"]*)"', blk)
        rd = re.search(r'read\s*:\s*\{[^}]*date\s*:\s*"([^"]*)"[^}]*against\s*:\s*"((?:[^"\\]|\\.)*)"', blk)
        snap.update(rev=rev.group(1) if rev else None, read_date=rd.group(1) if rd else None, read_against_text=_u(rd.group(2)) if rd else None,
                    blocks=[{"id": a, "name": _u(b), "state": c, "role": _u(d)} for a, b, c, d in BLOCK_RE.findall(blk)],
                    predictions=[{"id": a, "text": _u(b), "confidence": float(c), "resolves": _u(d)} for a, b, c, d in PRED_RE.findall(blk)],
                    rulings=[{"id": a, "ruled": bool(b), "qid": c or None, "path": d or None, "q": _u(e), "s": _u(f)} for a, b, c, d, e, f in RULE_RE.findall(blk)],
                    gauges=[{"label": _u(a), "base": float(b), "prev": float(c), "target": float(d), "scale": _u(e)} for a, b, c, d, e in GAUGE_RE.findall(blk)])
    except Exception as e:  # noqa: BLE001
        snap.setdefault("errors", []).append(f"board parse: {type(e).__name__}: {e}")
    return snap


def queue_snapshot(root: str) -> dict:
    try:
        r = subprocess.run(_py(".z1-control/validate.py", "--report"), cwd=root, capture_output=True, text=True, timeout=60)
        rep = json.loads(r.stdout)
        od = rep.get("overdue", [])
        return {"candidates": rep.get("candidates"), "records": rep.get("records"), "awaiting_z2": rep.get("awaiting_z2"),
                "overdue": len(od), "overdue_top": [{k: x.get(k) for k in ("q_id", "title", "submitted", "overdue_days")} for x in od[:8]],
                "decision_window_days": rep.get("decision_window_days")}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def zones_snapshot(root: str) -> dict:
    try:
        t = _md_tables(open(os.path.join(root, "ZONE_REGISTRY.md"), encoding="utf-8").read())

        def n(prefix: str) -> int:
            for k, v in t.items():
                if k.lower().startswith(prefix):
                    return max(0, len(v) - 1)
            return 0
        return {"active": n("active"), "limited": n("limited"), "readonly": n("read-only"), "planned_rows": n("planned")}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def run_all(root: str, tiers: list[str] | None = None, only: list[str] | None = None, with_snapshots: bool = True) -> dict:
    reg = [t for t in registry() if (not tiers or t["tier"] in tiers) and (not only or t["id"] in only)]
    results = [run_one(t, root) for t in reg]
    return assemble(results, root, with_snapshots)


def assemble(results: list[dict], root: str, with_snapshots: bool = True) -> dict:
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    tiers = []
    for tid, name, desc in TIERS:
        rs = [r for r in results if r["tier"] == tid]
        c: dict[str, int] = {}
        for r in rs:
            c[r["status"]] = c.get(r["status"], 0) + 1
        v = "EMPTY" if not rs else ("RED" if any(r["status"] in BAD for r in rs) else ("GREEN" if c.get("PASS") else "RED"))
        tiers.append({"id": tid, "name": name, "desc": desc, "counts": c, "verdict": v})
    bad = [r["id"] for r in results if r["status"] in BAD]
    # the run is GREEN only if every tier that ran is GREEN — a tier that only skipped is RED, not absent
    ran = [t for t in tiers if t["verdict"] != "EMPTY"]
    verdict = "GREEN" if ran and all(t["verdict"] == "GREEN" for t in ran) else "RED"
    rep = {"tool": TOOL_NAME, "version": TOOL_VERSION, "schema": SCHEMA,
           "ran_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "git": git_info(root), "python": sys.version.split()[0],
           "node": (subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip() if shutil.which("node") else None),
           "counts": counts, "verdict": verdict, "bad": bad, "tiers": tiers, "results": results}
    if with_snapshots:
        rep["board"] = board_snapshot(root)
        rep["queue"] = queue_snapshot(root)
        rep["zones"] = zones_snapshot(root)
    return rep


def print_table(rep: dict) -> None:
    g = rep["git"]
    print(f"{TOOL_NAME} v{TOOL_VERSION} · {rep['ran_at']} · {g['branch']}@{g['short']}{' (dirty)' if g['dirty'] else ''} · python {rep['python']}")
    print(f"{'status':<8} {'tier':<4} {'s':>6} id                          name")
    for r in rep["results"]:
        extra = f"  ← {r['reason']}" if r["status"] == "SKIP" else (f"  ← rc {r['rc']} (expected {r['expect']})" if r["status"] == "FAIL" else "")
        print(f"{r['status']:<8} {r['tier']:<4} {r['duration_s']:>6.1f} {r['id']:<27} {r['name']}{extra}")
        if r["status"] in BAD and r["tail"]:
            for ln in r["tail"].splitlines()[-6:]:
                print("          | " + ln[:150])
    for t in rep["tiers"]:
        print(f"{t['id']} {t['name']:<22} {t['verdict']:<6} " + " ".join(f"{k}={v}" for k, v in sorted(t["counts"].items())))
    if rep.get("board"):
        b = rep["board"]
        print(f"board: {b.get('verdict')} · seals {b.get('counts')} · read {b.get('read_date')} · rulings {len(b.get('rulings', []))} · predictions {len(b.get('predictions', []))}")
    if rep.get("queue") and "candidates" in rep["queue"]:
        q = rep["queue"]
        print(f"queue: {q['candidates']} candidates · {q['awaiting_z2']} awaiting Z2 · {q['overdue']} past the {q['decision_window_days']}d window")
    print("counts:", ", ".join(f"{k}={v}" for k, v in sorted(rep["counts"].items())))
    print("verdict:", rep["verdict"])


BEGIN, END = "/*RESULTS-BEGIN*/", "/*RESULTS-END*/"


def render_into(dashboard_path: str, rep: dict) -> None:
    src = open(dashboard_path, encoding="utf-8").read()
    i, j = src.find(BEGIN), src.find(END)
    if i < 0 or j < 0 or j < i:
        raise ValueError(f"{dashboard_path}: RESULTS markers not found")
    # HTML end tags are case-insensitive: any "</script" in a captured tail would close the block
    payload = re.sub(r"</(script)", r"<\\/\1", json.dumps(rep, ensure_ascii=False, separators=(",", ":")), flags=re.I)
    out = src[:i] + BEGIN + "\nconst RESULTS = " + payload + ";\n" + src[j:]
    open(dashboard_path, "w", encoding="utf-8").write(out)


# ---------------------------------------------------------------------------------------------------
# self-test — plant every classification and prove each fires; prove fail-closed; prove render round trip
# ---------------------------------------------------------------------------------------------------
def run_smoke_test() -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        subprocess.run(["git", "-C", td, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "seed"], check=True)
        planted = [
            dict(id="p-pass", tier="T0", area="x", name="pass", cmd=[PY, "-c", "print('ok')"], expect=0, timeout=10, requires=[], needs_cmd=[], env={}, kind="cmd", proves=["W1"], note=""),
            dict(id="p-fail", tier="T0", area="x", name="fail", cmd=[PY, "-c", "import sys;print('boom');sys.exit(1)"], expect=0, timeout=10, requires=[], needs_cmd=[], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-expect2", tier="T1", area="x", name="expected nonzero", cmd=[PY, "-c", "import sys;sys.exit(2)"], expect=2, timeout=10, requires=[], needs_cmd=[], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-timeout", tier="T1", area="x", name="timeout", cmd=[PY, "-c", "import time;time.sleep(5)"], expect=0, timeout=1, requires=[], needs_cmd=[], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-skip", tier="T2", area="x", name="skip", cmd=[PY, "-c", "print(1)"], expect=0, timeout=10, requires=["no_such_module_xyz_123"], needs_cmd=[], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-skipcmd", tier="T2", area="x", name="skip cmd", cmd=["no-such-binary-xyz"], expect=0, timeout=10, requires=[], needs_cmd=["no-such-binary-xyz"], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-error", tier="T3", area="x", name="error", cmd=["/nonexistent/binary/xyz"], expect=0, timeout=10, requires=[], needs_cmd=[], env={}, kind="cmd", proves=[], note=""),
            dict(id="p-env", tier="T3", area="x", name="env passed", cmd=[PY, "-c", "import os,sys;sys.exit(0 if os.environ.get('HARNESS_X')=='1' else 1)"], expect=0, timeout=10, requires=[], needs_cmd=[], env={"HARNESS_X": "1"}, kind="cmd", proves=[], note=""),
        ]
        res = [run_one(t, td) for t in planted]
        got = {r["id"]: r["status"] for r in res}
        want = {"p-pass": "PASS", "p-fail": "FAIL", "p-expect2": "PASS", "p-timeout": "TIMEOUT", "p-skip": "SKIP", "p-skipcmd": "SKIP", "p-error": "ERROR", "p-env": "PASS"}
        for k, v in want.items():
            print(f"  {k:<12} → {got.get(k):<8} {'OK' if got.get(k) == v else 'FAIL'}")
            ok &= got.get(k) == v
        ok &= "boom" in next(r for r in res if r["id"] == "p-fail")["tail"]
        print("  failing command's output kept in tail →", "OK" if ok else "FAIL")
        rep = assemble(res, td, with_snapshots=False)
        ok &= rep["verdict"] == "RED" and set(rep["bad"]) == {"p-fail", "p-timeout", "p-error"}
        print("  mixed run → RED, bad = fail+timeout+error:", "OK" if rep["verdict"] == "RED" else "FAIL")
        tv = {t["id"]: t["verdict"] for t in rep["tiers"]}
        ok &= tv == {"T0": "RED", "T1": "RED", "T2": "RED", "T3": "RED", "T4": "EMPTY"}
        print("  tier verdicts (T2 all-SKIP → RED, T4 → EMPTY):", tv)
        clean = assemble([r for r in res if r["status"] == "PASS"], td, with_snapshots=False)
        ok &= clean["verdict"] == "GREEN"
        print("  all-PASS run → GREEN:", "OK" if clean["verdict"] == "GREEN" else "FAIL")
        for label, subset in (("empty run", []), ("all-SKIP run", [r for r in res if r["status"] == "SKIP"]),
                              ("PASS + a SKIP-only tier", [r for r in res if r["status"] in ("PASS", "SKIP")])):
            v = assemble(subset, td, with_snapshots=False)["verdict"]
            print(f"  fail-closed · {label:<24} → {v}  {'OK' if v == 'RED' else 'FAIL'}")
            ok &= v == "RED"
        # render round trip: markers replaced, payload parses back, a </script> (any case) cannot close the tag
        dash = os.path.join(td, "dash.html")
        open(dash, "w", encoding="utf-8").write("<html><script>\n/*RESULTS-BEGIN*/\nconst RESULTS = null;\n/*RESULTS-END*/\nconsole.log(RESULTS);\n</script></html>")
        clean["results"][0]["tail"] = "x</script><b>y</SCRIPT></ScRiPt>"
        render_into(dash, clean)
        out = open(dash, encoding="utf-8").read()
        m = re.search(r"/\*RESULTS-BEGIN\*/\nconst RESULTS = (.*);\n/\*RESULTS-END\*/", out, re.S)
        back = json.loads(re.sub(r"<\\/(script)", r"</\1", m.group(1), flags=re.I)) if m else None
        ok &= (back is not None and back["verdict"] == "GREEN" and re.search(r"</script", m.group(1), re.I) is None
               and out.lower().count("<script>") == 1 and back["results"][0]["tail"] == "x</script><b>y</SCRIPT></ScRiPt>")
        print("  --render: markers replaced, payload round-trips, </script> escaped in every case:", "OK" if back else "FAIL")
        render_into(dash, clean)
        ok &= open(dash, encoding="utf-8").read().count("RESULTS-BEGIN") == 1
        print("  --render twice → still one block:", "OK" if ok else "FAIL")
        try:
            render_into(os.path.join(td, "nomark.html"), clean) if open(os.path.join(td, "nomark.html"), "w").write("<html></html>") else None
            ok = False
        except ValueError:
            print("  --render without markers → refused")
        # board snapshot parser on a planted block
        html = ('const HUMANAIOS = {\n rev:"2026-09-16",\n read:{board:"Live", date:"2026-09-16", against:"main at abc1234"},\n blocks:[\n'
                '  {id:"1", name:"a \\"quoted\\" step", state:"done", role:"stage 1",\n   why:"..."},\n  {id:"2", name:"b", state:"waiting", role:"stage 2"},\n ],\n'
                ' predictions:[\n  {id:"C1", text:"t", confidence:0.70, resolves:"2026-10-01"},\n ],\n'
                ' rulings:[\n  {id:"d1", ruled:true, q:"q1?", s:"RULED: x", opts:["a"]},\n  {id:"d2", qid:"Q-BOARD-RULING-02", path:"z1-inbox/x.md", q:"q2?", s:"open", opts:["a","b"]},\n ],\n'
                ' gauges:[\n  {label:"g", base:7.5, prev:7.5, target:100, scale:"3 of 40"},\n ],\n seals:[]\n};\n')
        os.makedirs(os.path.join(td, "ui"))
        open(os.path.join(td, BOARD), "w", encoding="utf-8").write(html)
        snap = board_snapshot(td)
        ok &= (len(snap["blocks"]) == 2 and snap["blocks"][0]["name"] == 'a "quoted" step' and snap["blocks"][1]["state"] == "waiting"
               and snap["predictions"][0]["confidence"] == 0.7 and snap["rulings"][0]["ruled"] and not snap["rulings"][1]["ruled"]
               and snap["rulings"][1]["qid"] == "Q-BOARD-RULING-02" and snap["gauges"][0]["base"] == 7.5 and snap["rev"] == "2026-09-16")
        print("  board snapshot: blocks/predictions/rulings/gauges/rev parsed from the HUMANAIOS block:", "OK" if ok else "FAIL")
        # repo index check: a named path that does not exist must FAIL — with or without an extension
        os.makedirs(os.path.join(td, ".github"))
        open(os.path.join(td, ".github", "CODEOWNERS"), "w").write("* @x\n")
        open(os.path.join(td, "REPOSITORY_STRUCTURE.md"), "w").write(
            "see `ui/intent-os-humanaios-v3_3.html`, `.github/CODEOWNERS`, `tools/nope.py` and `.github/NOFILE`; not paths: `--self-test`, `Q-ID`, `python3`, `<date>`\n")
        good, txt = check_repo_index(td)
        claims = index_path_claims(open(os.path.join(td, "REPOSITORY_STRUCTURE.md")).read())
        ok &= (not good) and "MISSING tools/nope.py" in txt and "MISSING .github/NOFILE" in txt \
            and claims == [".github/CODEOWNERS", ".github/NOFILE", "tools/nope.py", "ui/intent-os-humanaios-v3_3.html"]
        print("  repo index: absent paths (with and without extension) → FAIL; flags/ids not counted:", "OK" if not good and len(claims) == 4 else "FAIL")
        open(os.path.join(td, "REPOSITORY_STRUCTURE.md"), "w").write("see `ui/intent-os-humanaios-v3_3.html` and `.github/CODEOWNERS`\n")
        good, _ = check_repo_index(td)
        ok &= good
        print("  repo index: every named path exists → PASS:", "OK" if good else "FAIL")
        # planned repos: rows must actually be marked PLANNED
        open(os.path.join(td, "PLANNED_REPOS.md"), "w").write("## Planned\n| Repo | Status |\n|---|---|\n| x | PLANNED |\n## Status Definitions\n| Term | Meaning |\n|---|---|\n| PLANNED | claimed |\n")
        g1, _ = check_planned(td)
        open(os.path.join(td, "PLANNED_REPOS.md"), "w").write("## Status Definitions\n| Term | Meaning |\n|---|---|\n| ACTIVE | live |\n")
        g2, _ = check_planned(td)
        ok &= g1 and not g2
        print("  planned repos: a PLANNED row → PASS; definition tables alone → FAIL:", "OK" if g1 and not g2 else "FAIL")
        # zones: operations must be ACTIVE
        open(os.path.join(td, "ZONE_REGISTRY.md"), "w").write("## Active Zones\n| Zone ID | Repo Name | Purpose | Status |\n|---|---|---|---|\n| Z-000 | operations | gov | ✅ ACTIVE |\n"
                                                              "## Limited-Cap Zones\n| Zone ID | Repo Name | Status |\n|---|---|---|\n| Z-008 | docs | LIMITED |\n"
                                                              "## Read-Only Zones\n| Zone ID | Repo Name | Status |\n|---|---|---|\n| Z-011 | research | RO |\n"
                                                              "## Planned Zones\n| Zone ID | Repo Name |\n|---|---|\n| Z-012+ | see |\n")
        good, _ = check_zones(td)
        ok &= good
        open(os.path.join(td, "ZONE_REGISTRY.md"), "w").write("## Active Zones\n| Zone ID | Repo Name | Purpose | Status |\n|---|---|---|---|\n| Z-001 | humanaios | core | ✅ ACTIVE |\n")
        bad_, _ = check_zones(td)
        ok &= not bad_
        open(os.path.join(td, "ZONE_REGISTRY.md"), "w").write("## Active Zones\n| Zone ID | Repo Name | Purpose | Status |\n|---|---|---|---|\n| Z-000 | operations | gov | INACTIVE |\n"
                                                              "## Limited-Cap Zones\n| Zone ID | Repo Name | Status |\n|---|---|---|\n| Z-008 | docs | LIMITED |\n"
                                                              "## Read-Only Zones\n| Zone ID | Repo Name | Status |\n|---|---|---|\n| Z-011 | research | RO |\n"
                                                              "## Planned Zones\n| Zone ID | Repo Name |\n|---|---|\n| Z-012+ | see |\n")
        inactive, _ = check_zones(td)
        ok &= not inactive
        print("  zones: operations ACTIVE → PASS; absent → FAIL; INACTIVE → FAIL:", "OK" if good and not bad_ and not inactive else "FAIL")
    print("SELF-TEST", "PASS" if ok else "FAIL")
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", "--input", dest="root", default=ROOT,
                    help="repository root to test (--input is the tools/README.md alias)")
    ap.add_argument("--tier", nargs="*", help="run only these tiers (T0..T4)")
    ap.add_argument("--only", nargs="*", help="run only these check ids")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--render", action="store_true", help="inject the receipt into the dashboard's RESULTS block")
    ap.add_argument("--out", default=RECEIPT, help="receipt path (relative to root); '-' to skip writing")
    ap.add_argument("--self-test", "--smoke-test", dest="self_test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return 0 if run_smoke_test() else 2
    if a.list:
        for t in registry():
            print(f"{t['tier']} {t['id']:<27} {t['name']:<70} {' '.join(t['cmd']) if t['cmd'] else '<native:' + t['kind'] + '>'}")
        return 0
    rep = run_all(a.root, a.tier, a.only)
    if a.out != "-":
        p = os.path.join(a.root, a.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(rep, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        rep["receipt"] = a.out
    if a.render:
        render_into(os.path.join(a.root, DASHBOARD), rep)
    if a.json:
        print(json.dumps(rep, indent=1, ensure_ascii=False))
    else:
        print_table(rep)
        if a.out != "-":
            print("receipt:", a.out)
        if a.render:
            print("rendered:", DASHBOARD)
    return 0 if rep["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    sys.exit(main())
