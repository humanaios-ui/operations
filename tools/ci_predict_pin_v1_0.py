#!/usr/bin/env python3
"""
ci_predict_pin_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 2 of the execution-grounded calibration plan

PIN half of a three-part loop (PIN → RESOLVE → CONSOLIDATE), calibrating CI check
outcomes instead of agent self-report. Mirrors the proven CAPTURE/CONSOLIDATE split
already used by smag_pr_autocapture_v1_0.py / smag_consolidate_v1_0.py, retargeted
at tools/nf_ledger_v0_1.py's event model (a genuine stated probability `p`, refused
outside [0,1], and a real Brier score) rather than the flat SMAG row.

THE ANCHOR IS THE GIT COMMIT, NOT THIS COMMENT
-----------------------------------------------
The provable "committed before the outcome" fact is the git commit that introduces
or edits `ci_predictions/pr.json` — that commit exists, and is dated, before any
check on it can have run. This tool's job is only to make that commit's content
into a durable, GitHub-timestamped receipt (a PR comment) that the resolve and
consolidate steps can find later; the comment's own timestamp is corroborating,
not the anchor.

WHY A COMMENT, NOT A DIRECT LEDGER WRITE
-----------------------------------------
`tools/nf_ledger_v0_1.py`'s hash chain requires one consistent, ordered writer.
A `pull_request` workflow has no safe way to append to a shared file (no stable
checkout of "the ledger as of right now" that a concurrent PR wouldn't race). So
this step posts the raw declaration as a marked, machine-parseable comment and
defers hashing/appending to ci_predict_consolidate_v1_0.py, which runs at PR close
against a single checkout of main — exactly the CAPTURE/CONSOLIDATE split SMAG
already validated in this repo.

WHY THIS NEVER CHECKS OUT THE PR BRANCH
------------------------------------------
The live workflow holds `pull-requests: write` to post the pin comment. If it
also checked out and ran code from the PR branch, a same-repo PR could modify
this very script (or anything it imports) to use that write-capable token for
anything. So `run()` never touches PR-branch content as code: the declaration
file's bytes are fetched read-only through the contents API
(fetch_declaration_via_api) and only ever passed to parse_declaration, which
does nothing but validate JSON structure. The script executing is always the
copy checked out from main.

DECLARATION FILE
-----------------
`ci_predictions/pr.json`, committed by the PR author before push:
  {
    "checks": {
      "quality": {"conclusion": "success", "p": 0.9},
      "guard": {"conclusion": "success", "p": 0.85}
    },
    "note": "optional free text"
  }
`conclusion` is the predicted terminal GitHub check-run conclusion
(success/failure/neutral/cancelled/skipped/timed_out/action_required/stale).
`p` is the stated probability that the check concludes with exactly that value;
it is validated by ci_predict_consolidate_v1_0.py using nf_ledger_v0_1.check_p,
the same refusal the mesh ledger already enforces — not re-implemented here.

Usage:
  python3 tools/ci_predict_pin_v1_0.py pin --repo OWNER/REPO --pr 123 \\
      --file ci_predictions/pr.json
  python3 tools/ci_predict_pin_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smag_pr_autocapture_v1_0 import derive_substrate  # noqa: E402  (reuse, don't reinvent)

TOOL_NAME = "ci_predict_pin"
TOOL_VERSION = "1.0.0"
DEFAULT_FILE = "ci_predictions/pr.json"

# Marker wrapping the embedded JSON so resolve/consolidate can find it without
# scraping the human-readable text around it (same technique as smag_consolidate's
# ```json fence, made check-specific so a PR can't collide with a SMAG row).
PIN_MARKER = "<!-- ci-predict:pin -->"
_JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)

VALID_CONCLUSIONS = {
    "success", "failure", "neutral", "cancelled", "skipped",
    "timed_out", "action_required", "stale",
}


class DeclarationError(ValueError):
    """Raised when a predictions file is malformed. Never silently dropped."""


def parse_declaration(content: str, label: str) -> dict:
    """Validate predictions JSON already in hand. Raises, never warns-and-skips.

    `label` is only for error messages (a path, or "PR #123 @ ci_predictions/pr.json").
    This is the shared validation core for both the local-file and the
    API-fetched entry points below.
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise DeclarationError(f"{label}: invalid JSON — {exc}") from exc
    if not isinstance(data, dict):
        raise DeclarationError(f"{label}: top level must be a JSON object")
    checks = data.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise DeclarationError(f"{label}: 'checks' must be a non-empty object")
    for name, spec in checks.items():
        if not isinstance(spec, dict):
            raise DeclarationError(f"{label}: check {name!r} is not an object")
        conclusion = spec.get("conclusion")
        if conclusion not in VALID_CONCLUSIONS:
            raise DeclarationError(
                f"{label}: check {name!r} has invalid conclusion {conclusion!r}"
            )
        p = spec.get("p")
        if not isinstance(p, (int, float)) or not (0.0 <= p <= 1.0):
            raise DeclarationError(f"{label}: check {name!r} has p={p!r}, must be in [0,1]")
    return data


def load_declaration(path: Path) -> dict:
    """Read and validate a predictions file from a local checkout.

    For hand-testing against a real checkout, or from within a repository the
    caller already trusts. The live pin workflow does not use this: see
    fetch_declaration_via_api, which never checks out PR-branch content.
    """
    if not path.exists():
        raise DeclarationError(f"no declaration at {path}")
    return parse_declaration(path.read_text(encoding="utf-8"), str(path))


def build_payload(pr_number: str, head_sha: str, predictor: str, declaration: dict,
                  committed_at: str = "") -> dict:
    """Pure: assemble the payload that goes into the pin comment. No I/O.

    `committed_at` should be the git commit timestamp that last touched the
    declaration file (ISO 8601), supplied by the caller via
    `git log -1 --format=%cI -- <file>` — that commit, not this comment, is the
    provable "before the outcome" anchor. Left empty rather than guessed if the
    caller cannot determine it.
    """
    return {
        "schema": "ci_predict_pin_v1",
        "pr": str(pr_number),
        "head_sha": head_sha,
        "predictor": predictor,
        "committed_at": committed_at,
        "checks": declaration["checks"],
        "note": declaration.get("note", ""),
    }


def render_pin_comment(payload: dict) -> str:
    """Render the human-readable + machine-parseable pin comment."""
    lines = [f"- `{name}` → predicted **{spec['conclusion']}** (p={spec['p']})"
             for name, spec in sorted(payload["checks"].items())]
    anchor = payload.get("committed_at") or "unknown — git log lookup failed"
    return (
        f"{PIN_MARKER}\n"
        f"## CI prediction — PR #{payload['pr']} @ `{payload['head_sha'][:12]}`\n\n"
        f"Committed before any of these checks resolved, at `{anchor}`. Predictor: "
        f"`{payload['predictor']}`.\n\n" + "\n".join(lines) +
        (f"\n\n_{payload['note']}_" if payload.get("note") else "") +
        f"\n\n```json\n{json.dumps(payload, sort_keys=True)}\n```"
    )


def gh_json(path: str):
    """Fetch JSON from the GitHub API via gh. Returns None on failure."""
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def git_commit_date(path: Path) -> str:
    """The ISO 8601 commit date of the last commit touching `path`, from a
    local checkout.

    For hand-testing against a real checkout. The live pin workflow never
    checks out PR-branch content — see commit_date_via_api — so this is not
    on that path. Empty string, never a guess, on any failure (detached
    checkout, shallow clone missing history, file untracked yet).
    """
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def fetch_declaration_via_api(repo: str, ref: str, path: str = DEFAULT_FILE):
    """The declaration file's content at `ref`, read via the contents API.

    This is how the live workflow gets the PR author's declaration WITHOUT
    checking out the PR branch: `actions/checkout` in the pin workflow stays
    on the trusted base ref (this script never runs untrusted code with a
    write-capable token), and only this one file's bytes, fetched and
    strictly validated by parse_declaration, cross into the job at all.
    Returns None if the file does not exist at that ref (not an error: a PR
    with no declaration is simply not predicting anything).
    """
    proc = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}", "-f", f"ref={ref}"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout)
        return base64.b64decode(payload["content"]).decode("utf-8")
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def commit_date_via_api(repo: str, sha: str) -> str:
    """The head commit's own commit date via the API, ISO 8601.

    Less precise than git_commit_date's "the commit that last touched this
    exact file" — this is the head commit's date, which for a PR whose last
    push included the declaration is the same thing, and is the honest
    tradeoff for never checking out the PR branch. Empty string on failure.
    """
    proc = subprocess.run(
        ["gh", "api", f"repos/{repo}/commits/{sha}"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        return ""
    try:
        commit = json.loads(proc.stdout)
        return ((commit.get("commit") or {}).get("committer") or {}).get("date", "")
    except json.JSONDecodeError:
        return ""


def post_comment(repo: str, pr_number: str, body: str) -> int:
    """Post the pin comment. One comment per push; not deduped here — the
    consolidate step dedups by head_sha, so a rerun on the same commit is
    harmless noise, not a correctness risk."""
    proc = subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--repo", repo, "--body", body],
        capture_output=True, text=True,
    )
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def run(repo: str, pr_number: str, declaration_file: str = DEFAULT_FILE) -> int:
    """Fetch the declaration and PR metadata entirely via the API — no
    checkout of PR-branch content, so this never executes anything the PR
    author wrote. `declaration_file` is a repo-relative path resolved at the
    PR's head ref through the contents API, not a local filesystem path.
    """
    pr = gh_json(f"repos/{repo}/pulls/{pr_number}")
    if pr is None:
        print(f"::warning::could not fetch PR {pr_number}; skipping pin", file=sys.stderr)
        return 0  # a missing pin is a VOID later, never a workflow failure
    head_sha = (pr.get("head") or {}).get("sha", "")

    content = fetch_declaration_via_api(repo, head_sha, declaration_file)
    if content is None:
        print(f"no {declaration_file} at {head_sha[:12]}; nothing to pin")
        return 0
    declaration = parse_declaration(content, f"PR #{pr_number} @ {declaration_file}")

    predictor = derive_substrate((pr.get("user") or {}).get("login", ""))
    committed_at = commit_date_via_api(repo, head_sha)
    payload = build_payload(pr_number, head_sha, predictor, declaration, committed_at)
    comment = render_pin_comment(payload)
    print(comment)
    return post_comment(repo, pr_number, comment)


def run_smoke_test() -> bool:
    """Pure-logic smoke test. No network, matches house convention."""
    ok = True
    declaration = {"checks": {"quality": {"conclusion": "success", "p": 0.9},
                              "guard": {"conclusion": "success", "p": 0.7}},
                   "note": "example"}
    payload = build_payload("42", "abc123def456", "Claude Code", declaration)
    ok = ok and payload["pr"] == "42" and payload["predictor"] == "Claude Code"
    ok = ok and payload["committed_at"] == ""  # no anchor supplied: empty, not guessed
    comment = render_pin_comment(payload)
    ok = ok and PIN_MARKER in comment and "```json" in comment
    ok = ok and "unknown — git log lookup failed" in comment

    anchored = build_payload("42", "abc123def456", "Claude Code", declaration,
                             committed_at="2026-09-12T10:00:00Z")
    ok = ok and "2026-09-12T10:00:00Z" in render_pin_comment(anchored)
    match = _JSON_BLOCK.search(comment)
    ok = ok and match is not None
    round_tripped = json.loads(match.group(1)) if match else {}
    ok = ok and round_tripped == payload

    # A bad probability is refused at declaration time, not silently accepted.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump({"checks": {"x": {"conclusion": "success", "p": 1.5}}}, handle)
        bad_path = Path(handle.name)
    try:
        load_declaration(bad_path)
        ok = False  # should have raised
    except DeclarationError:
        pass
    finally:
        bad_path.unlink(missing_ok=True)

    # An unknown conclusion string is refused the same way.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump({"checks": {"x": {"conclusion": "sorta", "p": 0.5}}}, handle)
        bad_path2 = Path(handle.name)
    try:
        load_declaration(bad_path2)
        ok = False
    except DeclarationError:
        pass
    finally:
        bad_path2.unlink(missing_ok=True)

    # A non-object top level (array/scalar) is refused, not an AttributeError.
    try:
        parse_declaration("[1, 2, 3]", "test")
        ok = False
    except DeclarationError:
        pass
    try:
        parse_declaration("42", "test")
        ok = False
    except DeclarationError:
        pass

    # fetch_declaration_via_api / commit_date_via_api never touch a local
    # checkout; verified here against a faked subprocess, no network.
    class FakeContentsResponse:
        returncode = 0
        stdout = json.dumps({"content": base64.b64encode(
            b'{"checks": {"quality": {"conclusion": "success", "p": 0.9}}}'
        ).decode()})

    class FakeCommitResponse:
        returncode = 0
        stdout = json.dumps({"commit": {"committer": {"date": "2026-09-12T10:00:00Z"}}})

    class FakeFailure:
        returncode = 1
        stdout = ""

    orig_run = subprocess.run
    subprocess.run = lambda *a, **k: FakeContentsResponse()
    try:
        content = fetch_declaration_via_api("owner/repo", "deadbeef")
        ok = ok and content is not None
        ok = ok and parse_declaration(content, "x")["checks"]["quality"]["p"] == 0.9
    finally:
        subprocess.run = orig_run

    subprocess.run = lambda *a, **k: FakeCommitResponse()
    try:
        ok = ok and commit_date_via_api("owner/repo", "deadbeef") == "2026-09-12T10:00:00Z"
    finally:
        subprocess.run = orig_run

    subprocess.run = lambda *a, **k: FakeFailure()
    try:
        ok = ok and fetch_declaration_via_api("owner/repo", "deadbeef") is None
        ok = ok and commit_date_via_api("owner/repo", "deadbeef") == ""
    finally:
        subprocess.run = orig_run

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    pin = sub.add_parser("pin")
    pin.add_argument("--repo", required=True)
    pin.add_argument("--pr", required=True)
    pin.add_argument("--file", default=DEFAULT_FILE)

    args = parser.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command != "pin":
        parser.print_help()
        return 2
    try:
        return run(args.repo, args.pr, args.file)
    except DeclarationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
